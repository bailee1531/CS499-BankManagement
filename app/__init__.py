"""
Flask Application Factory Module

This module defines a factory function to create and configure a Flask application.
It sets up configuration values, registers blueprints, and defines a basic home route.
"""

import os
from datetime import timedelta
from flask import Flask, render_template

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
    app.secret_key = "hello"  

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

    # ---------------------------
    # Home Routes
    # ---------------------------
    
    # Define a simple home route that renders the index.html template
    @app.route('/')
    def home():
        """
        Home route that renders the homepage.
        """
        return render_template("index.html")

    # Employee home route that renders the employee homepage
    @app.route('/employee-home')
    def employee_home():
        """
        Employee Home route that renders the employee homepage.
        """
        return render_template("employee_home.html")

    return app
