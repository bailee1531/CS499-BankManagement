from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Regexp, Optional, Length, Email

# -----------------------------------------------------------------------------
# TellerSettingsForm: Tellers can modify their personal information.
# -----------------------------------------------------------------------------
class TellerSettingsForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Regexp(r'^\d{3}-\d{3}-\d{4}$')])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=25)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])

# -----------------------------------------------------------------------------
# AdminSettingsForm: Modify admin password only.
# -----------------------------------------------------------------------------
class AdminSettingsForm(FlaskForm):
    email = StringField('Email')
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])