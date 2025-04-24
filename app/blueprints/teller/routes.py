from flask import Blueprint, Response, request, session, current_app, render_template, redirect, url_for, flash, jsonify
from app.blueprints.sharedUtilities import (
    get_csv_path, login_required, flash_error, flash_success, get_account_transactions, get_customer_accounts
)
from .forms import TellerSettingsForm
from Crypto.PublicKey import ECC
from decimal import Decimal
import pandas as pd
import hashlib
import json
import csv
import os

# Blueprint for teller routes
teller_bp = Blueprint('teller', __name__, template_folder='templates')

# ------------------------
# Get Identicon for Avatar
# ------------------------
def get_unique_identicon_url(username):
    # Hash the username
    unique_hash = hashlib.md5(username.encode('utf-8')).hexdigest()
    
    # Generate the Gravatar URL using the hashed value
    return f"https://www.gravatar.com/avatar/{unique_hash}?s=50&d=initials&name={username}"

# ------------
# Teller Login
# ------------
@teller_bp.route("/login", methods=["GET", "POST"])
def teller_login():
    if request.method == "POST":
        username = request.form.get("username")
        employee_id = request.form.get("employeeId")
        username = username.lower()

        df = pd.read_csv(get_csv_path("employees.csv"))

        match = df[(df["Username"] == username) & (df["EmployeeID"].astype(str) == str(employee_id)) & (df["Position"] == "Teller")]

        if not match.empty:
            session['teller'] = username
            session['employee_id'] = int(match.iloc[0]["EmployeeID"])
            session['role'] = 'teller'
            return redirect(url_for("teller.teller_dashboard"))
        else:
            flash_error("Invalid Teller credentials", "danger")

    return render_template("auth/teller_login.html")

# ----------------
# Teller Dashboard
# ----------------
@teller_bp.route("/dashboard", methods=["GET", "POST"])
@login_required("teller")
def teller_dashboard():
    try:
        customers_df = pd.read_csv(get_csv_path("customers.csv"))
        persons_df = pd.read_csv(get_csv_path("persons.csv"))
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))

        # Convert IDs to int for consistency
        customers_df["CustomerID"] = customers_df["CustomerID"].astype(int)
        persons_df["ID"] = persons_df["ID"].astype(int)
        accounts_df["CustomerID"] = accounts_df["CustomerID"].astype(int)
        accounts_df["AccountID"] = accounts_df["AccountID"].astype(int) # Ensure AccountID is int

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

    except Exception as e:
        customers = []
        return jsonify(success=False, message=str(e)), 500
    return render_template("teller/teller_dashboard.html", customers=customers)

# ---------------
# Teller Settings
# ---------------
@teller_bp.route("/settings", methods=["GET", "POST"])
@login_required('teller')
def teller_settings():
    from scripts.customer import modifyInfo
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
                return redirect(url_for('teller.teller_settings'))

            pem_path = os.path.abspath(os.path.join(current_app.root_path, "..", f"{teller_id}privatekey.pem"))
            try:
                with open(pem_path, 'rt') as f:
                    key_data = f.read()
                    key = ECC.import_key(key_data, form.current_password.data.strip())
            except ValueError as ve:
                flash_error("Current password is incorrect.")
                print(f"ECC import failed: {ve}")
                return redirect(url_for('teller.teller_settings'))
            except Exception as e:
                import traceback
                flash_error("Error accessing private key file.")
                print(f"Unexpected error: {e}")
                traceback.print_exc()
                return redirect(url_for('teller.teller_settings'))

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


        return redirect(url_for('teller.teller_settings'))

    # Pre-fill form values
    form.first_name.data = per_df.at[idx, 'FirstName']
    form.last_name.data = per_df.at[idx, 'LastName']
    form.phone.data = per_df.at[idx, 'PhoneNum']
    form.email.data = per_df.at[idx, 'Email']
    form.address.data = per_df.at[idx, 'Address']
    form.username.data = username

    return render_template("teller/teller_settings.html", form=form)


### Customer Management ###

# ----------------------
# Edit Customer Username
# ----------------------
@teller_bp.route("/edit-username", methods=["POST"])
@login_required("teller")
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

# -----------------------
# Reset Customer Password
# -----------------------
@teller_bp.route("/reset-password", methods=["POST"])
@login_required("teller")
def reset_customer_password():
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
    
# -----------------------------------
# Display All Accounts a Customer Has
# -----------------------------------
@teller_bp.route("/get-accounts/<int:customer_id>")
@login_required("teller")
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
@teller_bp.route("/check-accounts/<int:customer_id>", methods=["GET"])
@login_required("teller")
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
@teller_bp.route("/customer/<int:customer_id>/accounts", methods=["GET"])
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
@teller_bp.route("/transactions-json/teller/<customer_id>")
@login_required("teller")
def get_customer_transactions(customer_id):
    try:
        trans_df = pd.read_csv(get_csv_path("transactions.csv"))
        acc_df = pd.read_csv(get_csv_path("accounts.csv"))

        customer_accounts = acc_df[acc_df["CustomerID"] == int(customer_id)]["AccountID"].tolist()
        filtered = trans_df[trans_df["AccountID"].isin(customer_accounts)]

        return jsonify(filtered.to_dict(orient="records"))

    except Exception as e:
        print(f"Failed to load transactions (teller): {e}")
        return jsonify([])

# ----------------------------
# Display Account Transactions
# ----------------------------
@teller_bp.route("/account/<int:account_id>/transactions", methods=["GET"])
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

# ------------------------------------
# Create a User Account for a Customer
# ------------------------------------
@teller_bp.route("/open-account", methods=["POST"])
@login_required("teller")
def open_account():
    from scripts.customer.webLogin import login_page_button_pressed
    data = request.get_json()
    try:
        # Unpack fields
        first = data.get("firstName").strip()
        last = data.get("lastName").strip()
        username = data.get("username").strip()
        password = data.get("password").strip()
        address = data.get("address").strip()
        ssn = data.get("ssn").strip()
        email = data.get("email").strip()
        phone = data.get("phone").strip()
        q1 = data.get("securityAnswer1").strip()
        q2 = data.get("securityAnswer2").strip()

        # Call existing function to handle CSV + key logic
        result = login_page_button_pressed(
            1, "Customer", username, password,
            first, last, address, email, phone, ssn, q1, q2
        )

        if result["status"] != "success":
            return jsonify(success=False, message=result["message"])

        # Get new customer ID
        cust_df = pd.read_csv(get_csv_path("customers.csv"))
        customer_row = cust_df[cust_df["Username"] == username]
        if customer_row.empty:
            return jsonify(success=False, message="Customer ID not found after creation.")
        customer_id = int(customer_row["CustomerID"].iloc[0])

        # Add account
        acc_path = get_csv_path("accounts.csv")
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
        print(f"Account creation failed: {e}")
        return jsonify(success=False, message="Account creation failed.")

# ----------------------------------
# Open a Bank Account for a Customer
# ----------------------------------
@teller_bp.route("/create-account", methods=["POST"])
@login_required("teller")
def create_account_existing_customer():
    from scripts.customer.openAcc import open_account as open_standard_account
    from scripts.createCreditCard import openCreditCardAccount
    from scripts.createLoan import createMortgageLoanAccount

    data = request.get_json()

    try:
        customer_id = int(data.get("customerID"))
        account_type = data.get("accountType", "").strip()
        deposit = Decimal(str(data.get("depositAmount", "0.00")))

        if account_type in ["Checking", "Savings", "Money Market"]:
            result = open_standard_account(customer_id, account_type, deposit)

        elif account_type == "Travel Visa":
            result = openCreditCardAccount(customer_id)

        elif account_type == "Home Mortgage Loan":
            loan_amt = Decimal(str(data.get("loanAmount", "0.00")))
            loan_term = int(data.get("loanTerm", 0))
            result = createMortgageLoanAccount(customer_id, loan_amt, loan_term)

        else:
            return jsonify({"status": "error", "message": f"Unsupported account type: {account_type}"}), 400

        if result["status"] == "success":
            return jsonify(success=True, message=result["message"])
        else:
            return jsonify(success=False, message=result["message"])

    except Exception as e:
        print(f"Creating account failed: {e}")
        return jsonify(success=False, message="Account creation failed.")

# --------------------------------
# Delete a Customer's Bank Account
# --------------------------------
@teller_bp.route("/delete-account", methods=["POST"])
@login_required("teller")
def delete_account():
    from scripts.deleteAccount import deleteAcc
    data = request.get_json()
    cust_id = data.get("customerID")
    acc_id = data.get("accountID")

    if not cust_id or not acc_id:
        return jsonify({"status": "error", "message": "Missing customer or account ID."})

    username = session.get("teller")
    if not username:
        return jsonify({"status": "error", "message": "No authenticated user found."})

    # Load employees.csv to get performed_by_id
    employees_df = pd.read_csv(get_csv_path("employees.csv"))
    user_row = employees_df[employees_df["Username"] == username]

    if user_row.empty:
        return jsonify({"status": "error", "message": f"User '{username}' not found in employees.csv"})

    performed_by_id = int(user_row["EmployeeID"].iloc[0])

    result = deleteAcc(int(cust_id), int(acc_id), performed_by_id)
    return jsonify(result)

# --------------------------------
# Delete a Customer's User Account
# --------------------------------
@teller_bp.route("/delete-customer", methods=["POST"])
@login_required("teller")
def delete_customer():
    from scripts.customer.deleteUser import delete_user_button_pressed
    data = request.get_json()
    customer_id = int(data.get("customerID"))

    try:
        accounts_path = get_csv_path("accounts.csv")
        bills_path = get_csv_path("bills.csv")

        acc_df = pd.read_csv(accounts_path)
        bills_df = pd.read_csv(bills_path)

        # Delete only $0.00 accounts
        acc_df = acc_df[~((acc_df["CustomerID"] == customer_id) & (acc_df["CurrBal"].astype(float) == 0.00))]

        # Delete only $0.00 bills
        bills_df = bills_df[~((bills_df["CustomerID"] == customer_id) & (bills_df["Amount"].astype(float) == 0.00))]

        # Save updated files
        acc_df.to_csv(accounts_path, index=False)
        bills_df.to_csv(bills_path, index=False)

        # Now attempt delete
        result = delete_user_button_pressed("Customer", customer_id, is_admin=True)

        if result["status"] == "success":
            return jsonify(success=True, message=result["message"])
        else:
            return jsonify(success=False, message=result["message"]), 400
    except Exception as e:
        return jsonify(success=False, message=f"Error: {e}"), 500


### Transactions ###

# ----------------------
# Deposit for a Customer
# ----------------------
@teller_bp.route("/deposit", methods=["POST"])
@login_required("teller")
def deposit():
    from scripts.makeDeposit import deposit
    data = request.get_json()

    try:
        accPath = get_csv_path("accounts.csv")
        df = pd.read_csv(accPath)
        df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        
        accountID = data.get("accountId").strip()
        amount = data.get("amount").strip()
        accountID = int(accountID)

        accIndex = df.loc[df['AccountID'] == accountID].index[0]

        bal = Decimal(df.at[accIndex, 'CurrBal'])

        if not accountID or not amount:
            return jsonify(success=False, message="Account ID and deposit amount are required.")

        try:
            amount = Decimal(amount)
            if amount <= Decimal("0.00"):
                return jsonify(success=False, message="Deposit amount must be positive.")
            result = deposit(accountID, amount)
        except ValueError:
            return jsonify(success=False, message="Invalid account ID or deposit amount format.")

        if result["status"] == "success":
            bal += Decimal(amount)
            df.at[accIndex, 'CurrBal'] = Decimal(bal)
            df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            df.to_csv(accPath, index=False)
            return jsonify(success=True, message="Deposit completed.")
        else:
            return jsonify(success=False, message=result["message"])
    except Exception as e:
        print(f"Deposit failed: {e}")
        return jsonify(success=False, message="Deposit failed.")

# -----------------------
# Withdraw for a Customer
# -----------------------
@teller_bp.route("/withdraw", methods=["POST"])
@login_required("teller")
def withdraw():
    from scripts.withdrawMoney import withdraw
    data = request.get_json()

    try:
        accPath = get_csv_path("accounts.csv")
        df = pd.read_csv(accPath)
        df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        
        accountID = data.get("accountId").strip()
        amount = data.get("amount").strip()
        accountID = int(accountID)

        accIndex = df.loc[df['AccountID'] == accountID].index[0]

        bal = Decimal(df.at[accIndex, 'CurrBal'])

        if not accountID or not amount:
            return jsonify(success=False, message="Account ID and withdrawal amount are required.")

        try:
            accountID = int(accountID)
            amount = Decimal(amount)
            if amount <= Decimal("0.00"):
                return jsonify(success=False, message="Withdrawal amount must be positive.")
            result = withdraw(accountID, amount)
        except ValueError:
            return jsonify(success=False, message="Invalid account ID or withdrawal amount format.")

        if result["status"] == "success":
            bal -= Decimal(amount)
            df.at[accIndex, 'CurrBal'] = Decimal(bal)
            df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            df.to_csv(accPath, index=False)
            return jsonify(success=True, message="Withdrawal completed.")
        else:
            return jsonify(success=False, message=result["message"])
    except Exception as e:
        print(f"Withdrawal failed: {e}")
        return jsonify(success=False, message="Withdrawal failed.")

# -----------------------
# Transfer for a Customer
# -----------------------
@teller_bp.route("/transfer", methods=["POST"])
@login_required("teller")
def transfer():
    from scripts.fundTransfer import transferFunds
    data = request.get_json()

    try:
        accPath = get_csv_path("accounts.csv")
        df = pd.read_csv(accPath)
        df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        
        src_account = data.get("sourceAccountId").strip()
        dest_account = data.get("destinationAccountId").strip()
        amount = data.get("amount").strip()

        src_account = int(src_account)
        dest_account = int(dest_account)
        amount = Decimal(amount)

        src_index = df.loc[df['AccountID'] == src_account].index[0]
        dest_index = df.loc[df['AccountID'] == dest_account].index[0]

        srcBal = Decimal(df.at[src_index, 'CurrBal'])
        destBal = Decimal(df.at[dest_index, 'CurrBal'])

        if not src_account or not dest_account or not amount:
            return jsonify(success=False, message="Source Account ID, Destination Account ID, and transfer amount are required.")

        try:
            if amount <= Decimal("0.00"):
                return jsonify(success=False, message="Transfer amount must be positive.")
            if src_account == dest_account:
                return jsonify(success=False, message="Source and destination accounts cannot be the same.")
            result = transferFunds(src_account, dest_account, amount)
        except ValueError:
            return jsonify(success=False, message="Invalid account ID or transfer amount format.")

        if result["status"] == "success":
            srcBal -= Decimal(amount)
            destBal += Decimal(amount)
            df.at[src_index, 'CurrBal'] = Decimal(srcBal)
            df.at[dest_index, 'CurrBal'] = Decimal(destBal)
            df['CurrBal'] = df['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            df.to_csv(accPath, index=False)
            return jsonify(success=True, message="Transfer completed.")
        else:
            return jsonify(success=False, message=result["message"])
    except Exception as e:
        print(f"Transfer failed: {e}")
        return jsonify(success=False, message="Transfer failed.")