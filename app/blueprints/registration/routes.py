import pandas as pd
from decimal import Decimal
from datetime import date, timedelta
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session
)
import logging

# Import forms for registration and deposit
from app.blueprints.registration.forms import (
    TellerUsernameForm,
    RegistrationStep1Form, 
    RegistrationStep2Form
)

# Import customer operations and utilities for account creation
from scripts.customer import webLogin, openAcc
from scripts import createCreditCard
from scripts import createCreditCard
from scripts.billPayment import scheduleBillPayment

# Import shared utilities for checking account type and managing flash messages
from app.blueprints.sharedUtilities import (
    user_has_account_type, get_csv_path, 
    flash_success, flash_error
)

# Define the registration blueprint
register_bp = Blueprint('registration', __name__, template_folder='templates')

# Constants for login type (new account vs. existing account)
NEW_ACCOUNT: int = 1
LOGIN: int = 2

# Set up logger for debugging and logging
logger = logging.getLogger(__name__)

def get_customer_id_by_username(username: str) -> int:
    """
    Retrieve a customer's ID from the CSV based on their username.

    Args:
        username (str): The username to search for.

    Returns:
        int: The customer's ID.

    Raises:
        ValueError: If required columns are missing.
        IndexError: If the username is not found.
    """
    # Path to the customer CSV file
    customer_csv_path: str = get_csv_path("customers.csv")
    user_info = pd.read_csv(customer_csv_path)

    # Check if the necessary columns exist in the CSV
    if 'Username' not in user_info.columns or 'CustomerID' not in user_info.columns:
        raise ValueError("Malformed customer CSV: missing required columns.")

    # Find the row that matches the given username
    customer_row = user_info[user_info['Username'].str.lower() == username.lower()]
    if customer_row.empty:
        raise IndexError("Username not found in customer CSV.")

    # Return the customer ID
    return int(customer_row['CustomerID'].iloc[0])


@register_bp.route('/customer/register/step1', methods=['GET', 'POST'])
def register_step1():
    """
    First step of customer registration.
    Collects personal details and stores them in session, then redirects to step 2.

    Returns:
        Response: Redirects to step 2 on success, or renders the registration form if validation fails.
    """
    form = RegistrationStep1Form()
    if form.validate_on_submit():
        # Store collected data in session
        session['registration'] = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'address': form.address.data,
            'phone_number': form.phone_number.data,
            'tax_id': form.tax_id.data,
            'birthday': form.birthday.data,
        }
        return redirect(url_for('registration.register_step2'))
    return render_template('registration/register_step1.html', form=form)

@register_bp.route('/customer/register/step2', methods=['GET', 'POST'])
def register_step2():
    """
    Second step of registration.
    Checks for username availability and stores login/security details.

    Returns:
        Response: Redirect to customer dashboard on success, otherwise renders the registration form.
    """
    form = RegistrationStep2Form()
    if form.validate_on_submit():
        # Check if the username is already taken
        usernames = pd.read_csv(get_csv_path("customers.csv"))['Username'].str.lower()
        if form.username.data.lower() in usernames.values:
            flash_error("Username already taken. Please choose another.")
            return render_template('registration/register_step2.html', form=form)

        # Store login and security details in session
        registration = session.get('registration', {})
        registration.update({
            'username': form.username.data.lower(),
            'password': form.password.data,
            'email': form.email.data,
            'security_question_1': form.security_question_1.data,
            'security_answer_1': form.security_answer_1.data.lower(),
            'security_question_2': form.security_question_2.data,
            'security_answer_2': form.security_answer_2.data.lower(),
        })
        session['registration'] = registration
                # Attempt to create a new customer account
        login_result = webLogin.login_page_button_pressed(
            NEW_ACCOUNT,
            "Customer",
            registration['username'],
            registration['password'],
            registration['first_name'],
            registration['last_name'],
            registration['address'],
            registration['email'],
            registration['phone_number'],
            registration['tax_id'],
            registration['security_answer_1'],
            registration['security_answer_2'],
        )

        if login_result.get("status") != "success":
            flash_error(login_result.get("message", "Registration failed."))
            return redirect(url_for('registration.register_step1'))

        # Registration success
        session.clear()
        session['customer'] = registration['username']
        session['customer_id'] = get_customer_id_by_username(registration['username'])
        flash_success("Welcome to your dashboard!")
        return redirect(url_for("customer.customer_dashboard"))
    return render_template('registration/register_step2.html', form=form)

@register_bp.route("/register/teller-username", methods=["GET", "POST"])
def register_teller_username():
    if not session.get("employee_mode"):
        return redirect(url_for("home"))

    form = TellerUsernameForm()

    if form.validate_on_submit():
        # Read from employees.csv
        df = pd.read_csv(get_csv_path("employees.csv"))
        username_input = form.username.data.strip().lower()

        # Match user by lowercased username
        matched_user = df[df['Username'].str.lower() == username_input]

        if matched_user.empty:
            flash_error("This username is not recognized. Please ask your admin to create your account.")
            return redirect(url_for('registration.register_teller_username'))

        # Extract and split username into first and last names
        user_row = matched_user.iloc[0]
        full_username = user_row['Username']
        first_name, last_name = full_username.split('.', 1)

        first_name = first_name.capitalize()
        last_name = last_name.capitalize()

        # Save pre-filled data in session
        session['registration'] = {
            'first_name': first_name,
            'last_name': last_name,
            'username': full_username,
            'email': f"{first_name}.{last_name}@evergreen.com"
        }

        return redirect(url_for('registration.register_teller_step1'))

    return render_template("registration/register_teller_username.html", form=form)

@register_bp.route("/register/teller-step1", methods=["GET", "POST"])
def register_teller_step1():
    if not session.get("employee_mode"):
        return redirect(url_for("home"))

    registration = session.get("registration", {})
    if "username" not in registration:
        return redirect(url_for("registration.register_teller_username"))

    form = RegistrationStep1Form()

    if form.validate_on_submit():
        session['registration'].update({
            'address': form.address.data,
            'phone_number': form.phone_number.data,
            'tax_id': form.tax_id.data,
            'birthday': form.birthday.data,
        })
        session.modified = True
        return redirect(url_for('registration.register_teller_step2'))

    # Pre-fill first and last name from session
    form.first_name.data = registration.get("first_name", "")
    form.last_name.data = registration.get("last_name", "")


    return render_template('registration/register_teller_step1.html', form=form, disable_name_fields=True)

@register_bp.route("/register/teller-step2", methods=["GET", "POST"])
def register_teller_step2():
    if not session.get("employee_mode"):
        return redirect(url_for("home"))

    registration = session.get('registration', {})
    required_keys = ['first_name', 'last_name', 'username', 'address', 'phone_number', 'tax_id', 'birthday']

    if not all(key in registration for key in required_keys):
        flash_error("Your session has expired or is incomplete. Please restart the registration.")
        return redirect(url_for('registration.register_teller_username'))

    form = RegistrationStep2Form()

    # Pre-fill and disable username and email
    form.username.data = registration['username']
    form.username.data = form.username.data.lower()
    form.email.data = registration['email']
    form.confirm_email.data = registration['email']

    if form.validate_on_submit():
        result = webLogin.login_page_button_pressed(
            NEW_ACCOUNT,
            "Teller",
            registration['username'],  # Use from session
            form.password.data,
            registration['first_name'],
            registration['last_name'],
            registration['address'],
            registration['email'],
            registration['phone_number'],
            registration['tax_id'],
            form.security_answer_1.data,
            form.security_answer_2.data,
        )

        if result.get("status") != "success":
            flash_error(result.get("message", "Registration failed."))
            return redirect(url_for('registration.register_teller_step1'))

        # Registration success
        session.clear()
        session['teller'] = registration['username']
        session['role'] = 'teller'
        flash_success("Welcome to your dashboard!")
        return redirect(url_for("teller.teller_dashboard"))

    return render_template("registration/register_teller_step2.html", form=form, disable_username=True, disable_email_field=True, disable_confirm_email_field=True)
