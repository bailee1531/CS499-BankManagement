# blueprints/utilites.py

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
    return os.path.join(current_app.root_path, '..', 'csvFiles', filename)

# ---------------------------
# Session & Customer Utilities
# ---------------------------
def get_logged_in_customer():
    customer_id = session.get("customer_id")
    if not customer_id:
        abort(403)
    return customer_id

def user_has_account_type(customer_id, account_type):
    accounts_csv = get_csv_path("accounts.csv")
    try:
        accounts = pd.read_csv(accounts_csv)
    except FileNotFoundError:
        return False
    return not accounts[
        (accounts['CustomerID'] == customer_id) &
        (accounts['AccountType'] == account_type)
    ].empty

def get_customer_accounts(customer_id):
    accounts_csv_path = get_csv_path("accounts.csv")
    accounts_df = pd.read_csv(accounts_csv_path)
    return accounts_df[accounts_df["CustomerID"] == customer_id]

# ---------------------------
# Flash Utilities
# ---------------------------
def flash_error(message):
    flash(message, "danger")

def flash_success(message):
    flash(message, "success")

# ---------------------------
# Decorators
# ---------------------------
def login_required(session_key="customerID"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session_key not in session:
                flash("Login required", "danger")
                return redirect(url_for("auth.customer_login", next=request.url))
            return f(*args, **kwargs)
        return wrapper
    return decorator
