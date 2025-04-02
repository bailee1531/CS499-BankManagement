# Importing necessary libraries from Flask-WTF and WTForms
from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from app.blueprints.sharedUtilities import (
    get_logged_in_customer, get_customer_accounts,
    flash_error
)

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