"""
forms.py

This module defines Flask-WTF forms used for registration and deposit submissions.
"""

# Importing necessary libraries from Flask-WTF and WTForms
from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, SelectField, DateField,
    PasswordField, HiddenField, DecimalField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length,
    Regexp, ValidationError, NumberRange
)
from wtforms.fields.core import Field  # for type annotations

# -----------------------------------------------------------------------------
# TellerUsernameForm: Collects username input to verify before sign up.
# -----------------------------------------------------------------------------
class TellerUsernameForm(FlaskForm):
    """
    Form for teller to input their pre-created username.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    submit = SubmitField('Continue')

# -----------------------------------------------------------------------------
# RegistrationStep1Form: Collects basic personal details in step 1 of registration.
# -----------------------------------------------------------------------------
class RegistrationStep1Form(FlaskForm):
    """
    Step 1 of registration: gathers basic personal information.

    Attributes:
        first_name (StringField): User's first name.
        last_name (StringField): User's last name.
        address (StringField): User's address.
        phone_number (StringField): User's phone number in format XXX-XXX-XXXX.
        tax_id (StringField): User's SSN in format XXX-XX-XXXX.
        birthday (DateField): User's birthday in YYYY-MM-DD format.
        submit (SubmitField): Form submission button.
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

    Attributes:
        username (StringField): Desired username.
        password (PasswordField): User's password.
        confirm_password (PasswordField): Confirmation of the password.
        email (StringField): User's email address.
        confirm_email (StringField): Confirmation of the email address.
        security_question_1 (SelectField): The first security question.
        security_answer_1 (StringField): Answer for the first security question.
        security_question_2 (SelectField): The second security question.
        security_answer_2 (StringField): Answer for the second security question.
        submit (SubmitField): Form submission button.
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

    # List of predefined security questions
    security_question_choices = [
        ("mother_child", "Who is your Mother's favorite child?"),
        ("chicken_name", "What would you name a chicken if you owned one?"),
        ("first_gamertag", "What was your first gamertag?"),
        ("childhood_dream", "What was your dream career as a child?"),
        ("least_favorite_relative", "Who is your least favorite relative?"),
        ("first_anime", "What was your first anime?"),
        ("longest_word", "What is the longest word you can spell without spell check?"),
        ("favorite_food", "What is your favorite food?"),
        ("never_visit", "Where would you never visit even if you were on your last breath?"),
        ("remove_kindly", "If you could kindly remove someone from the history books, who would it be?"),
        ("only_eat", "If you could only eat one meal for the rest of your life, what would it be?"),
        ("musical_experts", "What musical do you know well enough to sing every song?"),
        ("best_spiderman", "Who was the best Spider-Man?"),
        ("worst_film", "What was the worst film ever created?")
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

    def validate_security_question_2(self, field: Field) -> None:
        """
        Validates that the two selected security questions are different.

        Args:
            field (Field): The field for the second security question.

        Raises:
            ValidationError: If the second security question is the same as the first.
        """
        if field.data == self.security_question_1.data:
            raise ValidationError("Security questions must be different.")


# -----------------------------------------------------------------------------
# RegistrationStep3Form: Final step in registration.
# -----------------------------------------------------------------------------
class RegistrationStep3Form(FlaskForm):
    """
    Step 3 of registration: handles the account type selection and final submission.

    Attributes:
        account_type (HiddenField): Hidden field storing the chosen account type.
        submit (SubmitField): Form submission button.
    """
    account_type = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Register')


# -----------------------------------------------------------------------------
# DepositForm: Form for submitting a deposit.
# -----------------------------------------------------------------------------
class DepositForm(FlaskForm):
    """
    A form for entering a deposit amount.

    Attributes:
        deposit_amount (DecimalField): Field for entering the deposit amount in dollars.
        submit (SubmitField): Form submission button.
    """
    deposit_amount = DecimalField(
        'Deposit Amount ($)',
        validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive.")]
    )
    submit = SubmitField('Submit Deposit')
