from flask import (render_template, redirect, url_for, request, flash,
                   send_from_directory, abort, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.security import check_password_hash
import os

from app import app, db
from app.forms import RegistrationForm, LoginForm, CourseForm, SearchForm
from app.models import User, Course


def save_file(file, type='images'):
    if file and file.filename:
        filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{file.filename}")
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], type)
        file_path = os.path.join(folder_path, filename)
        try:
            file.save(file_path)
            current_app.logger.info(f"File saved: {file_path}")
            return filename
        except Exception as e:
            current_app.logger.error(f"File save error for {file.filename}: {e}")
            flash(f'An unexpected error occurred while uploading the file.', 'danger')
            return None
    return None

def delete_file_if_exists(filename, type='images'):
    if not filename:
        return
    try:
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], type)
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"File deleted: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting file {filename}: {e}")


@app.context_processor
def base():
    form = SearchForm()
    return dict(search_form=form)


@app.route('/')
def courses_view():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('query', '').strip()

    query_filter = Course.query

    if search_query:
        query_filter = query_filter.filter(
            or_(
                Course.title.ilike(f'%{search_query}%'),
                Course.instructor.ilike(f'%{search_query}%')
            )
        )
        title = f'Search Results: "{search_query}"'
    else:
        title = 'Available Courses'

    courses = query_filter.order_by(Course.date_posted.desc()).paginate(
        page=page, per_page=current_app.config.get('COURSES_PER_PAGE', 6)
    )

    return render_template('index.html', courses=courses, title=title, query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('courses_view'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            current_app.logger.info(f'User {form.username.data} registered successfully.')
            flash(f'Account for {form.username.data} created! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f'Registration failed (IntegrityError) for username: {form.username.data}')
            flash('This username is already taken. Please choose a different one.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}", exc_info=True)
            flash('An unexpected error occurred during registration.', 'danger')

    return render_template('register.html', form=form, title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('courses_view'))
    form = LoginForm()
    if form.validate_on_submit():
        submitted_username = form.username.data
        submitted_password = form.password.data
        user = User.query.filter_by(username=submitted_username).first()

        if user and user.check_password(submitted_password):
            login_user(user, remember=form.remember.data)
            current_app.logger.info(f'User {user.username} logged in successfully.')
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('courses_view'))
        else:
            current_app.logger.warning(f'Failed login attempt for username: {submitted_username}')
            flash('Invalid username or password.', 'danger')
    elif request.method == 'POST':
         flash('Please fill in all fields.', 'warning')

    return render_template('login.html', form=form, title='Login')

@app.route('/logout')
@login_required
def logout():
    current_app.logger.info(f'User {current_user.username} logged out.')
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('courses_view'))

@app.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if not current_user.is_admin:
        flash('Only an administrator can create courses.', 'danger')
        abort(403)

    form = CourseForm()
    if form.validate_on_submit():
        image_filename = save_file(form.image.data, type='images')
        material_filename = save_file(form.material.data, type='materials')

        course = Course(
            title=form.title.data,
            description=form.description.data,
            instructor=form.instructor.data,
            image_filename=image_filename,
            material_filename=material_filename,
            creator=current_user
        )
        try:
            db.session.add(course)
            db.session.commit()
            current_app.logger.info(f'Course "{form.title.data}" created by {current_user.username}.')
            flash('Course created successfully!', 'success')
            return redirect(url_for('courses_view'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Course creation error: {e}", exc_info=True)
            flash('An error occurred while creating the course.', 'danger')

    return render_template('create_course.html', form=form, title='Create Course', legend='New Course')

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = db.get_or_404(Course, course_id)
    return render_template('course_details.html', course=course, title=course.title)

@app.route('/course/<int:course_id>/update', methods=['GET', 'POST'])
@login_required
def update_course(course_id):
    course = db.get_or_404(Course, course_id)
    if not current_user.is_admin:
        abort(403)

    form = CourseForm()
    if form.validate_on_submit():
        if form.image.data:
            delete_file_if_exists(course.image_filename, type='images')
            course.image_filename = save_file(form.image.data, type='images')
        if form.material.data:
            delete_file_if_exists(course.material_filename, type='materials')
            course.material_filename = save_file(form.material.data, type='materials')

        course.title = form.title.data
        course.description = form.description.data
        course.instructor = form.instructor.data
        try:
            db.session.commit()
            current_app.logger.info(f'Course ID {course_id} updated by {current_user.username}.')
            flash('Course updated successfully!', 'success')
            return redirect(url_for('course_detail', course_id=course.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Course update error for ID {course_id}: {e}", exc_info=True)
            flash('An error occurred while updating the course.', 'danger')

    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.instructor.data = course.instructor

    image_url = None
    if course.image_filename:
        try:
             image_url = url_for('static', filename=os.path.join('uploads', 'images', course.image_filename))
        except Exception as e:
            current_app.logger.warning(f"Could not generate URL for image {course.image_filename}: {e}")

    return render_template('create_course.html', form=form, title='Update Course', legend=f'Update: {course.title}', image_url=image_url)

@app.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = db.get_or_404(Course, course_id)
    if not current_user.is_admin:
        abort(403)

    course_title = course.title
    image_to_delete = course.image_filename
    material_to_delete = course.material_filename

    try:
        db.session.delete(course)
        db.session.commit()
        delete_file_if_exists(image_to_delete, type='images')
        delete_file_if_exists(material_to_delete, type='materials')
        current_app.logger.info(f'Course "{course_title}" (ID: {course_id}) deleted by {current_user.username}.')
        flash(f'Course "{course_title}" successfully deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Course delete error for ID {course_id}: {e}", exc_info=True)
        flash('An error occurred while deleting the course.', 'danger')

    return redirect(url_for('courses_view'))

@app.route('/uploads/<type>/<path:filename>')
def uploaded_file(type, filename):
    if type not in ('images', 'materials'):
        abort(404)

    filename = secure_filename(filename)
    if not filename or '..' in filename or filename.startswith(('/', '\\')):
        abort(400)

    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], type)

    if not os.path.isfile(os.path.join(directory, filename)):
        abort(404)

    try:
        return send_from_directory(directory, filename)
    except Exception as e:
        current_app.logger.error(f"Error sending file {filename} from {directory}: {e}")
        abort(500)