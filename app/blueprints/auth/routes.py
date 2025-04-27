# Spring 2025 Authors: Bailee Segars, Braden Doty, Sierra Yerges, Taiyo Hino
# ====================
# Imports
# ====================

import pandas as pd
import logging
from typing import Tuple, Optional
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)

# App imports: Forms, business logic, and shared utilities
from app.blueprints.auth.forms import LoginForm, ResetPasswordForm
from scripts.customer import webLogin, resetPassword
from app.blueprints.sharedUtilities import (
    get_csv_path,
    flash_success, flash_error
)

# ====================
# Blueprint Setup
# ====================

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# ====================
# Constants
# ====================

NEW_ACCOUNT: int = 1
LOGIN: int = 2

# ====================
# Logger
# ====================

logger = logging.getLogger(__name__)

# ====================
# Helper Functions
# ====================

def process_login(form: LoginForm, session_key: str, login_type: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Process login form submission for different user types.

    Args:
        form (LoginForm): The login form instance.
        session_key (str): The session key to use ("customer", "teller", or "admin").
        login_type (int): The type of login attempt (LOGIN or NEW_ACCOUNT).

    Returns:
        Tuple[Optional[str], Optional[str]]:
            - Redirection URL on success
            - Error message on failure (if any)
    """
    # Prevent user from logging in again if already logged in
    if session.get(session_key):
        flash_error("Already Logged In", "warning")
        if session_key == "customer":
            return url_for('customer.customer_dashboard'), None
        elif session_key == "teller":
            return url_for('teller.teller_dashboard'), None
        elif session_key == "admin":
            return url_for('admin.admin_dashboard'), None
        else:
            return None, "Unknown session type"

    # Guard clause for invalid form submission
    if not form.validate_on_submit():
        return None, None

    username: str = form.username.data
    password: str = form.password.data

    # Look up CustomerID if customer login
    if session_key == "customer":
        try:
            customer_id: int = get_customer_id_by_username(username)
        except (IndexError, ValueError) as e:
            logger.error(f"Error retrieving customer ID for {username}: {e}")
            flash_error("Customer not found or data error")
            return None, str(e)

    # Determine user type for authentication
    if session_key == "customer":
        user_type: str = "Customer"
    elif session_key == "teller":
        user_type: str = "Teller"
    elif session_key == "admin":
        user_type: str = "Admin"
    else:
        return None, "Unknown session type"

    # Attempt login using external login function
    login_result = webLogin.login_page_button_pressed(login_type, user_type, username, password)
    if not login_result or login_result.get("status") == "error":
        error_message = login_result.get("message", "Login failed") if login_result else "Login function returned None"
        flash_error(error_message)
        return None, error_message

    # Store login session data
    session[session_key] = username
    if session_key == "customer":
        session["customer_id"] = int(customer_id)

    flash_success("Login Successful!")
    # Redirect to the appropriate dashboard based on the role
    if session_key == "customer":
        return url_for('customer.customer_dashboard'), None
    elif session_key == "teller":
        return url_for('teller.teller_dashboard'), None
    elif session_key == "admin":
        return url_for('admin.admin_dashboard'), None

    return None, "Unknown session type"



def handle_login(session_key: str, template_name: str) -> str:
    """
    General handler for rendering login form and processing login attempt.

    Args:
        session_key (str): Session key to store (customer, teller, admin).
        template_name (str): Template to render.

    Returns:
        str: Redirect or rendered template.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, session_key, LOGIN)

    if redirect_url:
        return redirect(next_url if next_url and next_url != "None" else redirect_url)

    return render_template(template_name, form=form)

def get_customer_id_by_username(username: str) -> int:
    """
    Look up CustomerID for a given username from the customer CSV.

    Args:
        username (str): The username to search for.

    Returns:
        int: The CustomerID.

    Raises:
        ValueError: If CSV is malformed.
        IndexError: If username is not found.
    """
    customer_csv_path: str = get_csv_path("customers.csv")
    user_info = pd.read_csv(customer_csv_path)

    if 'Username' not in user_info.columns or 'CustomerID' not in user_info.columns:
        raise ValueError("Malformed customer CSV: missing required columns.")

    customer_row = user_info[user_info['Username'] == username]
    if customer_row.empty:
        raise IndexError("Username not found in customer CSV.")

    return int(customer_row['CustomerID'].iloc[0])

# ====================
# Routes
# ====================

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    """
    Customer login page and logic.

    Returns:
        Response: Redirect on success, login form on failure.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "customer", LOGIN)
    
    if redirect_url:
        return redirect(next_url or redirect_url)

    return render_template("auth/login.html", form=form,
                           title="Evergreen Bank - Login",
                           header_text="Customer Login",
                           login_instructions="Enter your username and password to securely access your UAH Bank account.",
                           form_action=url_for('auth.customer_login'),
                           forgot_password_url=url_for('auth.forgot_password_page'),
                           show_signup_button=True,
                           signup_url=url_for("registration.register_step1"))

@auth_bp.route('/teller/login', methods=['GET', 'POST'])
def teller_login():
    """
    Teller login page and logic.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "teller", LOGIN)

    if redirect_url:
        return redirect(next_url or redirect_url)

    return render_template("auth/login.html", form=form,
                           title="Evergreen Bank - Teller Login",
                           header_text="Teller Login",
                           login_instructions="Please enter your teller username and password to log in.",
                           form_action=url_for('auth.teller_login'),
                           forgot_password_url=url_for('auth.forgot_password_page'),
                           show_signup_button=False)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login page and logic.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "admin", LOGIN)

    if redirect_url:
        return redirect(next_url or redirect_url)

    return render_template("auth/login.html", form=form,
                           title="Evergreen Bank - Admin Login",
                           header_text="Admin Login",
                           login_instructions="Enter your administrator credentials to log in.",
                           form_action=url_for('auth.admin_login'),
                           forgot_password_url=url_for('auth.forgot_password_page'),
                           show_signup_button=False)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_page():
    form = ResetPasswordForm()
    next_url = (
        request.args.get("next") or
        request.form.get("next") or
        "/"  # Fallback to homepage
    )

    if form.validate_on_submit():
        user_id = form.user_id.data
        answer1 = form.answer1.data
        answer2 = form.answer2.data
        new_password = form.new_password.data

        try:
            user_id = int(float(user_id))
        except (ValueError, TypeError):
            flash_error("Invalid user ID format.")
            return render_template("auth/forgot_password.html", form=form)

        result = resetPassword.forgot_password(user_id, answer1, answer2, new_password)

        if result["status"] == "success":
            flash_success(result["message"])
            return redirect(next_url)
        else:
            flash_error(result["message"])

    return render_template("auth/forgot_password.html", form=form)

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout route: Clears session and redirects to home.

    Returns:
        Response: Redirect to home.
    """
    session.clear()
    flash_success("You have been logged out.")
    return redirect(url_for('home'))
