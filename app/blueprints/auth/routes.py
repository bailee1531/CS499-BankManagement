"""
Authentication Blueprint Module

This module defines the blueprint for authentication-related routes.
It includes a login route that handles both GET and POST requests to process user login.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.blueprints.auth.forms import LoginForm
from scripts.customer import webLogin

# Create the authentication blueprint.
# The template_folder parameter specifies the location of blueprint templates relative to this module.
auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route for handling user authentication.

    - GET: Renders the login page with the login form.
    - POST: Processes the login form, performs authentication, and redirects the user.
    
    Returns:
        A rendered template for GET requests, or a redirect response after successful login.
    """
    # Instantiate the login form
    form = LoginForm()

    # Check if the form is submitted and valid
    if form.validate_on_submit():
        # Extract username and password from the form
        username = form.username.data
        password = form.password.data
        
        # Call the login function from the webLogin module with provided credentials
        webLogin.login_page_button_pressed(2, username, password)

        # Store the username in the session to keep track of the logged-in user
        session["user"] = username

        # Flash a success message to the user
        flash("Login Successful!")

        # Redirect the user to the dashboard page
        # Ensure that the 'customer.dashboard' route exists or update the endpoint accordingly
        return redirect(url_for('customer.dashboard'))
    else:
        # If the form is not submitted, but the user is already in session,
        # notify and redirect them to the dashboard.
        if "user" in session:
            flash("Already Logged In")
            return redirect(url_for('customer.dashboard'))

    # Render the login template with the form if not already redirected
    return render_template('auth/login.html', form=form)
