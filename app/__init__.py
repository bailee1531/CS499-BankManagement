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
    app.secret_key = "hello"  # In production, use a more secure and environment-specific key

    # Configure the session lifetime (e.g., 30 minutes)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    # Register blueprints with the application
    # Authentication blueprint
    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Accounts blueprint
    from app.blueprints.accounts.routes import accounts_bp
    app.register_blueprint(accounts_bp)  # uses /accounts from the blueprint itself

    # Define a simple home route that renders the index.html template
    @app.route('/')
    def home():
        """
        Home route that renders the homepage.
        """
        return render_template("index.html")

    @app.route('/employee-home')
    def employee_home():
        """
        Employee Home route that renders the employee homepage.
        """
        return render_template("employee_home.html")

    return app
