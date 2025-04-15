"""
forms.py

This module defines Flask-WTF forms used for user authentication,
registration, deposit submissions, and mortgage applications.
Each form includes detailed documentation and type annotations
where applicable.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
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

# -----------------------------------------------------------------------------
# ResetPasswordForm: A form for user's to reset their password.
# -----------------------------------------------------------------------------
class ResetPasswordForm(FlaskForm):
    """
    A Flask-WTF form for password reset via security questions.

    Fields:
        user_id (StringField): Field for the user’s ID. Required.
        question1 (StringField): Answer to security question 1. Required.
        question2 (StringField): Answer to security question 2. Required.
        new_password (PasswordField): New password to set. Required.
        submit (SubmitField): Form submission button.
    """
    user_id = StringField("User ID", validators=[DataRequired()])
    question1 = StringField("Answer to Security Question 1", validators=[DataRequired()])
    question2 = StringField("Answer to Security Question 2", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    submit = SubmitField("Reset Password")
