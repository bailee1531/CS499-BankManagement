from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from scripts.customer import webLogin

# Create a Flask Blueprint for user authentication
userAuth_blueprint = Blueprint(
    "userAuth_blueprint", __name__, static_folder="static", template_folder="template"
)

@userAuth_blueprint.route("/customer", methods=["POST", "GET"])
def login():
    """
    Handle login requests for customers.
    If the request is POST, process login credentials.
    If the request is GET, check if the user is already logged in and redirect accordingly.
    """
    if request.method == "POST":
        session.permanent = True  # Make session data persistent
        
        # Retrieve username and password from form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Call the login function from the webLogin module
        webLogin.login_page_button_pressed(2, username, password)

        # Store the username in session
        session["user"] = username
        
        flash("Login Successful!")
        return f"{username}   {password}"
    
    else:
        # If user is already logged in, redirect to the user dashboard
        if "user" in session:
            flash("Already Logged In")
            return redirect(url_for("user"))

        # Render the login page
        return render_template("login.html")
