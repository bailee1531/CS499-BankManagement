from flask import Flask, render_template
from flask_blueprints import *
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "hello"  # Set the secret key on the app instance
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Configure session lifetime

app.register_blueprint(userAuth_blueprint, url_prefix="/login")

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
