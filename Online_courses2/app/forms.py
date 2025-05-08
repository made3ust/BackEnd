from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileSize
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Checks if the username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    instructor = StringField('Instructor', validators=[DataRequired(), Length(max=100)])
    image = FileField('Image (jpg, png, gif, up to 16MB)', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Only images are allowed!'),
        FileSize(max_size=16 * 1024 * 1024, message='File is too large (max 16MB)!')
    ])
    material = FileField('Materials (pdf, docx, txt, zip, up to 16MB)', validators=[
        FileAllowed(['pdf', 'docx', 'txt', 'zip'], 'Only documents or zip archives are allowed!'),
        FileSize(max_size=16 * 1024 * 1024, message='File is too large (max 16MB)!')
    ])
    submit = SubmitField('Save Course')

class SearchForm(FlaskForm):
    query = StringField('Search Courses')
    submit = SubmitField('Search')