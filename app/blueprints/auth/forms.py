"""
forms.py

This module defines Flask-WTF forms used for user authentication,
registration, deposit submissions, and mortgage applications.
Each form includes detailed documentation and type annotations
where applicable.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


# -----------------------------------------------------------------------------
# LoginForm: A simple login form for user authentication.
# -----------------------------------------------------------------------------
class LoginForm(FlaskForm):
    """
    A Flask-WTF form for user login.

    Fields:
        username (StringField): Field for the user's username. Required.
        password (PasswordField): Field for the user's password. Required.
        submit (SubmitField): Form submission button.
    """
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
