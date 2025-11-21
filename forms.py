# forms.py - Forms with validation (security: Prevents bad inputs).
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TelField
from wtforms.validators import DataRequired, Length, Email, Regexp

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Email(message="Invalid email.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, message="Too short.")])
    submit = SubmitField('Login')

class UserDetailsForm(FlaskForm):
    org_company = StringField('Organization/Company', validators=[DataRequired(), Length(max=255)])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    phone = TelField('Phone', validators=[DataRequired(), Regexp(r'^\+?[\d\s-]{7,20}$', message="Invalid phone format.")])
    tax_reg = StringField('Tax/Registration Number', validators=[DataRequired(), Regexp(r'^[\w-]{5,20}$', message="Invalid tax/reg format.")])
    submit = SubmitField('Save Details')
