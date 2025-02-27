"""
Module: forms.py

This module defines WTForms classes used for user authentication.
The LoginForm class handles the input and validation of login credentials.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    """
    A Flask-WTF form for user login.

    Fields:
        username (StringField): The username input field. It is required.
        password (PasswordField): The password input field. It is required.
        submit (SubmitField): The submit button to send the form data.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
