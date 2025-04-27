# Spring 2025 Authors: Bailee Segars, Sierra Yerges
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Optional, Length

# --------------------------
# Modify admin password only
# --------------------------
class AdminSettingsForm(FlaskForm):
    email = StringField('Email')
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])