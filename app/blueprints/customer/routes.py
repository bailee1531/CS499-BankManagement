import pandas as pd
import os
from decimal import Decimal
from datetime import datetime
from Crypto.PublicKey import ECC
from flask import (
    Blueprint, render_template, redirect, url_for, jsonify, request, Response, session, current_app
)

from scripts.makeDeposit import deposit
from scripts.withdrawMoney import withdraw
from scripts.fundTransfer import transferFunds
from scripts.customer import modifyInfo
from .forms import WithdrawForm, TransferForm, DepositForm, choose_account, SettingsForm
from app.blueprints.sharedUtilities import (
    get_csv_path, get_logged_in_customer, get_customer_accounts,
    login_required, flash_error, flash_success
)

customer_bp = Blueprint('customer', __name__, template_folder='templates')

# ---------------------------
# Helper Functions
# ---------------------------

def build_account_choices(accounts_df):
    return [
        (str(row["AccountID"]), f"{row['AccountType']} - Balance: ${row['CurrBal']:.2f}")
        for _, row in accounts_df.iterrows()
    ]


# ---------------------------
# Dashboard
# ---------------------------

@customer_bp.route('/Dashboard')
@login_required("customer_id")
def customer_dashboard() -> Response:
    customer_id = get_logged_in_customer()
    try:
        accounts_df = get_customer_accounts(customer_id)
        accounts_list = [
            {
                "account_id": row["AccountID"],
                "account_type": row["AccountType"].upper(),
                "curr_bal": row["CurrBal"]
            }
            for _, row in accounts_df.iterrows()
        ]
    except Exception as e:
        flash_error("Error retrieving account information.")
        accounts_list = []

    return render_template("customer/customer_dashboard.html", accounts=accounts_list)

# ---------------------------
#Settings
# ---------------------------
@customer_bp.route('/settings', methods=['GET', 'POST'])
@login_required("customer_id")
def settings():
    form = SettingsForm()
    username = session.get("customer")
    if not username:
        flash_error("You must be logged in to access settings.")
        return redirect(url_for('auth.customer_login'))

    # Load user data from CSVs
    cust_df = pd.read_csv(get_csv_path("customers.csv"))
    per_df = pd.read_csv(get_csv_path("persons.csv"))

    try:
        customer_id = cust_df.loc[cust_df['Username'] == username, 'CustomerID'].iloc[0]
    except IndexError:
        flash_error("User not found.")
        return redirect(url_for('auth.customer_login'))

    person_idx = per_df.index[per_df['ID'] == customer_id].tolist()
    if not person_idx:
        flash_error("Customer data not found.")
        return redirect(url_for('auth.customer_login'))

    idx = person_idx[0]

    if form.validate_on_submit():
        changes = {}
        newUser = form.username.data.strip()

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
            cust_df.loc[cust_df['CustomerID'] == customer_id, 'Username'] = newUser
            cust_df.to_csv(get_csv_path("customers.csv"), index=False)

            session['customer'] = newUser
            changes['Username'] = newUser
        if form.password.data.strip():
            if not form.current_password.data.strip():
                flash_error("Current password is required to update your password.")
                return redirect(url_for('customer.settings'))

            pem_path = os.path.abspath(os.path.join(current_app.root_path, "..", f"{customer_id}privatekey.pem"))
            try:
                with open(pem_path, 'rt') as f:
                    key_data = f.read()
                    key = ECC.import_key(key_data, form.current_password.data.strip())
            except ValueError as ve:
                flash_error("Current password is incorrect.")
                print(f"[DEBUG] ECC import failed: {ve}")
                return redirect(url_for('customer.settings'))
            except Exception as e:
                import traceback
                flash_error("Error accessing private key file.")
                print(f"[DEBUG] Unexpected error: {e}")
                traceback.print_exc()
                return redirect(url_for('customer.settings'))

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
            success = True
            for key, value in changes.items():
                result = modifyInfo.modify_info(customer_id, {key: value})
                messages.append(result["message"])
                if result["status"] != "success":
                    success = False
            flash_success(" | ".join(messages))
        else:
            flash_error("No changes were made.")

        return redirect(url_for('customer.settings'))

    # Pre-fill form values
    form.first_name.data = per_df.at[idx, 'FirstName']
    form.last_name.data = per_df.at[idx, 'LastName']
    form.phone.data = per_df.at[idx, 'PhoneNum']
    form.email.data = per_df.at[idx, 'Email']
    form.address.data = per_df.at[idx, 'Address']
    form.username.data = username

    return render_template("customer/settings.html", form=form, title="User Settings")



# ---------------------------
# Account Overview
# ---------------------------

@customer_bp.route('/account-overview/<int:account_id>')
@login_required("customer_id")
def account_overview(account_id: int) -> Response:
    try:
        customer_id = get_logged_in_customer()
        accounts_df = get_customer_accounts(customer_id)

        account_row = accounts_df[accounts_df["AccountID"] == account_id]
        if account_row.empty:
            flash_error("Account not found.")
            return redirect(url_for("customer.customer_dashboard"))

        account = account_row.iloc[0].to_dict()
        account["AccountID"] = account_row.iloc[0]["AccountID"]  # ✅ Add this line
        account["account_type"] = account.get("AccountType", "").upper()
        account["curr_bal"] = account.get("CurrBal", 0)

        accounts_list = accounts_df.to_dict("records")  # for use in `accounts|length`

        return render_template("customer/account_overview.html",
                               account=account,
                               accounts=accounts_list,
                               current_transactions=[],
                               past_transactions=[])

    except Exception as e:
        flash_error("Error retrieving account details.")
        return redirect(url_for("customer.customer_dashboard"))


# ---------------------------
# API: Transactions
# ---------------------------

@customer_bp.route('/api/transactions/<int:account_id>')
@login_required("customer_id")
def get_transactions(account_id: int):
    try:
        df = pd.read_csv(get_csv_path("transactions.csv"))
        df["AccountID"] = df["AccountID"].astype(int)
        df = df[df["AccountID"] == account_id]

        if df.empty:
            return jsonify({"current_transactions": [], "past_transactions": []})

        df["TransDate"] = pd.to_datetime(df["TransDate"], errors="coerce")
        df = df.sort_values("TransDate")
        today = datetime.now().replace(hour=0, minute=0)

        to_dict_list = lambda d: d.apply(lambda row: {
            "description": row["TransType"],
            "amount": row["Amount"],
            "TransDate": row["TransDate"].strftime("%Y-%m-%d") if pd.notnull(row["TransDate"]) else ""
        }, axis=1).tolist()

        return jsonify({
            "current_transactions": to_dict_list(df[df["TransDate"] > today]),
            "past_transactions": to_dict_list(df[df["TransDate"] <= today])
        })

    except Exception as e:
        return jsonify({"error": f"Error retrieving transactions: {str(e)}"}), 500

# ---------------------------
# Deposit
# ---------------------------

@customer_bp.route('/deposit', methods=['GET', 'POST'])
@login_required("customer_id")
def deposit_money():
    customer_id = get_logged_in_customer()
    form = DepositForm()

    try:
        accounts_df = get_customer_accounts(customer_id)
        form.account_id.choices = build_account_choices(accounts_df)
    except Exception:
        flash_error("Error retrieving account information.")

    if form.validate_on_submit():
        result = deposit(int(form.account_id.data), form.amount.data)
        if result["status"] != "success":
            flash_error(result["message"])
        else:
            return redirect(url_for("customer.account_overview", account_id=form.account_id.data))

    return render_template("customer/deposit.html", form=form)

# ---------------------------
# Withdraw
# ---------------------------

@customer_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required("customer_id")
def withdraw_money():
    customer_id = get_logged_in_customer()
    form = WithdrawForm()

    try:
        accounts_df = get_customer_accounts(customer_id)
        form.account_id.choices = build_account_choices(accounts_df)
    except Exception:
        flash_error("Error retrieving account information.")

    if form.validate_on_submit():
        result = withdraw(int(form.account_id.data), form.amount.data)
        if result["status"] != "success":
            flash_error(result["message"])
        else:
            return redirect(url_for("customer.account_overview", account_id=form.account_id.data))

    return render_template("customer/withdraw.html", form=form)

# ---------------------------
# Transfer
# ---------------------------

@customer_bp.route('/account/transfer', methods=['GET', 'POST'])
@login_required('customer_id')
def transfer_funds() -> Response:
    """
    Display two dropdowns. One for the source account and one for the destination account.
    Retrieves and displays the ID and type for each checking, savings, and money market account.
    Returns:
    --------
    Response: Rendered template with account details or redirection on error.
    """
    form = TransferForm()
    form = choose_account()
    amount = form.amount.data

    if form.validate_on_submit():
        try:
            src_account = int(form.src_account.data)
            dest_account = int(form.dest_account.data)
            transfer_result = transferFunds(src_account, dest_account, amount)
            if transfer_result.get("status") == "error":
                flash_error(transfer_result.get("message", "Transfer Failed"))
                return redirect(url_for("customer.customer_dashboard"))
            flash_success(transfer_result.get("message", "Transfer Complete"))
            return redirect(url_for("customer.customer_dashboard"))
        except Exception as e:
            # If there is an error retrieving account details, show an error message and redirect
            flash_error(f"Error retrieving account details. {str(e)}")
    return render_template("customer/transfer_funds.html", form=form)