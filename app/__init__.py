import os
from datetime import timedelta
from flask import Flask, render_template

def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = "hello"  # Set the secret key on the app instance
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Configure session lifetime


    # Register your blueprints
    from app.blueprints.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # A simple home route (if needed)
    @app.route('/')
    def home():
        return render_template("index.html")

    return app
