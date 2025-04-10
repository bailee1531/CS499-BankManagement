import pandas as pd
import logging
from decimal import Decimal
from flask import Blueprint, render_template, Response, redirect, url_for, jsonify, request, session
from datetime import datetime, timedelta, date
from app.blueprints.sharedUtilities import (
    get_csv_path, get_logged_in_customer,
    get_customer_accounts, 
    login_required, flash_error, flash_success
)
from scripts.archive import archive, viewArchivedBills, viewArchivedLoans
from scripts.makeDeposit import deposit
from scripts.withdrawMoney import withdraw
from scripts.fundTransfer import transferFunds
from scripts.billPayment import scheduleBillPayment
from scripts.transactionLog import generate_transaction_ID

from .forms import (
    DepositForm, WithdrawForm, choose_account, TransferForm, BillPaymentForm, SettingsForm
)

logger = logging.getLogger(__name__)

# Create a Blueprint for the customer-related routes
customer_bp = Blueprint('customer', __name__, template_folder='templates')

# =============================================================================
# Helper Functions
# =============================================================================
def build_account_choices(accounts_df: pd.DataFrame) -> list:
    return [(int(row["AccountID"]), f'{row["AccountType"]} - ${row["CurrBal"]:.2f}')
            for _, row in accounts_df.iterrows()]

def load_account_by_id(account_id: int) -> pd.Series:
    accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
    account_row = accounts_df[accounts_df["AccountID"] == account_id]
    if account_row.empty:
        raise ValueError("Account not found.")
    return account_row.iloc[0]

def get_bill_for_account(customer_id: int, account_id: int) -> pd.Series:
    bills_df = pd.read_csv(get_csv_path("bills.csv"))
    filtered_bills = bills_df[
        (bills_df['PaymentAccID'] == account_id) &
        (bills_df['CustomerID'] == customer_id)
    ]
    if filtered_bills.empty:
        return pd.Series()
    return filtered_bills.loc[filtered_bills['Amount'].idxmin()]

def read_dataframes():
    try:
        bills_df = pd.read_csv(get_csv_path("bills.csv"))
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
        logs_df = pd.read_csv(get_csv_path("logs.csv"))
        return bills_df, accounts_df, logs_df
    except Exception as e:
        logger.error("Error reading data files.", exc_info=True)
        raise

def update_account_balance(accounts_df, account_id, new_balance):
    acc_index = accounts_df[accounts_df["AccountID"] == account_id].index
    if acc_index.empty:
        raise ValueError("Payment account not found.")
    accounts_df.at[acc_index[0], 'CurrBal'] = new_balance
    accounts_df.to_csv(get_csv_path("accounts.csv"), index=False)

def get_account_by_id(account_id: int) -> tuple:
    """
    Retrieves the account row and accounts DataFrame for the given account_id
    for the logged in customer.

    Returns:
        Tuple (account_row (Series), accounts_df (DataFrame), customer_id (int))
    Raises:
        ValueError: If the account is not found.
    """
    customer_id = get_logged_in_customer()
    accounts_df = get_customer_accounts(customer_id)
    account_rows = accounts_df[accounts_df["AccountID"] == account_id]
    if account_rows.empty:
        raise ValueError("Account not found.")
    return account_rows.iloc[0], accounts_df, customer_id

def calculate_min_payment(balance: Decimal) -> Decimal:
    """
    Calculates the minimum payment for a credit card account.
    """
    if balance >= Decimal("100.00"):
        return Decimal("100.00")
    elif balance > Decimal("0.00"):
        return balance
    else:
        return Decimal("0.00")
    
def load_csv(filename: str) -> pd.DataFrame:
    """
    Loads a CSV file from the configured CSV path.
    """
    path = get_csv_path(filename)
    return pd.read_csv(path)

@customer_bp.route('/terms')
def terms_of_service() -> Response:
    """
    Render the Terms of Service page for customers.
    """
    return render_template("customer/terms.html")

@customer_bp.route('/Dashboard')
@login_required("customer_id")
def customer_dashboard() -> Response:
    """
    Render the user's dashboard displaying their accounts.
    """
    customer_id: int = get_logged_in_customer()  # Get the logged-in customer's ID
    
    try:
        # Retrieve customer accounts data
        customer_accounts_df = get_customer_accounts(customer_id)
        accounts_list = []
        for _, row in customer_accounts_df.iterrows():
            accounts_list.append({
                "account_id": row["AccountID"],
                "account_type": row["AccountType"],
                "curr_bal": row["CurrBal"]
            })
    except Exception as e:
        flash_error("Error retrieving account information.")
        accounts_list = []  # Set an empty list for accounts on error

    # Retrieve the customer's archived mortgage loans using the archive module
    try:
        archived_loans = viewArchivedLoans(customer_id)
    except Exception as e:
        archived_loans = [{"status": "error", "message": "Error retrieving archived loans."}]
    
    # Render the customer dashboard template with accounts and archived loans
    return render_template(
        "customer/customer_dashboard.html",
        accounts=accounts_list,
        archived_loans=archived_loans
    )

@customer_bp.route('/account-overview/<int:account_id>')
@login_required("customer_id")
def account_overview(account_id: int) -> Response:
    """
    Display detailed information for a specific account.
    """
    try:
        # Use helper function to load account data
        account = load_account_by_id(account_id)
        account["AccountID"] = int(account["AccountID"])
        account_type = account.get("AccountType", "").strip()

        # Prepare extra info dictionary
        extra_info = {}

        # Only extract APR if account is Savings or Money Market
        if account_type in ["Savings", "Money Market"]:
            apr = account.get("APR", None)
            if pd.notna(apr):
                extra_info["apr"] = float(apr)

    except Exception as e:
        flash_error(f"Error retrieving account details: {e}")
        return redirect(url_for("customer.customer_dashboard"))

    return render_template(
        "customer/account_overview.html",
        account=account,
        extra_info=extra_info
    )


#============================================================================
# Settings Route
# =============================================================================

@customer_bp.route('/settings', methods=['GET', 'POST'])
@login_required("customer_id")
def settings() -> Response:
    """
    Render and process the user settings form.
    """
    form = SettingsForm()
    username = session.get("customer")
    if not username:
        flash_error("You must be logged in to access settings.")
        return redirect(url_for('auth.customer_login'))

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
            per_df.at[idx, 'Username'] = newUser
            per_df.to_csv(get_csv_path("persons.csv"), index=False)
    
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
                logger.debug(f"ECC import failed: {ve}")
                return redirect(url_for('customer.settings'))
            except Exception as e:
                flash_error("Error accessing private key file.")
                logger.debug(f"Unexpected error: {e}", exc_info=True)
                return redirect(url_for('customer.settings'))

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
                result = modifyInfo.modify_info(customer_id, {key: value})
                messages.append(result["message"])
            flash_success(" | ".join(messages))
        else:
            flash_error("No changes were made.")

        return redirect(url_for('customer.settings'))

    form.first_name.data = per_df.at[idx, 'FirstName']
    form.last_name.data = per_df.at[idx, 'LastName']
    form.phone.data = per_df.at[idx, 'PhoneNum']
    form.email.data = per_df.at[idx, 'Email']
    form.address.data = per_df.at[idx, 'Address']
    form.username.data = username

    return render_template("customer/settings.html", form=form, title="User Settings")



@customer_bp.route('/credit-mortgage/<int:account_id>')
@login_required("customer_id")
def credit_mortgage_page(account_id: int) -> Response:
    """
    Display detailed information for Credit Card or Mortgage accounts.
    """
    try:
        # Use helper function to load account data
        try:
            account = load_account_by_id(account_id)
        except ValueError:
            flash_error("That mortgage account has been closed or archived.")
            return redirect(url_for("customer.customer_dashboard"))

        account["AccountID"] = int(account["AccountID"])
        account_type = str(account["AccountType"]).strip().lower()
        if account_type not in ["credit card", "mortgage loan"]:
            flash_error("This page is only for Credit Card or Mortgage accounts.")
            return redirect(url_for("customer.customer_dashboard"))

        # Set up extra_info
        extra_info = {}

        # Add APR if available (for both mortgage and credit card)
        apr = account.get("APR")
        if pd.notna(apr):
            extra_info["apr"] = float(apr)

        bills_df = pd.read_csv(get_csv_path("bills.csv"))
        bill_row = bills_df[bills_df["PaymentAccID"] == account_id]
        if not bill_row.empty:
            bill_data = bill_row.iloc[0]
            extra_info["bill_id"] = int(bill_data["BillID"])
            extra_info["due_date"] = str(bill_data["DueDate"])
            extra_info["minimum_due"] = float(bill_data["Amount"])



    except Exception as e:
        logger.error(f"Error in credit_mortgage_page: {e}", exc_info=True)
        flash_error("Error retrieving account details.")
        return redirect(url_for("customer.customer_dashboard"))

    return render_template(
        "customer/credit_mortgage_page.html",
        account=account,
        extra_info=extra_info
    )


# =============================================================================
# Deposit Route
# =============================================================================

@customer_bp.route('/deposit/<int:account_id>', methods=['GET', 'POST'])
@login_required("customer_id")
def deposit_money(account_id: int) -> Response:
    """
    Process a deposit for a selected account.
    """
    customer_id = get_logged_in_customer()
    form = DepositForm()

    try:
        accounts_df = get_customer_accounts(customer_id)
        form.account_id.choices = build_account_choices(accounts_df)

        # Preselect the account in the form if possible
        if request.method == 'GET':
            if account_id and any(account_id == choice[0] for choice in form.account_id.choices):
                form.account_id.data = account_id

    except Exception as e:
        flash_error("Error retrieving account information.")
        logger.error(f"Error setting up deposit form: {e}")

    if form.validate_on_submit():
        result = deposit(int(form.account_id.data), form.amount.data)
        if result["status"] != "success":
            flash_error(result["message"])
        else:
            return redirect(url_for("customer.account_overview", account_id=form.account_id.data))

    return render_template("customer/deposit.html", form=form, account_id=account_id)


# =============================================================================
# Withdraw Route
# =============================================================================

@customer_bp.route('/withdraw/<int:account_id>', methods=['GET', 'POST'])
@login_required("customer_id")
def withdraw_money(account_id=None) -> Response:
    customer_id = get_logged_in_customer()
    form = WithdrawForm()

    try:
        accounts_df = get_customer_accounts(customer_id)
        form.account_id.choices = build_account_choices(accounts_df)
        if request.method == "GET" and account_id is not None:
            form.account_id.data = account_id  # Preselect account in form
    except Exception as e:
        flash_error("Error retrieving account information.")
        logger.error(f"Error setting up withdrawal form: {e}")

    if form.validate_on_submit():
        result = withdraw(int(form.account_id.data), form.amount.data)
        if result["status"] != "success":
            flash_error(result["message"])
        else:
            return redirect(url_for("customer.account_overview", account_id=form.account_id.data))

    return render_template("customer/withdraw.html", form=form, account_id=account_id)

# =============================================================================
# Transfer Route
# =============================================================================

@customer_bp.route('/account/transfer', methods=['GET', 'POST'])
@login_required('customer_id')
def transfer_funds() -> Response:
    """
    Process a fund transfer between two accounts.
    """
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
            flash_error(f"Error retrieving account details. {str(e)}")
            logger.error(f"Error processing transfer: {e}", exc_info=True)
    return render_template("customer/transfer_funds.html", form=form)

# =============================================================================
# Bill Payment Route
# =============================================================================

@customer_bp.route('/pay-bill/<int:account_id>', methods=['GET', 'POST'])
@login_required("customer_id")
def pay_bill(account_id: int):
    """
    Handles bill payment for a specified account. 
    Allows customers to pay credit card or mortgage loan bills using their checking or savings accounts.
    """
    customer_id = get_logged_in_customer()

    # Load the target bill account
    try:
        try:
            account = load_account_by_id(account_id)
        except ValueError:
            flash_error("That mortgage account has been closed or archived.")
            return redirect(url_for("customer.customer_dashboard"))

        account["AccountID"] = int(account["AccountID"])
        account_type = account["AccountType"]
    except Exception:
        flash_error("Error retrieving account details.")
        return redirect(url_for("customer.customer_dashboard"))

    # Retrieve the bill associated with this account
    bill = get_bill_for_account(customer_id, account_id)

    # Default bill values for display if no bill is due
    if bill.empty or Decimal(str(bill["Amount"])).quantize(Decimal("0.00")) == Decimal("0.00"):
        min_amount = None
        due_date_obj = None
        due_date_str = None
        payee_name_value = "Evergreen Bank"
        payee_address_value = "Somewhere In The World"
        bill_id_value = ""
    else:
        # Bill exists, extract necessary fields
        min_amount = float(bill["Amount"])
        due_date_str = bill["DueDate"]
        try:
            due_date_obj = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except Exception:
            due_date_obj = None
        payee_name_value = bill["PayeeName"]
        payee_address_value = bill["PayeeAddress"]
        bill_id_value = bill["BillID"]

    # Get all eligible payment accounts (checking/savings)
    accounts_df = get_customer_accounts(customer_id)
    form = BillPaymentForm()
    form.paymentAccID.choices = [
        (int(row["AccountID"]), f'{row["AccountType"]} - ${row["CurrBal"]:.2f}')
        for _, row in accounts_df.iterrows()
        if row["AccountType"] in ["Checking", "Savings"]
    ]

    # Populate form fields on GET request
    if request.method == "GET":
        form.bill_id.data = bill_id_value
        form.paymentAccID.data = account_id
        if account_type in ['Credit Card', 'Mortgage Loan']:
            form.payee_name.data = payee_name_value
            form.payee_address.data = payee_address_value
            if due_date_obj:
                form.due_date.data = due_date_obj

    # Handle POST request (form submission)
    if form.validate_on_submit():
        # Extract form data
        bill_id = form.bill_id.data
        amount = Decimal(form.amount.data).quantize(Decimal('0.00'))
        due_date_input = form.due_date.data
        due_date_str_input = due_date_input.strftime("%Y-%m-%d") if due_date_input else ""
        payee_name_input = form.payee_name.data
        payee_address_input = form.payee_address.data
        payment_account_id = int(form.paymentAccID.data)

        # Load data files
        try:
            bills_df, accounts_df, logs_df = read_dataframes()
        except Exception:
            flash_error("Unable to read data files.")
            return redirect(url_for("customer.customer_dashboard"))

        # Existing bill: validate and process payment
        if bill_id and int(bill_id) in bills_df['BillID'].values:
            try:
                bill_record = bills_df[bills_df['BillID'] == int(bill_id)].iloc[0]
                full_amount_due = Decimal(bill_record["Amount"]).quantize(Decimal('0.00'))

                # Validate amount based on account type
                if account_type in ["Credit Card", "Mortgage Loan"]:
                    if amount < full_amount_due:
                        flash_error(f"You must pay at least the due amount of ${full_amount_due:.2f}.")
                        return render_template("customer/bill_pay.html", form=form, account_id=account_id, min_amount=full_amount_due, due_date=due_date_str_input, account_type=account_type)
                else:
                    if amount != full_amount_due:
                        flash_error(f"You must pay the exact bill amount of ${full_amount_due:.2f}.")
                        return render_template("customer/bill_pay.html", form=form, account_id=account_id, min_amount=full_amount_due, due_date=due_date_str_input, account_type=account_type)

                # Prevent using the same account for payment
                if payment_account_id == account_id:
                    flash_error("Payment account cannot be the same as the bill account.")
                    return redirect(url_for("customer.credit_mortgage_page" if account_type in ["Credit Card", "Mortgage Loan"] else "customer.account_overview", account_id=account_id))

                # Load account balances
                acc_row = load_account_by_id(account_id)
                curr_bal = Decimal(acc_row["CurrBal"]).quantize(Decimal('0.00'))
                payment_acc_row = load_account_by_id(payment_account_id)
                payment_curr_bal = Decimal(payment_acc_row["CurrBal"]).quantize(Decimal("0.00"))

                # Ensure sufficient funds
                if payment_curr_bal < amount:
                    flash_error("Insufficient funds in payment account.")
                    return redirect(url_for("customer.credit_mortgage_page" if account_type in ["Credit Card", "Mortgage Loan"] else "customer.account_overview", account_id=account_id))

                # Prevent overpaying credit card balance
                if account_type == "Credit Card":
                    new_balance = curr_bal - amount
                    if new_balance < Decimal("0.00"):
                        flash_error("Payment exceeds credit card balance.")
                        return redirect(url_for("customer.credit_mortgage_page", account_id=account_id))
                else:
                    new_balance = curr_bal - amount

                # Update balances
                new_payment_balance = payment_curr_bal - amount
                update_account_balance(accounts_df, account_id, new_balance)
                update_account_balance(accounts_df, payment_account_id, new_payment_balance)
                accounts_df.to_csv(get_csv_path("accounts.csv"), index=False)

                # Log the transaction
                transaction_id = generate_transaction_ID(logs_df)
                logs_df.loc[len(logs_df)] = {
                    'AccountID': payment_account_id,
                    'CustomerID': customer_id,
                    'TransactionType': f"Bill Payment to {payee_name_input}",
                    'Amount': amount,
                    'TransactionID': transaction_id
                }

                # Archive the bill
                archive_result = archive("bill", int(bill_id))
                if archive_result["status"] == "success":
                    flash_success("Bill paid and archived successfully.")
                else:
                    flash_error(f"Payment processed but archiving failed: {archive_result['message']}")

                # Mortgage loan special handling
                print("Bill exists — proceeding with payment.")
                print("No bill found — scheduling new bill.")
                print(f"Archive result: {archive_result}")

                loan_archived = False
                if account_type == "Mortgage Loan":
                    updated_accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
                    loan_row = updated_accounts_df[
                        (updated_accounts_df['AccountID'] == account_id) &
                        (updated_accounts_df['AccountType'] == 'Mortgage Loan')
                    ]
                    if not loan_row.empty and Decimal(str(loan_row.iloc[0]['CurrBal'])) == Decimal("0.00"):
                        loan_archive_result = archive("loan", account_id)
                        if loan_archive_result["status"] == "success":
                            flash_success("Mortgage loan fully paid and archived.")
                            loan_archived = True
                        else:
                            flash_error(f"Loan archiving failed: {loan_archive_result['message']}")

                # Schedule next bill if applicable
                if not loan_archived:
                    updated_accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
                    new_acc_row = updated_accounts_df[updated_accounts_df["AccountID"] == account_id].iloc[0]
                    new_balance = Decimal(str(new_acc_row["CurrBal"])).quantize(Decimal("0.00"))
                    if new_balance > Decimal("0.00"):
                        next_due_date = due_date_input + timedelta(days=30)
                        schedule_result = scheduleBillPayment(
                            customerID=customer_id,
                            payeeName=payee_name_input,
                            payeeAddress=payee_address_input,
                            amount=new_balance,
                            dueDate=next_due_date.strftime("%Y-%m-%d"),
                            paymentAccID=account_id
                        )
                        if schedule_result["status"] == "success":
                            flash_success("Next bill scheduled.")
                        else:
                            flash_error(schedule_result["message"])

                return redirect(url_for("credit_mortgage_page" if account_type in ["Credit Card", "Mortgage Loan"] else "customer.account_overview", account_id=account_id))


            except Exception as e:
                logger.error(f"Early bill payment failed: {e}", exc_info=True)
                flash_error("An error occurred while processing early payment.")

        # No current bill — schedule a new one
        else:
            result = scheduleBillPayment(
                customerID=customer_id,
                payeeName=payee_name_input,
                payeeAddress=payee_address_input,
                amount=amount,
                dueDate=due_date_str_input,
                paymentAccID=account_id
            )
            if result["status"] == "success":
                flash_success(result["message"])
                return redirect(url_for("customer.credit_mortgage_page" if account_type in ["Credit Card", "Mortgage Loan"] else "customer.account_overview", account_id=account_id))
            else:
                flash_error(result["message"])

    # Render the bill payment page
    return render_template(
        "customer/bill_pay.html",
        form=form,
        account_id=account_id,
        min_amount=min_amount,
        due_date=due_date_str,
        account_type=account_type
    )



# =============================================================================
# API Endpoints
# =============================================================================

@customer_bp.route('/api/transactions/<int:account_id>')
def get_transactions(account_id):
    """
    Retrieve transactions for a specific account, split into 'current' and 'past'
    based on whether they occurred within the last 30 days.
    """
    try:
        # Load the transactions from CSV
        path = get_csv_path('transactions.csv')
        df = pd.read_csv(path)

        # Filter transactions for the provided account ID
        df = df[df['AccountID'] == account_id]

        # Convert the TransDate column to datetime format
        df['TransDate'] = pd.to_datetime(df['TransDate'], errors='coerce')

        # Define time cutoff for current vs. past transactions
        today = datetime.today()
        cutoff = today - timedelta(days=30)

        # Separate into current and past based on transaction date
        current_df = df[df['TransDate'] >= cutoff]
        past_df = df[df['TransDate'] < cutoff]

        # Helper function to format DataFrame rows for JSON
        def format_transactions(df):
            return [
                {
                    "TransDate": row["TransDate"].strftime("%Y-%m-%d"),
                    "description": row["TransType"].capitalize(),
                    "amount": float(row["Amount"])
                }
                for _, row in df.iterrows()
            ]

        # Return JSON with both current and past transactions
        return jsonify({
            "current_transactions": format_transactions(current_df),
            "past_transactions": format_transactions(past_df)
        })

    except Exception as e:
        # Return error as JSON if something goes wrong
        return jsonify({"error": str(e)})


@customer_bp.route('/archived-bills/<int:account_id>')
@login_required("customer_id")
def get_archived_bills(account_id: int):
    """
    Retrieve archived credit card bills for the currently logged-in customer,
    filtered by the given account ID.
    """
    try:
        # Get customer ID from session
        customer_id = get_logged_in_customer()

        # Load all archived bills for the customer
        archived_bills = viewArchivedBills(customer_id)

        # Filter bills to only those related to the provided account ID
        filtered_bills = [
            bill for bill in archived_bills 
            if bill.get("PaymentAccID") == account_id
        ]

        # Return filtered bills in JSON
        return jsonify({"archived_bills": filtered_bills})

    except Exception as e:
        # Log and return error if something goes wrong
        logger.debug(f"Error in get_archived_bills for account {account_id}: {e}")
        return jsonify({"error": "Failed to load archived bills."}), 500


@customer_bp.route('/api/account-balance/<int:account_id>')
@login_required("customer_id")
def get_account_balance(account_id: int):
    """
    Retrieve the current balance and type of the account.
    If it's a credit card, also calculate and update the minimum payment due.
    """
    try:
        # Retrieve account information
        account, _, customer_id = get_account_by_id(account_id)
        account_type = account["AccountType"].upper()
        balance = float(account["CurrBal"])

        bill_updated = False  # Tracks whether a bill was updated
        amount_due = None     # Stores calculated minimum payment if applicable

        # Special handling for credit card accounts
        if account_type == "CREDIT CARD":
            # Calculate minimum payment due
            amount_due = calculate_min_payment(Decimal(str(balance)))

            try:
                # Load all bills
                bills_df = load_csv("bills.csv")
                bills_df["PaymentAccID"] = bills_df["PaymentAccID"].astype(int)

                # Filter bills for this specific credit card account
                matching = bills_df[bills_df["PaymentAccID"] == account_id]

                if not matching.empty:
                    # Find the earliest (upcoming) bill by due date
                    matching["DueDate"] = pd.to_datetime(matching["DueDate"], errors="coerce")
                    earliest_index = matching.sort_values("DueDate").index[0]

                    # Update the 'Amount' field with the new minimum payment
                    old_amount = bills_df.at[earliest_index, "Amount"]
                    bills_df.at[earliest_index, "Amount"] = float(amount_due)

                    # Save the updated bills back to CSV
                    bills_df.to_csv(get_csv_path("bills.csv"), index=False)

                    logger.debug(f"Updated Amount from {old_amount} to {amount_due} for PaymentAccID {account_id}")
                    bill_updated = True
                else:
                    logger.debug(f"No matching credit card bill to update for PaymentAccID {account_id}")
            except Exception as bill_err:
                logger.warning(f"Failed to update bills.csv: {bill_err}")

        # Return account information and bill status
        return jsonify({
            "balance": balance,
            "account_type": account_type,
            "bill_updated": bill_updated,
            "amount_due": float(amount_due) if amount_due is not None else None
        })

    except Exception as e:
        # Log and return error if account info retrieval fails
        logger.error(f"Error retrieving balance for account {account_id}: {e}")
        return jsonify({"error": f"Failed to get balance: {str(e)}"}), 500
