import os
import pandas as pd
from Crypto.PublicKey import ECC
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from app.blueprints.auth.forms import LoginForm
from app.blueprints.sharedUtilities import (
    get_csv_path, login_required, flash_error, flash_success
)
from scripts.createTeller import create_teller
from scripts.makeDeposit import deposit as make_deposit
from scripts.customer.modifyInfo import modify_info as modify_username
from scripts.customer import modifyInfo
from scripts.customer.deleteUser import delete_user_button_pressed as delete_customer_logic
from scripts.withdrawMoney import withdraw as withdraw_money
from scripts.fundTransfer import transferFunds as transfer_funds
from .form import TellerSettingsForm, AdminSettingsForm

# Blueprint for employee routes
employee_bp = Blueprint('employee', __name__, template_folder='templates')

# Admin Login Route
@employee_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()

    if request.method == "POST":
        username = request.form.get("username")
        employee_id = request.form.get("employeeId")

        teller_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/employees.csv"))
        df = pd.read_csv(teller_path)

        match = df[(df["Username"] == username) & (df["Position"] == "Admin")]

        if not match.empty:
            session['admin'] = username
            session['employee_id'] = 0
            session['role'] = 'admin'
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

    if not first or not last:
        return jsonify(success=False, message="Missing first or last name"), 400

    try:
        create_teller(first, last)
        return jsonify(success=True)
    except Exception as e:
        # Log the error and send back the message
        print(f"[ERROR] Failed to create teller: {e}")
        return jsonify(success=False, message=str(e)), 500


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
            session['teller'] = username
            session['employee_id'] = int(match.iloc[0]["EmployeeID"])
            session['role'] = 'teller'
            return redirect(url_for("employee.teller_dashboard"))
        else:
            flash("Invalid Teller credentials", "danger")

    return render_template("auth/teller_login.html")

# ---------------------------
#Teller Settings
# ---------------------------
@employee_bp.route("/teller/settings", methods=["GET", "POST"])
@login_required('teller')
def teller_settings():
    form = TellerSettingsForm()
    username = session.get("teller")
    if not username:
        flash_error("You must be logged in to access settings.")
        return redirect(url_for('auth.teller_login'))

    # Load user data from CSVs
    cust_df = pd.read_csv(get_csv_path("employees.csv"))
    per_df = pd.read_csv(get_csv_path("persons.csv"))

    try:
        teller_id = cust_df.loc[cust_df['Username'] == username, 'EmployeeID'].iloc[0]
    except IndexError:
        flash_error("User not found.")
        return redirect(url_for('auth.teller_login'))

    person_idx = per_df.index[per_df['ID'] == teller_id].tolist()
    if not person_idx:
        flash_error("Teller data not found.")
        return redirect(url_for('auth.teller_login'))

    idx = person_idx[0]

    if form.validate_on_submit():
        changes = {}
        newUser = form.username.data.strip()
        username_changed = False

        if form.first_name.data.strip() != str(per_df.at[idx, 'FirstName']).strip():
            changes['FirstName'] = form.first_name.data.strip()
        if form.last_name.data.strip() != str(per_df.at[idx, 'LastName']).strip():
            changes['LastName'] = form.last_name.data.strip()
        if form.phone.data.strip() != str(per_df.at[idx, 'PhoneNum']).strip():
            changes['PhoneNum'] = form.phone.data.strip()
        if form.email.data.strip() != str(per_df.at[idx, 'Email']).strip():
            changes['Email'] = form.email.data.strip()
        if form.address.data.strip() != str(per_df.at[idx, 'Address']).strip():
            changes['Address'] = form.address.data.strip()
        if newUser != username:
            cust_df.loc[cust_df['EmployeeID'] == teller_id, 'Username'] = newUser
            cust_df.to_csv(get_csv_path("employees.csv"), index=False)

            session['teller'] = newUser
            username_changed = True
        if form.password.data.strip():
            if not form.current_password.data.strip():
                flash_error("Current password is required to update your password.")
                return redirect(url_for('employee.teller_settings'))

            pem_path = os.path.abspath(os.path.join(current_app.root_path, "..", f"{teller_id}privatekey.pem"))
            try:
                with open(pem_path, 'rt') as f:
                    key_data = f.read()
                    key = ECC.import_key(key_data, form.current_password.data.strip())
            except ValueError as ve:
                flash_error("Current password is incorrect.")
                print(f"[DEBUG] ECC import failed: {ve}")
                return redirect(url_for('employee.teller_settings'))
            except Exception as e:
                import traceback
                flash_error("Error accessing private key file.")
                print(f"[DEBUG] Unexpected error: {e}")
                traceback.print_exc()
                return redirect(url_for('employee.teller_settings'))

            # Re-encrypt with new password
            encrypted = key.export_key(
                format='PEM',
                passphrase=form.password.data.strip(),
                use_pkcs8=True,
                protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
                compress=True,
                prot_params={'iteration_count': 210000}
            )
            with open(pem_path, 'wt') as f:
                f.write(encrypted)
            changes['Password'] = '***'

        if changes or username_changed:
            messages = []
            
            if username_changed:
                messages.append(f"Username successfully updated to {newUser}.")

            for key, value in changes.items():
                result = modifyInfo.modify_info(teller_id, {key: value})
                messages.append(result["message"])

            flash_success(" | ".join(messages))
        else:
            flash_error("No changes were made.")

        return redirect(url_for('employee.teller_settings'))

    # Pre-fill form values
    form.first_name.data = per_df.at[idx, 'FirstName']
    form.last_name.data = per_df.at[idx, 'LastName']
    form.phone.data = per_df.at[idx, 'PhoneNum']
    form.email.data = per_df.at[idx, 'Email']
    form.address.data = per_df.at[idx, 'Address']
    form.username.data = username

    return render_template("employee/teller_settings.html", form=form)

# ---------------------------
#Admin Settings
# ---------------------------
@employee_bp.route("/admin/settings", methods=["GET", "POST"])
@login_required('admin')
def admin_settings():
    form = AdminSettingsForm()
    username = session.get("admin")
    if not username:
        flash_error("You must be logged in to access settings.")
        return redirect(url_for('auth.admin_login'))

    # Load user data from CSVs
    cust_df = pd.read_csv(get_csv_path("employees.csv"))
    per_df = pd.read_csv(get_csv_path("persons.csv"))

    try:
        admin_id = cust_df.loc[cust_df['Username'] == username, 'EmployeeID'].iloc[0]
    except IndexError:
        flash_error("User not found.")
        return redirect(url_for('auth.admin_login'))

    person_idx = per_df.index[per_df['ID'] == admin_id].tolist()
    if not person_idx:
        flash_error("Admin data not found.")
        return redirect(url_for('employee.admin_login'))

    idx = person_idx[0]

    if form.validate_on_submit():
        changes = {}

        if form.password.data.strip():
            if not form.current_password.data.strip():
                flash_error("Current password is required to update your password.")
                return redirect(url_for('employee.admin_settings'))

            pem_path = os.path.abspath(os.path.join(current_app.root_path, "..", f"{admin_id}privatekey.pem"))
            try:
                with open(pem_path, 'rt') as f:
                    key_data = f.read()
                    key = ECC.import_key(key_data, form.current_password.data.strip())
            except ValueError as ve:
                flash_error("Current password is incorrect.")
                print(f"[DEBUG] ECC import failed: {ve}")
                return redirect(url_for('employee.admin_settings'))
            except Exception as e:
                import traceback
                flash_error("Error accessing private key file.")
                print(f"[DEBUG] Unexpected error: {e}")
                traceback.print_exc()
                return redirect(url_for('employee.admin_settings'))

            # Re-encrypt with new password
            encrypted = key.export_key(
                format='PEM',
                passphrase=form.password.data.strip(),
                use_pkcs8=True,
                protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
                compress=True,
                prot_params={'iteration_count': 210000}
            )
            with open(pem_path, 'wt') as f:
                f.write(encrypted)
            changes['Password'] = '***'

        if changes:
            messages = []
            
            for key, value in changes.items():
                result = modifyInfo.modify_info(admin_id, {key: value})
                messages.append(result["message"])

            flash_success(" | ".join(messages))
        else:
            flash_error("No changes were made.")

        return redirect(url_for('employee.admin_settings'))
    
    form.email.data = per_df.at[idx, 'Email']

    return render_template("employee/admin_settings.html", form=form)