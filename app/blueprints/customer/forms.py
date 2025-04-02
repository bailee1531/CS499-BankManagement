# Importing necessary libraries from Flask-WTF and WTForms
from flask_wtf import FlaskForm
from wtforms import SelectField
from app.blueprints.sharedUtilities import (
    get_logged_in_customer, get_customer_accounts,
    flash_error
)

class AccountsForm(FlaskForm):
    group_id = SelectField(u'Accounts', choices=[])

def choose_src():
    customer_id: int = get_logged_in_customer()  # Get the logged-in customer's ID
    srcForm = AccountsForm()
    try:
        # Retrieve customer accounts data
        customer_accounts_df = get_customer_accounts(customer_id)
        srcChoices = []
        # Iterate through the customer accounts and create a list of account information
        for _, row in customer_accounts_df.iterrows():
            if row["AccountType"] in ["checking", "savings", "money market"]:
               srcChoices.append((str(row["AccountID"]), f"{row['AccountType']} {row['AccountID']}"))
        srcForm.group_id.choices = srcChoices
        return srcForm
    except Exception as e:
        # If there is an error while retrieving the accounts, show an error message
        flash_error("Error retrieving account information.")
        srcForm.group_id.choices = []  # Set an empty list for accounts on error
        return srcForm
    
def choose_dest():
    customer_id: int = get_logged_in_customer()  # Get the logged-in customer's ID
    destForm = AccountsForm()
    try:
        # Retrieve customer accounts data
        customer_accounts_df = get_customer_accounts(customer_id)
        destChoices = []
        # Iterate through the customer accounts and create a list of account information
        for _, row in customer_accounts_df.iterrows():
            if row["AccountType"] in ["checking", "savings", "money market"]:
               destChoices.append((str(row["AccountID"]), f"{row['AccountType']} {row['AccountID']}"))
        destForm.group_id.choices = destChoices
        return destForm
    except Exception as e:
        # If there is an error while retrieving the accounts, show an error message
        flash_error("Error retrieving account information.")
        destForm.group_id.choices = []  # Set an empty list for accounts on error
        return destForm