from flask import Blueprint, Response, request, session, current_app, render_template, redirect, url_for, flash, jsonify
from app.blueprints.sharedUtilities import (
    get_csv_path, login_required, flash_error, flash_success, get_account_transactions, get_customer_accounts
)
from app.blueprints.auth.forms import LoginForm
from .forms import AdminSettingsForm
import pandas as pd
import hashlib
import json
import csv
import os

# Blueprint for admin routes
admin_bp = Blueprint('admin', __name__, template_folder='templates')

# ------------------------
# Get Identicon for Avatar
# ------------------------
def get_unique_identicon_url(username):
    # Hash the username
    unique_hash = hashlib.md5(username.encode('utf-8')).hexdigest()
    
    # Generate the Gravatar URL using the hashed value
    return f"https://www.gravatar.com/avatar/{unique_hash}?s=50&d=initials&name={username}"

# -----------
# Admin Login
# -----------
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()

    if request.method == "POST":
        username = request.form.get("username")
        username = username.lower()

        df = pd.read_csv(get_csv_path("employees.csv"))

        match = df[(df["Username"] == username) & (df["Position"] == "Admin")]

        if not match.empty:
            session['admin'] = username
            session['role'] = 'admin'
            return redirect(url_for("employee.admin_dashboard"))
        else:
            flash("Invalid credentials. Try again.", "danger")

    return render_template("auth/login.html", form=form,
                       title="Evergreen Bank - Admin Login",
                       header_text="Admin Login",
                       login_instructions="Enter your administrator credentials to log in.",
                       form_action=url_for('admin.admin_login'),
                       forgot_password_url="#",
                       show_signup_button=False)

# ---------------
# Admin Dashboard
# ---------------
@admin_bp.route("/dashboard")
@login_required("admin")
def admin_dashboard():
    employeePath = get_csv_path("employees.csv")
    customers_df = pd.read_csv(get_csv_path("customers.csv"))
    persons_df = pd.read_csv(get_csv_path("persons.csv"))
    accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
    log_df = pd.read_csv(get_csv_path("logs.csv"))

    # Convert IDs to int for consistency
    customers_df["CustomerID"] = customers_df["CustomerID"].astype(int)
    persons_df["ID"] = persons_df["ID"].astype(int)
    accounts_df["CustomerID"] = accounts_df["CustomerID"].astype(int)
    accounts_df["AccountID"] = accounts_df["AccountID"].astype(int)
    log_df["LogID"] = log_df["LogID"].astype(int)
    log_df["UserID"] = log_df["UserID"].astype(int)

    try:
        # Merge customers + persons to get full profile
        merged_df = pd.merge(customers_df, persons_df, left_on="CustomerID", right_on="ID", how="left")

        # Get just one account per customer
        account_map = accounts_df.groupby("CustomerID")["AccountID"].first().reset_index()
        merged_df = pd.merge(merged_df, account_map, left_on="CustomerID", right_on="CustomerID", how="left")

        # Rename AccountID column for clarity in the template
        merged_df = merged_df.rename(columns={"AccountID": "AccountNumber"})

        customers = merged_df.to_dict(orient="records")
        for customer in customers:
            customer["avatar_url"] = get_unique_identicon_url(customer["Username"])

        logs = log_df.to_dict(orient="records")
        if os.path.exists(employeePath) and os.path.getsize(employeePath) > 0:
            df = pd.read_csv(employeePath)

            # Check if required columns exist
            if all(col in df.columns for col in ["Username", "EmployeeID", "Position"]):
                tellers = df[df["Position"] == "Teller"].to_dict(orient="records")
                for teller in tellers:
                    teller["avatar_url"] = get_unique_identicon_url(teller["Username"])
            else:
                flash("CSV file missing required columns.", "danger")
                tellers = []
        else:
            flash("CSV file is empty or not found.", "warning")
            tellers = []

    except Exception as e:
        flash(f"Error reading CSV: {e}", "danger")
        tellers = []
        customers = []
        logs = []
        return jsonify(success=False, message=str(e)), 500

    return render_template("admin/admin_dashboard.html", tellers=tellers, customers=customers, logs=logs)

# --------------
# Admin Settings
# --------------
@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required('admin')
def admin_settings():
    from Crypto.PublicKey import ECC
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
        return redirect(url_for('admin.admin_login'))

    idx = person_idx[0]

    if form.validate_on_submit():
        password_changed = False

        if form.password.data.strip():

            if not form.current_password.data.strip():
                flash_error("Current password is required to update your password.")
                return redirect(url_for('admin.admin_settings'))

            pem_path = os.path.abspath(os.path.join(current_app.root_path, "..", f"{admin_id}privatekey.pem"))
            try:
                with open(pem_path, 'rt') as f:
                    key_data = f.read()
                    key = ECC.import_key(key_data, form.current_password.data.strip())
            except ValueError as ve:
                flash_error("Current password is incorrect.")
                print(f"ECC import failed: {ve}")
                return redirect(url_for('admin.admin_settings'))
            except Exception as e:
                import traceback
                flash_error("Error accessing private key file.")
                print(f"Unexpected error: {e}")
                traceback.print_exc()
                return redirect(url_for('admin.admin_settings'))

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

        return redirect(url_for('admin.admin_settings'))
    
    form.email.data = per_df.at[idx, 'Email']

    return render_template("admin/admin_settings.html", form=form)


### Teller Management ###

# ---------------------------------------
# Check If a Teller Has Set Up Login Info
# ---------------------------------------
@admin_bp.route("/check-employee", methods=["POST"])
def check_employee():
    data = request.get_json()
    employee_id = data.get("employeeID")

    if employee_id is None:
        return jsonify({'exists': bool(exists)})

    try:
        df = pd.read_csv(get_csv_path("persons.csv"))
        exists = (df["ID"] == int(employee_id)).any()
        return jsonify({'exists': bool(exists)})
    except FileNotFoundError:
        return jsonify({'exists': bool(exists)})
    except Exception as e:
        print(f"Error checking employee ID: {e}")
        return jsonify({'exists': bool(exists)})

# ---------------
# Create a Teller
# ---------------
@admin_bp.route("/create-teller", methods=["POST"])
@login_required("admin")
def create_teller_route():
    from scripts.createTeller import create_teller
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
        print(f"Failed to create teller: {e}")
        return jsonify(success=False, message=str(e)), 500

# -------------
# Edit a Teller
# -------------
@admin_bp.route("/edit-teller", methods=["POST"])
@login_required("admin")
def edit_teller():
    data = request.get_json()
    employee_id = int(data.get("employeeID", 0))
    new_username = data.get("newUsername", "").strip()

    if not new_username:
        return jsonify(success=False, message="Missing username"), 400
    
    csv_path = get_csv_path("employees.csv")

    try:
        df = pd.read_csv(csv_path)
        df.loc[df["EmployeeID"] == employee_id, "Username"] = new_username
        df.to_csv(csv_path, index=False)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500

# ---------------
# Delete a Teller
# ---------------
@admin_bp.route("/delete-teller", methods=["POST"])
@login_required("admin")
def delete_teller():
    from scripts.customer.deleteUser import delete_user_button_pressed
    data = request.get_json()
    employee_id = int(data.get("employeeID", 0))

    try:
        result = delete_user_button_pressed("Teller", employee_id, is_admin=True)
        if result["status"] == "success":
            return jsonify(success=True)
        else:
            return jsonify(success=False, message=result["message"]), 400
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


### Customer Management ###

# -----------------------------------
# Display All Accounts a Customer Has
# -----------------------------------
@admin_bp.route("/get-accounts/<int:customer_id>")
@login_required("admin")
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

# ----------------------------------------------------
# Check Account Balance of All Accounts a Customer Has
# ----------------------------------------------------
@admin_bp.route("/check-accounts/<int:customer_id>", methods=["GET"])
@login_required("admin")
def check_customer_accounts(customer_id):
    try:
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
        bills_df = pd.read_csv(get_csv_path("bills.csv"))

        nonzero_balance = accounts_df[
            (accounts_df['CustomerID'] == customer_id) & 
            (accounts_df['CurrBal'].astype(float) > 0.00)
        ]

        unpaid_bills = bills_df[
            (bills_df['CustomerID'] == customer_id) & 
            (bills_df['Amount'].astype(float) > 0.00)
        ]

        has_balance = not nonzero_balance.empty
        has_unpaid = not unpaid_bills.empty

        return jsonify(success=True, hasOpenAccountsOrBills=has_balance or has_unpaid)

    except Exception as e:
        print(f"Account status check failed: {e}")
        return jsonify(success=False, message=f"Error checking account status: {str(e)}"), 500

# -----------------------------
# Display All Customer Accounts
# -----------------------------
@admin_bp.route("/customer/<int:customer_id>/accounts", methods=["GET"])
def get_customer_accounts_route(customer_id):
    """
    Returns all accounts associated with a specific customer.
    Replaces NaN/NaT values in the DataFrame with None before sending the response.
    """
    try:
        df = get_customer_accounts(customer_id)
        df = df.replace({pd.NA: None, pd.NaT: None, float('nan'): None})  # Clean NaN values

        response_data = {
            "success": True,
            "accounts": df.to_dict(orient="records")
        }
        return Response(json.dumps(response_data), mimetype='application/json')
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    
# -----------------------------
# Display Customer Transactions
# -----------------------------
@admin_bp.route("/transactions-json/admin/<customer_id>")
@login_required("admin")
def transactions_for_customer(customer_id):
    try:
        acc_df = pd.read_csv(get_csv_path("accounts.csv"))
        tx_df = pd.read_csv(get_csv_path("transactions.csv"))

        acc_ids = acc_df[acc_df["CustomerID"] == int(customer_id)]["AccountID"].tolist()
        filtered_tx = tx_df[tx_df["AccountID"].isin(acc_ids)]

        return jsonify(filtered_tx.to_dict(orient="records"))

    except Exception as e:
        print(f"Failed to load transactions: {e}")
        return jsonify([])
    
# ----------------------------
# Display Account Transactions
# ----------------------------
@admin_bp.route("/account/<int:account_id>/transactions", methods=["GET"])
def get_account_transactions_route(account_id):
    """
    Returns a sorted list of transactions for a specific account, 
    ordered by transaction date (most recent first).
    """
    try:
        df = get_account_transactions(account_id)
        df_sorted = df.sort_values(by="TransDate", ascending=False)

        return jsonify(success=True, transactions=df_sorted.to_dict(orient="records"))
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500