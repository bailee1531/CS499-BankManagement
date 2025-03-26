from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, SelectField, DateField,
    PasswordField, HiddenField, DecimalField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    Regexp, ValidationError, NumberRange
)

