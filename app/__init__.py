"""
Flask Application Factory Module

This module defines a factory function to create and configure a Flask application.
It sets up configuration values, registers blueprints, and defines a basic home route.
"""

from datetime import timedelta
from flask import Flask, render_template, session, request, jsonify
import secrets
import os

def create_app(test_config=None):
    """
    Application factory function to create and configure the Flask app.

    Args:
        test_config (dict, optional): Configuration dictionary to override default settings.

    Returns:
        Flask app: Configured Flask application instance.
    """
    # Create an instance of the Flask application
    app = Flask(__name__)

    # Set a secret key for securely signing the session cookie
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

    # Configure the session lifetime (e.g., 30 minutes)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # ---------------------------
    # Register Blueprints
    # ---------------------------
    
    # Register the authentication blueprint (handles login, logout, etc.)
    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Register the accounts blueprint (handles user account management)
    from app.blueprints.accounts.routes import accounts_bp
    app.register_blueprint(accounts_bp)  

    # Register the customer blueprint (handles customer-specific features)
    from app.blueprints.customer.routes import customer_bp
    app.register_blueprint(customer_bp)  

    # Register the registration blueprint (handles user registration)
    from app.blueprints.registration.routes import register_bp
    app.register_blueprint(register_bp)  

    # Register the admin blueprint (handles admin stuff)
    from app.blueprints.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Register the teller blueprint (handles teller stuff)
    from app.blueprints.teller.routes import teller_bp
    app.register_blueprint(teller_bp, url_prefix="/teller")


    # ---------------------------
    # Home Routes
    # ---------------------------
    
    # Define a simple home route that renders the index.html template
    @app.route('/')
    def home():
        """
        Home route that renders the homepage.
        """
        session.pop("employee_mode", None)
        return render_template("index.html")

    # Employee home route that renders the employee homepage
    @app.route('/employee-home')
    def employee_home():
        """
        Employee Home route that renders the employee homepage.
        """
        session["employee_mode"] = True
        return render_template("employee_home.html")
    
    @app.errorhandler(403)
    def page_not_found(e):
        return render_template("page_error.html"), 403
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("page_error.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        # if a request has the wrong method to the API
        if request.path.startswith('/api/'):
            # we return a json saying so
            return jsonify(message="Method Not Allowed"), 405
        else:
            # otherwise we return a generic site-wide 405 page
            return render_template("page_error.html"), 405
        
    @app.errorhandler(415)
    def page_not_found(e):
        return render_template("page_error.html"), 415
    
    @app.errorhandler(500)
    def page_not_found(e):
        return render_template("page_error.html"), 500
    
    @app.errorhandler(502)
    def page_not_found(e):
        return render_template("page_error.html"), 502
    
    @app.errorhandler(503)
    def page_not_found(e):
        return render_template("page_error.html"), 503

    return app
