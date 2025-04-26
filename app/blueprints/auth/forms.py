# Spring 2025 Authors: Sierra Yerges, Braden Doty, Bailee Segars
"""
forms.py

This module defines Flask-WTF forms used for user authentication,
registration, deposit submissions, and mortgage applications.
Each form includes detailed documentation and type annotations
where applicable.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length


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
    user_id = StringField('User ID', validators=[DataRequired()])

    security_question_choices = [
        ("", "Select a security question"),  # Default placeholder
        ("mother_child", "Who is your Mother's favorite child?"),
        ("chicken_name", "What would you name a chicken if you owned one?"),
        ("first_gamertag", "What was your first gamertag?"),
        ("childhood_dream", "What was your dream career as a child?"),
        ("least_favorite_relative", "Who is your least favorite relative?"),
        ("first_anime", "What was your first anime?"),
        ("longest_word", "What is the longest word you can spell without spell check?"),
        ("favorite_food", "What is your favorite food?"),
        ("never_visit", "Where would you never visit?"),
        ("musical_experts", "What musical do you know well enough to sing every song?"),
        ("best_spiderman", "Who was the best Spider-Man?"),
        ("worst_film", "What was the worst film ever created?")
    ]

    question1 = SelectField('Security Question 1', choices=security_question_choices, validators=[DataRequired()])
    answer1 = StringField('Answer to Security Question 1', validators=[DataRequired(), Length(min=2, max=50)])
    question2 = SelectField('Security Question 2', choices=security_question_choices, validators=[DataRequired()])
    answer2 = StringField('Answer to Security Question 2', validators=[DataRequired(), Length(min=2, max=50)])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Reset Password')
