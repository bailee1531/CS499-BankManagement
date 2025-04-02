"""
forms.py

This module defines Flask-WTF forms used for user mortgage applications.
"""

from flask_wtf import FlaskForm
from wtforms import DecimalField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

# -----------------------------------------------------------------------------
# MortgageForm: Form for submitting a mortgage application.
# -----------------------------------------------------------------------------
class MortgageForm(FlaskForm):
    """
    A form for applying for a mortgage.

    Fields:
        current_income (DecimalField): User's current income.
        loan_amount (DecimalField): Desired mortgage loan amount.
        loan_term (IntegerField): Length of the loan in years.
        submit (SubmitField): Button to submit the application.
    """

    current_income = DecimalField(
        'Current Income ($)',
        validators=[
            DataRequired(), 
            NumberRange(min=0, message="Income must be positive.")
        ]
    )

    loan_amount = DecimalField(
        'Loan Amount ($)',
        validators=[
            DataRequired(), 
            NumberRange(min=0, message="Loan amount must be positive.")
        ]
    )

    loan_term = IntegerField(
        'Loan Term (Years)',
        validators=[
            DataRequired(), 
            NumberRange(min=1, message="Loan term must be at least 1 year.")
        ]
    )

    submit = SubmitField('Submit Application')
