import os
import sys
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.blueprints.auth.forms import LoginForm
from scripts.createTeller import create_teller
from scripts.makeDeposit import deposit as make_deposit
from scripts.customer.modifyInfo import modify_info as modify_username
from scripts.customer.deleteUser import delete_user_button_pressed as delete_customer_logic
from scripts.withdrawMoney import withdraw as withdraw_money
from scripts.fundTransfer import transferFunds as transfer_funds

# Blueprint for employee routes
employee_bp = Blueprint('employee', __name__, template_folder='templates')

# Admin Login Route
@employee_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()

    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        print(f"Username: {username}, Password: {password}")

        if username == "admin" and password == "admin123":
            return redirect(url_for("employee.admin_dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("auth/login.html", form=form,
                       title="UAH Bank - Admin Login",
                       header_text="Admin Login",
                       login_instructions="Enter your administrator credentials to log in.",
                       form_action=url_for('employee.admin_login'),
                       forgot_password_url="#",
                       show_signup_button=False)

# Admin Dashboard Route
@employee_bp.route("/admin-dashboard")
def admin_dashboard():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/employees.csv"))

    try:
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
            df = pd.read_csv(csv_path)

            # Check if required columns exist
            if all(col in df.columns for col in ["Username", "EmployeeID", "Position"]):
                tellers = df[df["Position"] == "Teller"].to_dict(orient="records")
            else:
                flash("CSV file missing required columns.", "danger")
                tellers = []
        else:
            flash("CSV file is empty or not found.", "warning")
            tellers = []

    except Exception as e:
        flash(f"Error reading CSV: {e}", "danger")
        tellers = []

    return render_template("employee/admin_dashboard.html", tellers=tellers)

# Create Teller Route
@employee_bp.route("/create-teller", methods=["POST"])
def create_teller_route():
    data = request.get_json()
    first = data.get("firstName", "").strip()
    last = data.get("lastName", "").strip()

    if first and last:
        create_teller(first, last)
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Missing first or last name"), 400

@employee_bp.route("/edit-teller", methods=["POST"])
def edit_teller():
    data = request.get_json()
    employee_id = int(data.get("employeeID", 0))
    new_username = data.get("newUsername", "").strip()

    if not new_username:
        return jsonify(success=False, message="Missing username"), 400

    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/employees.csv"))
    try:
        df = pd.read_csv(csv_path)
        df.loc[df["EmployeeID"] == employee_id, "Username"] = new_username
        df.to_csv(csv_path, index=False)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/delete-teller", methods=["POST"])
def delete_teller():
    data = request.get_json()
    employee_id = int(data.get("employeeID", 0))

    try:
        result = delete_customer_logic("Teller", employee_id, is_admin=True)
        if result["status"] == "success":
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=result["message"]), 400
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/teller-dashboard")
def teller_dashboard():
    customer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/customers.csv"))
    try:
        df = pd.read_csv(customer_path)
        customers = df.to_dict(orient="records")
    except Exception as e:
        customers = []
        flash(f"Error loading customers: {e}", "danger")

    return render_template("employee/teller_dashboard.html", customers=customers)

@employee_bp.route("/edit-username", methods=["POST"])
def edit_username():
    data = request.get_json()
    customer_id = data.get("customerId")
    new_username = data.get("newUsername")

    if not customer_id or not new_username:
        return jsonify(success=False, message="Missing fields"), 400

    try:
        modify_username(customer_id, {"Username": new_username})
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/delete-customer", methods=["POST"])
def delete_customer():
    data = request.get_json()
    customer_id = data.get("customerId")

    if not customer_id:
        return jsonify(success=False, message="Customer ID required"), 400

    try:
        result = delete_customer_logic("Customer", customer_id, is_admin=True)
        if result["status"] == "success":
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=result["message"]), 400
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/deposit", methods=["POST"])
def record_deposit():
    data = request.get_json()
    account_id = data.get("accountId")
    amount = float(data.get("amount"))

    try:
        make_deposit(account_id, amount)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/withdraw", methods=["POST"])
def record_withdrawal():
    data = request.get_json()
    account_id = data.get("accountId")
    amount = float(data.get("amount"))

    try:
        withdraw_money(account_id, amount)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/transfer", methods=["POST"])
def record_transfer():
    data = request.get_json()
    from_account = data.get("fromAccount")
    to_account = data.get("toAccount")
    amount = float(data.get("amount"))

    try:
        transfer_funds(from_account, to_account, amount)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

@employee_bp.route("/teller-login", methods=["GET", "POST"])
def teller_login():
    if request.method == "POST":
        username = request.form.get("username")
        employee_id = request.form.get("employeeId")

        teller_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/employees.csv"))
        df = pd.read_csv(teller_path)

        match = df[(df["Username"] == username) & (df["EmployeeID"].astype(str) == str(employee_id)) & (df["Position"] == "Teller")]

        if not match.empty:
            return redirect(url_for("employee.teller_dashboard"))
        else:
            flash("Invalid Teller credentials", "danger")

    return render_template("auth/teller_login.html")
