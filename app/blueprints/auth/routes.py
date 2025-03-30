import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from decimal import Decimal
import logging
from typing import Tuple, Optional

# Import forms for authentication and registration
from app.blueprints.auth.forms import (
    LoginForm, 
    RegistrationStep1Form, 
    RegistrationStep2Form, 
    RegistrationStep3Form, 
    DepositForm,
    MortgageForm
)

# Import customer operations and utilities for credit card/loan creation
from scripts.customer import webLogin, openAcc
from scripts import createCreditCard, createLoan

from app.blueprints.utilities import (
    get_csv_path, get_logged_in_customer, user_has_account_type,
    flash_success, flash_error
)

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Constants for login type
NEW_ACCOUNT: int = 1
LOGIN: int = 2

logger = logging.getLogger(__name__)

def process_login(form: LoginForm, session_key: str, login_type: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Process login form submission for different user types.

    Checks if the user is already logged in, validates the form, attempts login,
    sets session data, and returns a redirection URL or an error message.

    Args:
        form (LoginForm): The login form instance.
        session_key (str): The session key to use (e.g., "user", "teller", "admin").
        login_type (int): The type of login attempt.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing the redirection URL (if successful)
        and an error message (if any).
    """
    # Prevent duplicate login
    if session_key in session:
        flash("Already Logged In")
        return url_for(f'accounts.{session_key}_dashboard'), None

    if form.validate_on_submit():
        username: str = form.username.data
        password: str = form.password.data

        # Retrieve customer_id if a customer login is attempted
        if session_key == "user":
            try:
                customer_id: int = get_customer_id_by_username(username)
            except (IndexError, ValueError) as e:
                flash_error("User not found or data error")
                return None, str(e)

        user_type: str = "Customer" if session_key == "user" else "Employee"
        # Attempt login using the webLogin service
        login_result = webLogin.login_page_button_pressed(login_type, user_type, username, password)
        if not login_result or login_result.get("status") == "error":
            error_message = login_result.get("message", "Login failed") if login_result else "Login function returned None"
            flash_error(error_message)
            return None, error_message

        # Store session information upon successful login
        session[session_key] = username
        if session_key == "user":
            session["customer_id"] = int(customer_id)

        flash_success("Login Successful!")
        return url_for(f'accounts.{session_key}_dashboard'), None

    return None, None

def handle_login(session_key: str, template_name: str) -> str:
    """
    Handle login for a given user type and render the appropriate template.

    Args:
        session_key (str): The session key for the user type.
        template_name (str): The template to render.

    Returns:
        str: A redirection response or the rendered template.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, session_key, LOGIN)

    if redirect_url:
        # Redirect to the 'next' page if provided, otherwise to the dashboard
        return redirect(next_url if next_url and next_url != "None" else redirect_url)

    return render_template(template_name, form=form)

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
    customer_csv_path: str = get_csv_path("customers.csv")
    user_info = pd.read_csv(customer_csv_path)

    if 'Username' not in user_info.columns or 'CustomerID' not in user_info.columns:
        raise ValueError("Malformed customer CSV: missing required columns.")

    customer_row = user_info[user_info['Username'].str.lower() == username.lower()]
    if customer_row.empty:
        raise IndexError("Username not found in customer CSV.")

    return int(customer_row['CustomerID'].iloc[0])

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    """
    Customer login route.

    Returns:
        Response: Redirect to dashboard if successful, otherwise renders login template.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "user", LOGIN)
    if redirect_url:
        return redirect(next_url or redirect_url)
    return render_template("auth/login.html", form=form,
                           title="UAH Bank - Login",
                           header_text="Customer Login",
                           login_instructions="Enter your username and password to securely access your UAH Bank account.",
                           form_action=url_for('auth.customer_login'),
                           show_signup_button=True,
                           signup_url=url_for("auth.register_step1"))

@auth_bp.route('/teller/login', methods=['GET', 'POST'])
def teller_login():
    """
    Teller login route.

    Returns:
        Response: Redirect to dashboard if successful, otherwise renders login template.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "teller", LOGIN)
    if redirect_url:
        return redirect(next_url or redirect_url)
    return render_template("auth/login.html", form=form,
                           title="UAH Bank - Teller Login",
                           header_text="Teller Login",
                           login_instructions="Please enter your teller username and password to log in.",
                           form_action=url_for('auth.teller_login'),
                           forgot_password_url="#",  # adjust as needed
                           show_signup_button=False)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin login route.

    Returns:
        Response: Redirect to dashboard if successful, otherwise renders login template.
    """
    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    redirect_url, error = process_login(form, "admin", LOGIN)
    if redirect_url:
        return redirect(next_url or redirect_url)
    return render_template("auth/login.html", form=form,
                           title="UAH Bank - Admin Login",
                           header_text="Admin Login",
                           login_instructions="Enter your administrator credentials to log in.",
                           form_action=url_for('auth.admin_login'),
                           forgot_password_url="#",  # adjust as needed
                           show_signup_button=False)

@auth_bp.route('/customer/register/step1', methods=['GET', 'POST'])
def register_step1():
    """
    First step of customer registration.
    Stores personal details in session and redirects to step 2.

    Returns:
        Response: Redirect to step 2 on success, otherwise renders registration form.
    """
    form = RegistrationStep1Form()
    if form.validate_on_submit():
        session['registration'] = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'address': form.address.data,
            'phone_number': form.phone_number.data,
            'tax_id': form.tax_id.data,
            'birthday': form.birthday.data,
        }
        return redirect(url_for('auth.register_step2'))
    return render_template('auth/register_step1.html', form=form)

@auth_bp.route('/customer/register/step2', methods=['GET', 'POST'])
def register_step2():
    """
    Second step of registration.
    Checks for username availability and stores login/security details.

    Returns:
        Response: Redirect to step 3 on success, otherwise renders registration form.
    """
    form = RegistrationStep2Form()
    if form.validate_on_submit():
        usernames = pd.read_csv(get_csv_path("customers.csv"))['Username'].str.lower()
        if form.username.data.lower() in usernames.values:
            flash_error("Username already taken. Please choose another.")
            return render_template('auth/register_step2.html', form=form)

        # Update session with registration details
        registration = session.get('registration', {})
        registration.update({
            'username': form.username.data,
            'password': form.password.data,
            'email': form.email.data,
            'security_question_1': form.security_question_1.data,
            'security_answer_1': form.security_answer_1.data.lower(),
            'security_question_2': form.security_question_2.data,
            'security_answer_2': form.security_answer_2.data.lower(),
        })
        session['registration'] = registration
        return redirect(url_for('auth.register_step3'))
    return render_template('auth/register_step2.html', form=form)

@auth_bp.route('/customer/register/step3', methods=['GET', 'POST'])
def register_step3():
    """
    Final registration step.
    Completes registration, creates the new account, and opens additional account types if needed.

    Returns:
        Response: Redirects to deposit form or dashboard on success, otherwise renders registration form.
    """
    form = RegistrationStep3Form()
    if form.validate_on_submit():
        registration = session.get('registration')
        if not registration:
            flash_error("Your session has expired. Please complete the registration again.")
            return redirect(url_for('auth.register_step1'))

        registration['account_type'] = form.account_type.data
        session['registration'] = registration

        # Create new customer account using webLogin
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
        if login_result.get("status") == "error":
            flash_error(login_result.get("message", "Registration failed"))
            return redirect(url_for('auth.register_step1'))

        try:
            customer_id = get_customer_id_by_username(registration['username'])
        except Exception as e:
            flash_error(f"Error retrieving customer ID: {str(e)}")
            return redirect(url_for('auth.register_step1'))

        # Set session variables for a successful registration
        session["customer_id"] = customer_id
        session["user"] = registration["username"]

        if registration['account_type'] == 'travel_visa':
            try:
                createCreditCard.openCreditCardAccount(customer_id)
                flash_success("Travel visa account opened successfully!")
                session.pop('registration', None)
                return redirect(url_for('accounts.user_dashboard'))
            except Exception as e:
                flash_error(f"Unable to open travel visa account: {str(e)}")
                return redirect(url_for('auth.register_step1'))

        # For other account types, mark pending deposit step
        session['pending_account_type'] = registration['account_type']
        session['pending_account_name'] = registration['account_type']
        session.pop('registration', None)
        flash_success("Registration complete! Please proceed with your initial deposit to open your account.")
        return redirect(url_for('auth.deposit_form'))

    return render_template('auth/register_step3.html', form=form)

@auth_bp.route('/deposit', methods=['GET', 'POST'])
def deposit_form():
    """
    Route to handle deposit form submission for opening an account.

    Returns:
        Response: Redirect to user dashboard on success, otherwise renders deposit form.
    """
    form = DepositForm()
    customer_id = session.get("customer_id")
    pending_account_type = session.get("pending_account_type")
    pending_account_name = session.get("pending_account_name")

    # Ensure session has required data
    if not customer_id or not pending_account_type:
        flash_error("Session expired or incomplete. Please try again.")
        return redirect(url_for("accounts.personal_accounts"))

    # Check if user already has an account of this type
    if user_has_account_type(customer_id, pending_account_type):
        flash_error("You already have an account of this type. Only one account of each type is allowed per user.")
        return redirect(url_for("accounts.user_dashboard"))

    if form.validate_on_submit():
        deposit_amount = form.deposit_amount.data
        try:
            openAcc.open_account(customer_id, pending_account_type, deposit_amount)
            flash_success(f"{pending_account_name} opened successfully with an initial deposit of {deposit_amount}!")
            session.pop('pending_account_type', None)
            session.pop('pending_account_name', None)
            return redirect(url_for("accounts.user_dashboard"))
        except Exception as e:
            flash_error(f"Error opening account: {str(e)}")

    return render_template(
        'auth/deposit_form.html', 
        account_type=pending_account_name,
        form=form,
        form_action=url_for('auth.deposit_form')
    )

@auth_bp.route('/customer/mortgage', methods=['GET', 'POST'])
def mortgage_application():
    """
    Route for mortgage loan application.

    Returns:
        Response: Redirects to dashboard on success, otherwise renders the mortgage application form.
    """
    form = MortgageForm()
    if form.validate_on_submit():
        loan_amount = Decimal(form.loan_amount.data)
        loan_term = form.loan_term.data
        customer_id = session.get("customer_id")
        if not customer_id:
            flash_error("Customer not logged in or session expired.")
            return redirect(url_for('auth.customer_login'))

        result = createLoan.createMortgageLoanAccount(customer_id, loan_amount, loan_term)
        if result.get("status") == "success":
            flash_success(result.get("message"))
            return redirect(url_for('accounts.user_dashboard'))
        else:
            flash_error(result.get("message"))

    return render_template(
        'auth/collectMortgageInfo.html',
        form=form,
        form_action=url_for('auth.mortgage_application')
    )

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout route that clears session data and redirects to home.

    Returns:
        Response: Redirect to home page.
    """
    session_keys = ['user', 'customer_id', 'teller', 'admin']
    for key in session_keys:
        session.pop(key, None)
    flash_success("You have been logged out.")
    return redirect(url_for('home'))
