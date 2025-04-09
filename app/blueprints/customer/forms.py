from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField, StringField, DateField, PasswordField
from wtforms.validators import DataRequired, NumberRange, InputRequired, Optional, Length, Regexp, Email
from app.blueprints.sharedUtilities import (
    get_logged_in_customer,
    get_customer_accounts, 
    flash_error
)


class AccountTransactionForm(FlaskForm):
    """
    Base form for common account transactions (Deposit/Withdraw).
    Includes account selection and amount field.
    """
    account_id = SelectField(
        'Select Account',
        coerce=int,  # Ensure selected value is cast to int
        validators=[DataRequired()]
    )
    amount = DecimalField(
        'Amount',
        places=2,  # Ensures 2 decimal places for currency
        validators=[
            DataRequired(),
            NumberRange(min=0.01, message="Amount must be greater than zero.")
        ]
    )


class DepositForm(AccountTransactionForm):
    """
    Form for making deposits to a selected account.
    """
    submit = SubmitField('Deposit')


class WithdrawForm(AccountTransactionForm):
    """
    Form for withdrawing funds from a selected account.
    """
    submit = SubmitField('Withdraw')

# -----------------------------------------------------------------------------
# TransferForm: Form for transferring funds.
# -----------------------------------------------------------------------------
class TransferForm(FlaskForm):
    src_account = SelectField('', choices=[])
    dest_account = SelectField('', choices=[])
    amount = DecimalField(
        'Transfer Amount ($)',
        validators=[DataRequired(), NumberRange(min=0, message="Amount must be positive.")]
    )

def choose_account():
    """
    Populates the dropdown fields with valid accounts.
    Returns:
    --------
    form: obj
        Form object to be referenced
    """
    form = TransferForm()
    customer_id: int = get_logged_in_customer()  # Get the logged-in customer's ID
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
    current_password = PasswordField('Current Password', validators=[Optional(), Length(min=8)])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    submit = SubmitField('Update Settings')

class BillPaymentForm(FlaskForm):
    bill_id = StringField("Bill ID", validators=[DataRequired()])
    payee_name = StringField("Payee Name")
    payee_address = StringField("Payee Address")
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    due_date = DateField("Due Date", format='%Y-%m-%d', validators=[InputRequired()])
    paymentAccID = SelectField("Payment Account", choices=[], coerce=int)
    submit = SubmitField("Pay Bill")
