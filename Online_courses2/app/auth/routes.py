from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.courses_view'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
            current_app.logger.info(f'User {form.username.data} registered successfully.')
            flash(f'Account for {form.username.data} created! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            current_app.logger.warning(f'Registration failed (IntegrityError) for username: {form.username.data}')
            flash('This username is already taken. Please choose a different one.', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {e}", exc_info=True)
            flash('An unexpected error occurred during registration.', 'danger')

    return render_template('register.html', form=form, title='Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.courses_view'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            current_app.logger.info(f'User {user.username} logged in successfully.')
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('main.courses_view'))
        else:
            current_app.logger.warning(f'Failed login attempt for username: {form.username.data}')
            flash('Invalid username or password.', 'danger')

    return render_template('login.html', form=form, title='Login')

@auth_bp.route('/logout')
@login_required
def logout():
    current_app.logger.info(f'User {current_user.username} logged out.')
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('main.courses_view'))