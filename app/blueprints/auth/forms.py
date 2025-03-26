from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, SelectField, DateField,
    PasswordField, HiddenField, DecimalField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    Regexp, ValidationError, NumberRange
)

# -----------------------------------------------------------------------------
# LoginForm: A simple login form for user authentication.
# -----------------------------------------------------------------------------
class LoginForm(FlaskForm):
    """
    A Flask-WTF form for user login.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


# -----------------------------------------------------------------------------
# RegistrationStep1Form: Collects basic personal details in step 1 of registration.
# -----------------------------------------------------------------------------
class RegistrationStep1Form(FlaskForm):
    """
    Step 1 of registration: gathers basic personal information.
    """
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    address = StringField('Address', validators=[DataRequired(), Length(max=100)])
    
    phone_number = StringField(
        'Phone Number',
        validators=[
            DataRequired(),
            Regexp(r'^\d{3}-\d{3}-\d{4}$', message="Phone number must be in format XXX-XXX-XXXX")
        ]
    )

    tax_id = StringField(
        'Social Security Number (Tax ID)',
        validators=[
            DataRequired(),
            Regexp(r'^\d{3}-\d{2}-\d{4}$', message="SSN must be in format XXX-XX-XXXX")
        ]
    )

    birthday = DateField(
        'Birthday',
        format='%Y-%m-%d',
        validators=[DataRequired()],
        render_kw={"placeholder": "YYYY-MM-DD"}
    )

    submit = SubmitField('Next')


# -----------------------------------------------------------------------------
# RegistrationStep2Form: Collects account credentials and security questions.
# -----------------------------------------------------------------------------
class RegistrationStep2Form(FlaskForm):
    """
    Step 2 of registration: account credentials and security questions.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message="Passwords must match")]
    )

    email = StringField('Email', validators=[DataRequired(), Email()])
    confirm_email = StringField(
        'Confirm Email',
        validators=[DataRequired(), Email(), EqualTo('email', message="Emails must match")]
    )

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

    security_question_1 = SelectField(
        'Security Question 1',
        choices=security_question_choices,
        validators=[DataRequired()]
    )
    security_answer_1 = StringField(
        'Answer to Security Question 1',
        validators=[DataRequired(), Length(min=2, max=50)]
    )

    security_question_2 = SelectField(
        'Security Question 2',
        choices=security_question_choices,
        validators=[DataRequired()]
    )
    security_answer_2 = StringField(
        'Answer to Security Question 2',
        validators=[DataRequired(), Length(min=2, max=50)]
    )

    submit = SubmitField('Register')

    def validate_security_question_2(self, field):
        """
        Ensures that the two selected security questions are different.
        """
        if field.data == self.security_question_1.data:
            raise ValidationError("Security questions must be different.")


# -----------------------------------------------------------------------------
# RegistrationStep3Form: Final step in registration.
# -----------------------------------------------------------------------------
class RegistrationStep3Form(FlaskForm):
    """
    Step 3 of registration: handles the account type and final submission.
    """
    account_type = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Register')


# -----------------------------------------------------------------------------
# DepositForm: Form for submitting a deposit.
# -----------------------------------------------------------------------------
class DepositForm(FlaskForm):
    """
    A simple form to enter a deposit amount.
    """
    deposit_amount = DecimalField(
        'Deposit Amount ($)',
        validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive.")]
    )
    submit = SubmitField('Submit Deposit')

