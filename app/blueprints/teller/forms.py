# Spring 2025 Authors: Bailee Segars, Braden Doty, Sierra Yerges
from flask_wtf import FlaskForm
from flask import request
from wtforms import StringField, PasswordField, DecimalField, SelectField, SubmitField, HiddenField, DateField, BooleanField
from wtforms.validators import Regexp, Optional, Length, Email, NumberRange, DataRequired
from app.blueprints.sharedUtilities import get_customer_accounts, flash_error

# ---------------------------------------------
# Tellers can modify their personal information
# ---------------------------------------------
class TellerSettingsForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Regexp(r'^\d{3}-\d{3}-\d{4}$')])
    email = StringField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[Optional(), Length(max=100)])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=25)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    current_password = PasswordField('Current Password', validators=[Optional()])

# ---------------------
# Base Transaction Form
# ---------------------
class AccountTransactionForm(FlaskForm):
    """
    Base form for common account transactions (Deposit/Withdraw).
    Includes account selection and amount field.
    """
    account_id: SelectField = SelectField(
        'Select Account',
        validators=[DataRequired()],
        coerce=str  # Can change to int if account IDs are integers
    )
    amount: DecimalField = DecimalField(
        'Amount',
        places=2,  # Ensures 2 decimal places for currency
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be greater than zero.")
        ]
    )

# ------------
# Deposit Form
# ------------
class DepositForm(AccountTransactionForm):
    """
    Form for making deposits to a selected account.
    """
    submit: SubmitField = SubmitField('Deposit')

# ---------------
# Withdrawal Form
# ---------------
class WithdrawForm(AccountTransactionForm):
    """
    Form for withdrawing funds from a selected account.
    """
    submit: SubmitField = SubmitField('Withdraw')

# -------------
# Transfer Form
# -------------
class TransferForm(FlaskForm):
    src_account = SelectField('', choices=[])
    dest_account = SelectField('', choices=[])
    amount = DecimalField(
        'Transfer Amount ($)',
        validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive.")]
    )

# -----------------
# Bill Payment Form
# -----------------
class BillPaymentForm(FlaskForm):
    """
    Form for processing bill payments by tellers.
    """
    bill_id = HiddenField('Bill ID')
    bill_type = HiddenField('Bill Type', default='Regular')
    
    billAccountId = SelectField(
        'Bill Account',
        validators=[DataRequired()],
        coerce=int
    )
    
    paymentSourceId = SelectField(
        'Payment Source Account',
        validators=[DataRequired()],
        coerce=int
    )
    
    amount = DecimalField(
        'Payment Amount ($)',
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Payment amount must be greater than zero.")
        ]
    )
    
    payee_name = StringField(
        'Payee Name',
        validators=[Optional(), Length(max=100)]
    )
    
    payee_address = StringField(
        'Payee Address',
        validators=[Optional(), Length(max=200)]
    )
    
    due_date = DateField(
        'Due Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    
    is_recurring = BooleanField(
        'Make Recurring Payment',
        default=False
    )
    
    submit = SubmitField('Process Payment')

# --------------------------------
# Dropdown for Choosing an Account
# --------------------------------
def choose_account():
    """
    Populates the dropdown fields with valid accounts.
    Returns:
    --------
    form: obj
        Form object to be referenced
    """
    form = TransferForm()
    data = request.get_json()
    customer_id = data.get("customerID")
    try:
        # Retrieve customer accounts data
        customer_accounts_df = get_customer_accounts(customer_id)
        choices = []
        # Iterate through the customer accounts and create a list of account information
        for _, row in customer_accounts_df.iterrows():
            # Only shows valid account types in the drop down
            if row["AccountType"] in ["Checking", "Savings", "Money Market"]:
               choices.append((str(row["AccountID"]), f"{row['AccountType']} {row['AccountID']}"))
        form.src_account.choices = choices
        form.dest_account.choices = choices
        return form
    except Exception as e:
        # If there is an error while retrieving the accounts, show an error message
        flash_error("Error retrieving account information.")
        form.src_account.choices = []  # Set an empty list for accounts on error
        form.dest_account.choices = []
        return form