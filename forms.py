# forms.py - Forms with validation (security: Prevents bad inputs).
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Email(message="Invalid email.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="Too short.")])
    submit = SubmitField('Login')
