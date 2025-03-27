from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.blueprints.auth.forms import LoginForm, RegistrationStep1Form, RegistrationStep2Form, SettingsForm
from scripts.customer import webLogin
import email_validator

# Create the authentication blueprint.
auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/customer/login', methods=['GET', 'POST'])
def login():
    """
    Login route for handling customer authentication.
    - GET: Renders the customer login page.
    - POST: Processes the login form and redirects the customer.
    """
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Call the login function for customers (type 2)
        webLogin.login_page_button_pressed(2, "Customer", username, password)
        session["user"] = username
        flash("Login Successful!")
        return redirect(url_for('customer.dashboard'))
    else:
        if "user" in session:
            flash("Already Logged In")
            return redirect(url_for('customer.dashboard'))

    return render_template('auth/login.html', form=form)

@auth_bp.route('/teller/login', methods=['GET', 'POST'])
def teller_login():
    """
    Login route for handling employee authentication.
    - GET: Renders the employee login page.
    - POST: Processes the login form and redirects the employee.
    """
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Call the login function for employees (using a different type code, e.g., 3)
        webLogin.login_page_button_pressed(2, "Teller", username, password)
        session["teller"] = username
        flash("Teller Login Successful!")
        return redirect(url_for('teller.dashboard'))
    else:
        if "teller" in session:
            flash("Already Logged In")
            return redirect(url_for('teller.dashboard'))

    return render_template('auth/teller_login.html', form=form)

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Login route for handling administrator authentication.
    - GET: Renders the admin login page.
    - POST: Processes the login form and redirects the admin.
    """
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Call the login function for admins (using another type code, e.g., 4)
        webLogin.login_page_button_pressed(2, "Admin", username, password)
        session["admin"] = username
        flash("Admin Login Successful!")
        return redirect(url_for('admin.dashboard'))
    else:
        if "admin" in session:
            flash("Already Logged In")
            return redirect(url_for('admin.dashboard'))

    return render_template('auth/admin_login.html', form=form)

@auth_bp.route('/customer/register/step1', methods=['GET', 'POST'])
def register_step1():
    form = RegistrationStep1Form()  # This form collects first_name, last_name, address, phone_number, tax_id, birthday.
    if form.validate_on_submit():
        session['step1'] = {
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
    form = RegistrationStep2Form()  # This form collects username, password, email, security questions, and answers.
    if form.validate_on_submit():
        step1_data = session.get('step1')
        if not step1_data:
            flash("Your session has expired. Please complete the first step again.", "danger")
            return redirect(url_for('auth.register_step1'))

        
        # Combine data from step 1 and step 2
        user_data = {
            "first_name": step1_data['first_name'],
            "last_name": step1_data['last_name'],
            "address": step1_data['address'],
            "phone_number": step1_data['phone_number'],
            "tax_id": step1_data['tax_id'],
            "birthday": step1_data['birthday'],
            "username": form.username.data,
            "password": form.password.data,
            "email": form.email.data,
            "security_question_1": form.security_question_1.data,
            "security_answer_1": form.security_answer_1.data.lower(),
            "security_question_2": form.security_question_2.data,
            "security_answer_2": form.security_answer_2.data.lower(),
        }

        # Call create account python script
        
        
        # Clear the session data for step1 after successful registration
        session.pop('step1', None)
        
        flash('Account successfully created. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_step2.html', form=form)

@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()

    # if not any(role in session for role in ('user', 'teller', 'admin')):
    #     flash("You must be logged in to access settings.", "warning")
    #     return redirect(url_for('auth.login'))

    # if form.validate_on_submit():
    #     # TODO: Save form data to user record (update database or CSV)
    #     flash("Settings updated successfully.", "success")
    #     return redirect(url_for('auth.settings'))

    return render_template('settings.html', form=form, title="User Settings")
