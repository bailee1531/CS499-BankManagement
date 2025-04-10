import os
import pandas as pd
import csv
from Crypto.PublicKey import ECC
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, Response
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
from scripts.customer.webLogin import login_page_button_pressed
from .forms import TellerSettingsForm, AdminSettingsForm, DepositForm

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

@employee_bp.route("/check-employee", methods=["POST"])
def check_employee():
    data = request.get_json()
    employee_id = data.get("employeeID")
    personsPath = get_csv_path("persons.csv")

    if employee_id is None:
        return jsonify({'exists': bool(exists)})

    try:
        df = pd.read_csv(personsPath)
        exists = (df["ID"] == int(employee_id)).any()
        return jsonify({'exists': bool(exists)})
    except FileNotFoundError:
        return jsonify({'exists': bool(exists)})
    except Exception as e:
        print(f"Error checking employee ID: {e}")
        return jsonify({'exists': bool(exists)})

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
    try:
        customers_df = pd.read_csv(get_csv_path("customers.csv"))
        persons_df = pd.read_csv(get_csv_path("persons.csv"))
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))

        # Convert IDs to int for consistency
        customers_df["CustomerID"] = customers_df["CustomerID"].astype(int)
        persons_df["ID"] = persons_df["ID"].astype(int)
        accounts_df["CustomerID"] = accounts_df["CustomerID"].astype(int)

        # Merge customers + persons to get full profile
        merged_df = pd.merge(customers_df, persons_df, left_on="CustomerID", right_on="ID", how="left")

        # Get just one account per customer
        account_map = accounts_df.groupby("CustomerID")["AccountID"].first().reset_index()
        merged_df = pd.merge(merged_df, account_map, left_on="CustomerID", right_on="CustomerID", how="left")

        # Rename AccountID column for clarity in the template
        merged_df = merged_df.rename(columns={"AccountID": "AccountNumber"})

        customers = merged_df.to_dict(orient="records")

    except Exception as e:
        customers = []
        flash(f"Error loading customers: {e}", "danger")

    # Deposit form setup
    form = DepositForm()
    try:
        form.account_id.choices = [
            (str(acc["AccountID"]), f"{acc['AccountType']} - {acc['AccountID']}")
            for _, acc in accounts_df.iterrows()
        ]
    except Exception as e:
        form.account_id.choices = []
        flash(f"Error loading account options: {e}", "danger")

    return render_template("employee/teller_dashboard.html", customers=customers, form=form)

@employee_bp.route("/edit-username", methods=["POST"])
def edit_username():
    data = request.get_json()
    customer_id = data.get("customerId")
    new_username = data.get("newUsername")

    if not customer_id or not new_username:
        return jsonify(success=False, message="Missing fields"), 400

    try:
        customer_id = int(customer_id)
        customers_path = get_csv_path("customers.csv")
        df = pd.read_csv(customers_path)

        if customer_id not in df['CustomerID'].values:
            return jsonify(success=False, message="Customer ID not found"), 404

        df.loc[df['CustomerID'] == customer_id, 'Username'] = new_username
        df.to_csv(customers_path, index=False)

        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ---------------------------
#Reset Customer Password
# ---------------------------
@employee_bp.route("/reset-password", methods=["POST"])
def reset_customer_password_route():
    data = request.get_json()
    customer_id = data.get("customerID")
    old_password = data.get("oldPassword")
    new_password = data.get("newPassword")

    if not customer_id or not old_password or not new_password:
        return jsonify(success=False, message="Customer ID, old password, and new password required."), 400

    pem_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../", f"{customer_id}privatekey.pem"))

    try:
        with open(pem_path, 'rt') as f:
            key_data = f.read()
            key = ECC.import_key(key_data, old_password)

        encrypted = key.export_key(
            format='PEM',
            passphrase=new_password,
            use_pkcs8=True,
            protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
            compress=True,
            prot_params={'iteration_count': 210000}
        )

        with open(pem_path, 'wt') as f:
            f.write(encrypted)

        return jsonify(success=True)
    except ValueError:
        return jsonify(success=False, message="Old password is incorrect."), 400
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    
@employee_bp.route("/get-accounts/<int:customer_id>")
def get_accounts(customer_id):
    accounts = []
    try:
        accounts_path = get_csv_path("accounts.csv")
        with open(accounts_path, newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row["CustomerID"]) == customer_id:
                    accounts.append({
                        "AccountID": row["AccountID"],
                        "AccountType": row["AccountType"],
                        "CurrBal": row["CurrBal"],
                        "DateOpened": row["DateOpened"],
                        "CreditLimit": row.get("CreditLimit", ""),
                        "APR": row.get("APR", "")
                    })
        return jsonify(success=True, accounts=accounts)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@employee_bp.route("/check-accounts/<int:customer_id>", methods=["GET"])
def check_customer_accounts(customer_id):
    try:
        accounts_path = get_csv_path("accounts.csv")
        bills_path = get_csv_path("bills.csv")

        accounts_df = pd.read_csv(accounts_path)
        bills_df = pd.read_csv(bills_path)

        has_accounts = not accounts_df[accounts_df['CustomerID'] == customer_id].empty
        has_bills = not bills_df[bills_df['CustomerID'] == customer_id].empty

        return jsonify(success=True, hasOpenAccountsOrBills=has_accounts or has_bills)
    except Exception as e:
        return jsonify(success=False, message=f"Error checking account status: {str(e)}"), 500
    

@employee_bp.route("/open-account", methods=["POST"])
def open_account_route():
    data = request.get_json()

    try:
        # Unpack fields
        first = data.get("firstName").strip()
        last = data.get("lastName").strip()
        username = data.get("username").strip()
        password = data.get("password").strip()
        ssn = data.get("ssn").strip()
        email = data.get("email").strip()
        phone = data.get("phone").strip()
        q1 = data.get("securityAnswer1").strip()
        q2 = data.get("securityAnswer2").strip()

        # Call existing function to handle CSV + key logic
        result = login_page_button_pressed(
            1, "Customer", username, password,
            first, last, "N/A", email, phone, ssn, q1, q2
        )

        if result["status"] != "success":
            return jsonify(success=False, message=result["message"])

        # Get new customer ID
        cust_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/customers.csv"))
        cust_df = pd.read_csv(cust_path)
        customer_row = cust_df[cust_df["Username"] == username]
        if customer_row.empty:
            return jsonify(success=False, message="Customer ID not found after creation.")
        customer_id = int(customer_row["CustomerID"].iloc[0])

        # Add account
        acc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/accounts.csv"))
        acc_df = pd.read_csv(acc_path) if os.path.exists(acc_path) else pd.DataFrame(columns=[
            "AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"
        ])
        import random
        from datetime import date
        from decimal import Decimal

        acc_id = random.randint(1000, 9999)
        while acc_id in acc_df["AccountID"].values:
            acc_id = random.randint(1000, 9999)

        acc_df.loc[len(acc_df)] = {
            "AccountID": acc_id,
            "CustomerID": customer_id,
            "AccountType": data.get("accountType", "Checking"),
            "CurrBal": Decimal("0.00"),
            "DateOpened": date.today(),
            "CreditLimit": None,
            "APR": None
        }
        acc_df.to_csv(acc_path, index=False)

        return jsonify(success=True, message="Customer account successfully created.")

    except Exception as e:
        print(f"[ERROR] Account creation failed: {e}")
        return jsonify(success=False, message="Account creation failed.")


@employee_bp.route("/delete-account", methods=["POST"])
def delete_account():
    data = request.get_json()
    account_id = int(data.get("accountID"))

    # Load accounts CSV
    acc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../csvFiles/accounts.csv"))
    acc_df = pd.read_csv(acc_path)

    # Find the account
    account_row = acc_df[acc_df["AccountID"] == account_id]
    if account_row.empty:
        return jsonify(success=False, message="Account not found.")

    balance = float(account_row["CurrBal"].iloc[0])
    if balance != 0.00:
        return jsonify(success=False, message="Account must have a balance of $0.00 to be deleted.")

    # Delete the account
    acc_df = acc_df[acc_df["AccountID"] != account_id]
    acc_df.to_csv(acc_path, index=False)

    return jsonify(success=True, message="Account successfully deleted.")


@employee_bp.route("/deposit", methods=["GET", "POST"])
def record_deposit() -> Response:
    data = request.get_json()
    account_id = data.get("accountId")
    form = DepositForm()

    if form.validate_on_submit():
        result = make_deposit(account_id, form.amount.data)
        if result["status"] != "success":
            flash_error(result["message"])
        else:
            return redirect(url_for("employee.teller_dashboard"))
        
    return render_template("employee/teller_dashboard.html", form=form)

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
        password_changed = False

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
            password_changed = True

        messages = []

        if username_changed:
            messages.append(f"Username successfully updated to {newUser}.")
        if password_changed:
            messages.append("Password successfully updated.")

        for key, value in changes.items():
            result = modifyInfo.modify_info(teller_id, {key: value})
            messages.append(result["message"])

        if messages:
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
        password_changed = False

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
            password_changed = True

        messages = []
        if password_changed:
            messages.append(f"Password successfully updated.")

        if messages:
            flash_success(" | ".join(messages))
        else:
            flash_error("No changes were made.")

        return redirect(url_for('employee.admin_settings'))
    
    form.email.data = per_df.at[idx, 'Email']

    return render_template("employee/admin_settings.html", form=form)