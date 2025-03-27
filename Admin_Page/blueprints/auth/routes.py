import os
import sys
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from blueprints.auth.forms import AdminLoginForm

# Allow import of logic/createTeller.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logic")))
from logic.createTeller import create_teller


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register')
def register_step1():
    return "Register Step 1 Page"

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Temporary admin check
        if username == "admin" and password == "admin123":
            return redirect(url_for("auth.admin_dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template('auth/admin_login.html', form=form)

@auth_bp.route('/teller-login')
def teller_login():
    return render_template('auth/teller_login.html')

@auth_bp.route('/admin-login')
def admin_login():
    form = AdminLoginForm()
    return render_template('auth/admin_login.html', form=form)

@auth_bp.route("/admin-dashboard")
def admin_dashboard():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../csvFiles/employees.csv"))
    df = pd.read_csv(csv_path)
    tellers = df[df["Position"] == "Teller"].to_dict(orient="records")
    return render_template("auth/admin_dashboard.html", tellers=tellers)

@auth_bp.route("/create-teller", methods=["POST"])
def create_teller_route():
    data = request.get_json()
    first = data.get("firstName", "").strip()
    last = data.get("lastName", "").strip()

    if first and last:
        create_teller(first, last)
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Missing first or last name"), 400
