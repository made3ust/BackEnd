from flask import (render_template, redirect, url_for, request, flash,
                   send_from_directory, abort, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from app import db
from app.models import User, Course
from app.forms import CourseForm
from flask import Blueprint

courses_bp = Blueprint('courses', __name__, template_folder='templates', static_folder='../static')

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
    if not filename: return
    try:
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], type)
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"File deleted: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting file {filename}: {e}")

@courses_bp.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if not current_user.is_admin:
        flash('Only administrators can create courses.', 'danger')
        abort(403)

    form = CourseForm()
    if form.validate_on_submit():
        image_filename = save_file(form.image.data, type='images')
        material_filename = save_file(form.material.data, type='materials')

        course = Course(
            title=form.title.data, description=form.description.data,
            instructor=form.instructor.data, image_filename=image_filename,
            material_filename=material_filename, creator=current_user
        )
        try:
            db.session.add(course)
            db.session.commit()
            current_app.logger.info(f'Course "{form.title.data}" created by {current_user.username}.')
            flash('Course created successfully!', 'success')
            return redirect(url_for('main.courses_view'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Course creation error: {e}", exc_info=True)
            flash('An error occurred while creating the course.', 'danger')

    return render_template('create_course.html', form=form, title='Create Course', legend='New Course')

@courses_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    course = db.get_or_404(Course, course_id)
    return render_template('course_details.html', course=course, title=course.title)

@courses_bp.route('/course/<int:course_id>/update', methods=['GET', 'POST'])
@login_required
def update_course(course_id):
    course = db.get_or_404(Course, course_id)
    if not current_user.is_admin: abort(403)

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
            return redirect(url_for('courses.course_detail', course_id=course.id))
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

    return render_template('create_course.html', form=form, title='Update Course', legend=f'Update: {course.title}', image_url=image_url, course=course)

@courses_bp.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = db.get_or_404(Course, course_id)
    if not current_user.is_admin: abort(403)

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

    return redirect(url_for('main.courses_view'))

@courses_bp.route('/uploads/<type>/<path:filename>')
def uploaded_file(type, filename):
    if type not in ('images', 'materials'): abort(404)
    filename = secure_filename(filename)
    if not filename or '..' in filename or filename.startswith(('/', '\\')): abort(400)

    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], type)

    if not os.path.isfile(os.path.join(directory, filename)): abort(404)
    try:
        return send_from_directory(directory, filename)
    except Exception as e:
        current_app.logger.error(f"Error sending file {filename} from {directory}: {e}")
        abort(500)