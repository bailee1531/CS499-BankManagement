"""
forms.py

This module defines Flask-WTF forms used for user authentication,
registration, deposit submissions, and mortgage applications.
Each form includes detailed documentation and type annotations
where applicable.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Optional, Length, Regexp, Email

# -----------------------------------------------------------------------------
# SettingsForm: Customer can modify personal information.
# -----------------------------------------------------------------------------
class SettingsForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Regexp(r'^\d{3}-\d{3}-\d{4}$')])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=25)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    submit = SubmitField('Update Settings')
