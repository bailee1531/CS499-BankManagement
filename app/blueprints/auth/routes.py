from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.blueprints.auth.forms import LoginForm
from scripts.customer import webLogin

auth_bp = Blueprint('auth', __name__, template_folder='templates')  # path relative to the blueprint module

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Extract data from the form
        username = form.username.data
        password = form.password.data
        
        # Call your login function
        webLogin.login_page_button_pressed(2, username, password)

        session["user"] = username
        flash("Login Successful!")

        # Ensure that 'customer.dashboard' route exists or change to a valid endpoint.
        return redirect(url_for('customer.dashboard'))
    else:
        if "user" in session:
            flash("Already Logged In")
            return redirect(url_for('customer.dashboard'))

    return render_template('auth/login.html', form=form)
