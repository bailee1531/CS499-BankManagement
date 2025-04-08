# ---------------------------
# Imports
# ---------------------------
import os
import pandas as pd
from functools import wraps
from flask import (
    current_app, session, abort,
    redirect, url_for, flash, request
)

# ---------------------------
# CSV Path Utilities
# ---------------------------
def get_csv_path(filename):
    """
    Constructs the full path to a CSV file stored in the 'csvFiles' directory.

    Args:
        filename (str): The name of the CSV file.

    Returns:
        str: Full file path to the CSV file.
    """
    return os.path.join(current_app.root_path, '..', 'csvFiles', filename)

# ---------------------------
# Session & Customer Utilities
# ---------------------------
def get_logged_in_customer():
    """
    Retrieves the logged-in customer's ID from the session. If not found, raises a 403 error.

    Returns:
        int: The logged-in customer's ID.

    Raises:
        abort(403): If the customer is not logged in.
    """
    customer_id = session.get("customer_id")
    if not customer_id:
        abort(403)  # Unauthorized access
    return customer_id

def user_has_account_type(customer_id, account_type):
    """
    Checks if a customer already has an account of a specific type.

    Args:
        customer_id (int): The customer's ID.
        account_type (str): The account type to check.

    Returns:
        bool: True if the customer has the specified account type, otherwise False.
    """
    accounts_csv = get_csv_path("accounts.csv")
    try:
        accounts = pd.read_csv(accounts_csv)
    except FileNotFoundError:
        return False  # If the CSV file is not found, return False
    
    # Check if the customer has an account of the specified type
    return not accounts[
        (accounts['CustomerID'] == customer_id) &
        (accounts['AccountType'] == account_type)
    ].empty

def get_customer_accounts(customer_id):
    """
    Retrieves all accounts associated with a specific customer.

    Args:
        customer_id (int): The customer's ID.

    Returns:
        DataFrame: A pandas DataFrame containing all accounts for the specified customer.
    """
    accounts_csv_path = get_csv_path("accounts.csv")
    accounts_df = pd.read_csv(accounts_csv_path)
    return accounts_df[accounts_df["CustomerID"] == customer_id]

def get_account_transactions(account_id):
    transactions_path = get_csv_path("transactions.csv")
    transactions_df = pd.read_csv(transactions_path)
    print("Account IDs in CSV:", transactions_df["AccountID"].unique())
    print("Filtering for Account ID:", account_id)

    return transactions_df[transactions_df["AccountID"] == account_id]


# ---------------------------
# Flash Utilities
# ---------------------------
def flash_error(message):
    """
    Flash an error message to the user.

    Args:
        message (str): The error message to display.
    """
    flash(message, "danger")

def flash_success(message):
    """
    Flash a success message to the user.

    Args:
        message (str): The success message to display.
    """
    flash(message, "success")

# ---------------------------
# Decorators
# ---------------------------
def login_required(session_key="customer"):
    """
    Decorator to ensure that a user is logged in before accessing a route.

    Args:
        session_key (str): The session key to check for the user's login status (default is 'customer').

    Returns:
        function: The wrapped function that requires the user to be logged in.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not session.get(session_key):
                flash("Login required", "danger")
                # Role-specific fallback
                if session_key == "teller" or session_key == "employee_id":
                    return redirect(url_for("employee.teller_login", next=request.url))
                elif session_key == "admin":
                    return redirect(url_for("employee.admin_login", next=request.url))
                else:
                    return redirect(url_for("auth.customer_login", next=request.url))
            return f(*args, **kwargs)
        return wrapper
    return decorator

