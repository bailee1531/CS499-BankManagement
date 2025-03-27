from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError

# -----------------------------------------------------------------------------
# LoginForm: A simple login form for user authentication.
# -----------------------------------------------------------------------------
class LoginForm(FlaskForm):
    """
    A Flask-WTF form for user login.
    """
    # Text input for the username. Must be provided by the user.
    username = StringField('Username', validators=[DataRequired()])
    
    # Password input for the user's password. Also required.
    password = PasswordField('Password', validators=[DataRequired()])
    
    # Submit button to send the login data.
    submit = SubmitField('Login')


# -----------------------------------------------------------------------------
# RegistrationStep1Form: Collects basic personal details in the first step 
# of a multi-step registration process.
# -----------------------------------------------------------------------------
class RegistrationStep1Form(FlaskForm):
    # Input field for the user's first name, required and limited to 50 characters.
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    
    # Input field for the user's last name, required and limited to 50 characters.
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    
    # Input field for the user's address, required and limited to 100 characters.
    address = StringField('Address', validators=[DataRequired(), Length(max=100)])
    
    # Input field for the user's phone number.
    # Must match the pattern XXX-XXX-XXXX (e.g., 123-456-7890).
    phone_number = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\d{3}-\d{3}-\d{4}$', message="Phone number must be in format XXX-XXX-XXXX")
        ]
    )
    
    # Input field for the user's Tax ID, represented here as a Social Security Number.
    # Must match the pattern XXX-XX-XXXX (e.g., 123-45-6789).
    tax_id = StringField(
        'Social Security Number (Tax ID)',
        validators=[
            DataRequired(),
            Regexp(r'^\d{3}-\d{2}-\d{4}$', message="SSN must be in format XXX-XX-XXXX")
        ]
    )
    
    # Input field for the user's birthday.
    # Uses a date format 'YYYY-MM-DD' and includes a placeholder to guide the user.
    birthday = DateField(
        'Birthday',
        format='%Y-%m-%d',
        validators=[DataRequired()],
        render_kw={"placeholder": "YYYY-MM-DD"}
    )
    
    # Submit button to proceed to the next registration step.
    submit = SubmitField('Next')


# -----------------------------------------------------------------------------
# RegistrationStep2Form: Collects account credentials and security questions.
# -----------------------------------------------------------------------------
class RegistrationStep2Form(FlaskForm):
    # Input field for the username with required data and a length between 4 and 25 characters.
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    
    # Password field requiring a minimum of 8 characters.
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    
    # Field to confirm the password. Uses EqualTo to ensure it matches the 'password' field.
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message="Passwords must match")
    ])

    # Input field for the email address. Must be a valid email format.
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # Field to confirm the email address. Also checks that it matches the first email field.
    confirm_email = StringField('Confirm Email', validators=[
        DataRequired(), Email(), EqualTo('email', message="Emails must match")
    ])

    # A predefined list of tuples containing security question identifiers and their text.
    security_question_choices = [
        ("mother_maiden", "What is your mother's maiden name?"),
        ("first_pet", "What was the name of your first pet?"),
        ("first_car", "What was your first car?"),
        ("childhood_friend", "What is the first name of your childhood best friend?"),
        ("favorite_teacher", "Who was your favorite teacher in school?"),
        ("first_job", "What was your first job?"),
        ("city_birth", "In which city were you born?"),
        ("favorite_food", "What is your favorite food?")
    ]

    # Dropdown field for selecting the first security question.
    security_question_1 = SelectField(
        'Security Question 1', 
        choices=security_question_choices, 
        validators=[DataRequired()]
    )
    
    # Input field for answering the first security question.
    security_answer_1 = StringField(
        'Answer to Security Question 1', 
        validators=[DataRequired(), Length(min=2, max=50)]
    )

    # Dropdown field for selecting the second security question.
    security_question_2 = SelectField(
        'Security Question 2', 
        choices=security_question_choices, 
        validators=[DataRequired()]
    )
    
    # Input field for answering the second security question.
    security_answer_2 = StringField(
        'Answer to Security Question 2', 
        validators=[DataRequired(), Length(min=2, max=50)]
    )

    # Submit button to complete the registration process.
    submit = SubmitField('Register')

    # Custom validation method for the second security question.
    # Ensures that the two chosen security questions are not the same.
    def validate_security_question_2(self, field):
        # If the second question is the same as the first, raise a validation error.
        if field.data == self.security_question_1.data:
            raise ValidationError("Security questions must be different.")

# -----------------------------------------------------------------------------
# SettingsForm: Allows user to manage personal information.
# -----------------------------------------------------------------------------
class SettingsForm(FlaskForm):
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\d{3}-\d{3}-\d{4}$')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Update Settings')
