import pandas as pd
from flask import Blueprint, render_template, Response, redirect, url_for
from app.blueprints.sharedUtilities import (
    get_csv_path, get_logged_in_customer,
    get_customer_accounts, 
    login_required, flash_error
)

# Create a Blueprint for the customer-related routes
customer_bp = Blueprint('customer', __name__, template_folder='templates')

@customer_bp.route('/Dashboard')
@login_required("customer_id")
def customer_dashboard() -> Response:
    """
    Render the user's dashboard displaying their accounts.

    Retrieves the customer's account information from the database and displays it on the dashboard.

    Returns:
        Response: Rendered template for the user's dashboard with account details.
    """
    customer_id: int = get_logged_in_customer()  # Get the logged-in customer's ID
    
    try:
        # Retrieve customer accounts data
        customer_accounts_df = get_customer_accounts(customer_id)
        accounts_list = []

        # Iterate through the customer accounts and create a list of account information
        for _, row in customer_accounts_df.iterrows():
            accounts_list.append({
                "account_id": row["AccountID"],
                "account_type": row["AccountType"],
                "curr_bal": row["CurrBal"]
            })
    except Exception as e:
        # If there is an error while retrieving the accounts, show an error message
        flash_error("Error retrieving account information.")
        accounts_list = []  # Set an empty list for accounts on error

    # Render the customer dashboard template with the list of accounts
    return render_template("customer/customer_dashboard.html", accounts=accounts_list)

@customer_bp.route('/account/<int:account_id>')
@login_required("customer_id")
def account_detail(account_id: int) -> Response:
    """
    Display detailed information for a specific account.

    Retrieves and displays the details for a particular account by its account ID.

    Args:
        account_id (int): The ID of the account to display.

    Returns:
        Response: Rendered template with account details or redirection on error.
    """
    try:
        # Load account data from CSV file
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
        
        # Find the specific account row based on the account ID
        account_row = accounts_df[accounts_df["AccountID"] == account_id]
        
        # If the account is not found, show an error and redirect to the dashboard
        if account_row.empty:
            flash_error("Account not found.")
            return redirect(url_for("customer.customer_dashboard"))
        
        # Convert the account row to a dictionary for easy access in the template
        account = account_row.iloc[0].to_dict()
    except Exception as e:
        # If there is an error retrieving account details, show an error message and redirect
        flash_error("Error retrieving account details.")
