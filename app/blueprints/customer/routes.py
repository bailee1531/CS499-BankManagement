# Spring 2025 Authors: Braden Doty, Bailee Segars, Sierra Yerges
import pandas as pd
import os
import logging
from decimal import Decimal
from Crypto.PublicKey import ECC
from flask import Blueprint, render_template, Response, redirect, url_for, jsonify, request, session, current_app
from datetime import datetime, timedelta, date
from collections import Counter
from dateutil.relativedelta import relativedelta
from app.blueprints.sharedUtilities import (
    get_csv_path, get_logged_in_customer,
    get_customer_accounts, 
    login_required, flash_error, flash_success
)

from scripts.customer import modifyInfo
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
    accounts_df.at[acc_index[0], 'CurrBal'] = float(new_balance)  # Convert to float
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

def get_previous_bill_due_date(account_id: int) -> datetime.date:
    """
    Retrieves the most recent bill due date for a specific account from archivedBills.csv.
    This helps maintain consistent billing cycles regardless of payment date.
    
    Args:
        account_id: The ID of the account to find previous bills for
        
    Returns:
        datetime.date: The most recent bill due date or today's date if none found
    """
    try:
        # Get path to archived bills
        archived_bills_path = get_csv_path("archivedBills.csv")
        
        # Check if file exists
        if not os.path.exists(archived_bills_path):
            return datetime.now().date()
        
        # Load archived bills
        archived_bills_df = pd.read_csv(archived_bills_path)
        
        # Filter for the account
        matching_bills = archived_bills_df[archived_bills_df['PaymentAccID'] == account_id]
        
        if matching_bills.empty:
            return datetime.now().date()
        
        # Sort by due date (descending) to get most recent
        matching_bills['DueDate'] = pd.to_datetime(matching_bills['DueDate'], errors='coerce')
        matching_bills = matching_bills.sort_values('DueDate', ascending=False)
        
        # Get the most recent due date
        most_recent_due_date = matching_bills.iloc[0]['DueDate']
        
        if pd.isna(most_recent_due_date):
            return datetime.now().date()
        
        return most_recent_due_date.date()
    
    except Exception as e:
        logger.error(f"Error retrieving previous bill due date: {e}")
        # Fall back to current date if there's an error
        return datetime.now().date()

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
            extra_info["minimum_due"] = float(bill_data["MinPayment"])



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

        if request.method == 'POST':
            print("POST received")
            print(form.data)
            print(form.errors)

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
@login_required('customer')
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
    - For credit cards: Allows partial payment (if >= minimum payment)
    - For mortgages: Requires full payment of monthly amount
    - For recurring bills: Allows payment and maintains recurrence
    """
    customer_id = get_logged_in_customer()
    
    # Load account data
    try:
        account = load_account_by_id(account_id)
        account["AccountID"] = int(account["AccountID"])
        account_type = account["AccountType"]
    except ValueError:
        flash_error("That account has been closed or archived.")
        return redirect(url_for("customer.customer_dashboard"))
    except Exception:
        flash_error("Error retrieving account details.")
        return redirect(url_for("customer.customer_dashboard"))

    # Get bill information
    bill_data = get_bill_data(customer_id, account_id, account_type)
    
    # Set up the form with available payment accounts
    form = setup_bill_payment_form(customer_id, account_id, bill_data, account_type, request.method)
    
    # Process form submission
    if request.method == "POST" and form.validate_on_submit():
        return process_bill_payment(form, account_id, account_type, customer_id)
    elif request.method == "POST":
        # Show validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash_error(f"{form[field].label.text}: {error}")

    # Render the bill payment page
    return render_template(
        "customer/bill_pay.html",
        form=form,
        account_id=account_id,
        min_amount=bill_data.get('min_amount'),
        due_date=bill_data.get('due_date_str'),
        account_type=account_type,
        account=account
    )


def get_bill_data(customer_id: int, account_id: int, account_type: str) -> dict:
    """
    Retrieves bill data for an account and formats it for the bill payment form.
    
    Returns:
        dict: Bill data including minimum amount, due date, and payee information
    """
    bill = get_bill_for_account(customer_id, account_id)
    bill_data = {
        'min_amount': None,
        'due_date_obj': None,
        'due_date_str': None,
        'payee_name': "Evergreen Bank",
        'payee_address': "Somewhere In The World",
        'bill_id': ""
    }
    
    # For credit cards without a bill, set up default bill data
    if account_type == "Credit Card" and bill.empty:
        acc = load_account_by_id(account_id)
        curr_bal = Decimal(acc["CurrBal"]).quantize(Decimal("0.00"))
        # CurrBal is negative for credit cards with a balance to pay
        if curr_bal < Decimal("0.00"):  
            # Set minimum payment as 2% of balance or $25, whichever is greater
            # MinPayment is positive, so use abs() on the balance
            min_payment = max(abs(curr_bal) * Decimal("0.02"), Decimal("25.00")).quantize(Decimal("0.00"))
            bill_data['min_amount'] = float(min_payment)
            bill_data['due_date_str'] = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")
            bill_data['payee_name'] = "Evergreen Bank Credit Card"
            bill_data['payee_address'] = "Evergreen Bank Payments Dept"
    
    # Process bill data if a bill exists
    if not bill.empty:
        bill_data['bill_id'] = bill["BillID"]
        bill_data['payee_name'] = bill["PayeeName"]
        bill_data['payee_address'] = bill["PayeeAddress"]
        
        try:
            bill_data['due_date_str'] = bill["DueDate"]
            bill_data['due_date_obj'] = datetime.strptime(bill_data['due_date_str'], "%Y-%m-%d").date()
        except Exception:
            bill_data['due_date_obj'] = None

        if account_type in ['Credit Card', 'Mortgage Loan']:
            # MinPayment is stored as positive value
            bill_data['min_amount'] = float(Decimal(bill["MinPayment"]).quantize(Decimal("0.00")))
        else:
            # Amount is negative for bills, so use abs() to get the positive payment amount
            bill_data['min_amount'] = float(abs(Decimal(bill["Amount"])).quantize(Decimal("0.00")))
        
        # Check if bill is fully paid - Amount will be 0 when paid
        if Decimal(str(bill["Amount"])).quantize(Decimal("0.00")) == Decimal("0.00"):
            flash_success("Bill is fully paid. It will be archived upon processing.")
            
    return bill_data


def setup_bill_payment_form(customer_id: int, account_id: int, bill_data: dict, account_type: str, method: str) -> BillPaymentForm:
    """
    Sets up and populates the bill payment form.
    """
    # Get eligible payment accounts (checking/savings)
    accounts_df = get_customer_accounts(customer_id)
    form = BillPaymentForm()
    
    # Set payment account choices
    form.paymentAccID.choices = [
        (int(row["AccountID"]), f'{row["AccountType"]} - ${row["CurrBal"]:.2f}')
        for _, row in accounts_df.iterrows() if row["AccountType"] in ["Checking", "Savings"]
    ]

    # Populate form on GET request
    if method == "GET":
        form.bill_id.data = bill_data.get('bill_id', '')
        
        # Find a default payment account (not the current account)
        default_payment_account = None
        for _, row in accounts_df.iterrows():
            if row["AccountType"] in ["Checking", "Savings"] and int(row["AccountID"]) != account_id:
                default_payment_account = int(row["AccountID"])
                break
                
        if default_payment_account:
            form.paymentAccID.data = default_payment_account
        
        # Set bill type based on account type
        if account_type == 'Credit Card':
            form.bill_type.data = 'CreditCard'
            form.is_recurring.data = True
            form.payee_name.data = bill_data.get('payee_name', "Evergreen Bank Credit Card")
            form.payee_address.data = bill_data.get('payee_address', "Evergreen Bank Payments Dept")
            
            # Set due date for credit cards without bills
            if not bill_data.get('due_date_obj') and bill_data.get('due_date_str'):
                try:
                    form.due_date.data = datetime.strptime(bill_data.get('due_date_str'), "%Y-%m-%d").date()
                except:
                    form.due_date.data = datetime.now().date() + timedelta(days=25)
            
        elif account_type == 'Mortgage Loan':
            form.bill_type.data = 'Mortgage'
            form.is_recurring.data = True
        else:
            form.bill_type.data = 'Regular'
        
        # Set payee information if bill exists
        if bill_data.get('bill_id'):
            form.payee_name.data = bill_data.get('payee_name')
            form.payee_address.data = bill_data.get('payee_address')
            if bill_data.get('due_date_obj'):
                form.due_date.data = bill_data.get('due_date_obj')
        
        # Set default due date if none exists
        if not form.due_date.data:
            form.due_date.data = datetime.now().date() + timedelta(days=25)
                
    return form


def process_bill_payment(form: BillPaymentForm, account_id: int, account_type: str, customer_id: int):
    """
    Processes a bill payment submission.
    """
    bill_id = form.bill_id.data
    amount = Decimal(form.amount.data).quantize(Decimal("0.00"))
    due_date_str = form.due_date.data.strftime("%Y-%m-%d") if form.due_date.data else ""
    payee_name = form.payee_name.data
    payee_address = form.payee_address.data
    payment_account_id = int(form.paymentAccID.data)

    # Load data files
    try:
        bills_df, accounts_df, logs_df = read_dataframes()
    except Exception:
        flash_error("Unable to read data files.")
        return redirect(url_for("customer.customer_dashboard"))

    # Basic validation for all payment types
    if amount <= Decimal("0.00"):
        flash_error("Payment amount must be greater than zero.")
        return get_redirect_url(account_id, account_type)
        
    if payment_account_id == account_id:
        flash_error("Payment account cannot be the same as the bill account.")
        return get_redirect_url(account_id, account_type)
    
    # Check if payment account has sufficient funds
    if not has_sufficient_funds(payment_account_id, amount):
        flash_error("Insufficient funds in payment account.")
        return get_redirect_url(account_id, account_type)

    # Process based on bill existence
    if bill_id and int(bill_id) in bills_df['BillID'].values:
        try:
            return process_existing_bill_payment(
                bills_df, accounts_df, logs_df,
                bill_id, amount, due_date_str, payee_name, payee_address,
                payment_account_id, account_id, account_type, customer_id, form
            )
        except Exception as e:
            logger.error(f"Bill payment processing failed: {e}", exc_info=True)
            flash_error("An error occurred while processing your payment.")
            return get_redirect_url(account_id, account_type)
    else:
        # If no active bill found
        if account_type == 'Credit Card':
            # For credit cards, directly process payment without creating a bill
            return process_direct_credit_card_payment(
                customer_id, account_id, payment_account_id, amount, payee_name, accounts_df
            )
        else:
            # For other account types, create a new bill
            return create_new_bill(
                customer_id, payee_name, payee_address, 
                amount, due_date_str, account_id, account_type
            )


def get_redirect_url(account_id, account_type):
    """Helper to get the appropriate redirect URL based on account type."""
    if account_type in ["Credit Card", "Mortgage Loan"]:
        return redirect(url_for("customer.credit_mortgage_page", account_id=account_id))
    else:
        return redirect(url_for("customer.account_overview", account_id=account_id))


def has_sufficient_funds(account_id, amount):
    """Checks if an account has sufficient funds for a payment."""
    account = load_account_by_id(account_id)
    balance = Decimal(account["CurrBal"]).quantize(Decimal("0.00"))
    return balance >= amount


def process_direct_credit_card_payment(customer_id, account_id, payment_account_id, amount, payee_name, accounts_df):
    """Directly processes a credit card payment without an existing bill."""
    # Load account data
    try:
        account_row = load_account_by_id(account_id)
        payment_account_row = load_account_by_id(payment_account_id)
    except Exception:
        flash_error("Error retrieving account details.")
        return redirect(url_for("customer.customer_dashboard"))
    
    # Convert balances to Decimal
    credit_card_balance = Decimal(account_row["CurrBal"]).quantize(Decimal("0.00"))  # Negative value
    payment_account_balance = Decimal(payment_account_row["CurrBal"]).quantize(Decimal("0.00"))
    
    # Validate payment amount - ensure not paying more than owed
    # Since balance is negative, adding amount should not make it positive
    if credit_card_balance + amount > Decimal("0.00"):
        flash_error(f"Payment amount (${amount:.2f}) exceeds the credit card balance (${abs(credit_card_balance):.2f}).")
        return redirect(url_for("customer.credit_mortgage_page", account_id=account_id))
    
    # Calculate and update balances
    # For credit card: Add payment to negative balance to reduce debt
    new_credit_card_balance = credit_card_balance + amount
    # For payment account: Subtract payment amount
    new_payment_account_balance = payment_account_balance - amount
    
    update_account_balance(accounts_df, account_id, new_credit_card_balance)
    update_account_balance(accounts_df, payment_account_id, new_payment_account_balance)
    
    # Record the transactions
    record_payment_transactions(payment_account_id, account_id, amount, payee_name, "Credit Card")
    
    # Show success message
    if new_credit_card_balance == Decimal("0.00"):
        flash_success(f"Credit card balance fully paid. Your balance is now $0.00")
    else:
        remaining_balance = abs(new_credit_card_balance)
        flash_success(f"Payment of ${amount:.2f} successfully applied to your credit card. Remaining balance: ${remaining_balance:.2f}")
    
    return redirect(url_for("customer.credit_mortgage_page", account_id=account_id))


def process_existing_bill_payment(bills_df, accounts_df, logs_df, bill_id, amount, due_date_str, 
                                 payee_name, payee_address, payment_account_id, account_id, 
                                 account_type, customer_id, form):
    """Processes payment for an existing bill."""
    bill_index = bills_df[bills_df['BillID'] == int(bill_id)].index[0]
    bill_record = bills_df.iloc[bill_index]
    
    # For bills, Amount is negative, so use abs() to get positive payment amount
    full_amount_due = abs(Decimal(bill_record["Amount"]).quantize(Decimal("0.00")))
    bill_type = bill_record["BillType"]
    is_recurring = bill_record["IsRecurring"]

    # Try to get the current bill's due date
    try:
        current_due_date = datetime.strptime(bill_record["DueDate"], "%Y-%m-%d").date()
    except Exception:
        current_due_date = datetime.now().date()

    # Validate payment amount based on bill type
    validation_result = validate_payment_amount(
        bill_type, amount, full_amount_due, bill_record, 
        account_id, form, due_date_str, account_type
    )
    if validation_result:
        return validation_result
    
    # Account validation already done in the main process_bill_payment function
    
    # Update account balances
    account_balance = Decimal(load_account_by_id(account_id)["CurrBal"]).quantize(Decimal("0.00"))
    payment_account_balance = Decimal(load_account_by_id(payment_account_id)["CurrBal"]).quantize(Decimal("0.00"))
    
    # Calculate new balances
    if account_type in ["Credit Card", "Mortgage Loan"]:
        # For loans/credit cards: Add payment to negative balance to reduce debt
        new_balance = account_balance + amount
    else:
        # For regular accounts: Balance doesn't change as bill payment affects external entity
        new_balance = account_balance
    
    # Payment account always decreases
    new_payment_balance = payment_account_balance - amount
    
    # Update balances and record transactions
    update_account_balance(accounts_df, account_id, new_balance)
    update_account_balance(accounts_df, payment_account_id, new_payment_balance)
    record_payment_transactions(payment_account_id, account_id, amount, payee_name, account_type)
    
    # Process bill based on type
    if bill_type == "CreditCard":
        return process_credit_card_bill(
            bills_df, bill_id, bill_index, amount, full_amount_due, 
            is_recurring, account_id, customer_id, bill_record, current_due_date
        )
    elif bill_type == "Mortgage":
        return process_mortgage_bill(
            bills_df, bill_id, bill_index, amount, full_amount_due,
            is_recurring, account_id, customer_id, bill_record, current_due_date, new_balance
        )
    else:
        return process_regular_bill(
            bills_df, bill_id, bill_index, amount, is_recurring,
            customer_id, bill_record, account_id, current_due_date
        )


def validate_payment_amount(bill_type, amount, full_amount_due, bill_record, 
                          account_id, form, due_date_str, account_type):
    """Validates payment amount based on bill type."""
    # Load account for template rendering
    try:
        account = load_account_by_id(account_id)
    except Exception:
        account = {"AccountID": account_id, "CurrBal": 0, "AccountType": account_type}
    
    error_template = lambda error_msg: render_template(
        "customer/bill_pay.html", 
        form=form, 
        account_id=account_id,
        min_amount=float(bill_record.get("MinPayment", full_amount_due)), 
        due_date=due_date_str, 
        account_type=account_type,
        account=account
    )
    
    if bill_type == "CreditCard":
        # MinPayment is stored as positive value
        min_payment = Decimal(bill_record["MinPayment"]).quantize(Decimal("0.00"))
        
        # Must pay at least minimum payment
        if amount < min_payment:
            flash_error(f"You must pay at least the minimum payment of ${min_payment:.2f}.")
            return error_template(f"You must pay at least the minimum payment of ${min_payment:.2f}.")
        
        # Cannot exceed bill amount
        if amount > full_amount_due:
            flash_error(f"Payment exceeds the remaining bill amount of ${full_amount_due:.2f}.")
            return error_template(f"Payment exceeds the remaining bill amount of ${full_amount_due:.2f}.")
        
    elif bill_type == "Mortgage":
        # Must pay at least the required amount
        if amount < full_amount_due:
            flash_error(f"You must pay at least the minimum payment of ${full_amount_due:.2f}.")
            return error_template(f"You must pay at least the minimum payment of ${full_amount_due:.2f}.")
        
        # Cannot exceed mortgage balance - CurrBal is negative for mortgages
        mortgage_balance = abs(Decimal(account["CurrBal"]).quantize(Decimal("0.00")))
        if amount > mortgage_balance:
            flash_error(f"Payment amount (${amount:.2f}) exceeds the remaining mortgage balance (${mortgage_balance:.2f}).")
            return error_template(f"Payment amount exceeds the remaining mortgage balance.")
    else:
        # For regular bills: Payment must match the full amount
        if amount != full_amount_due:
            flash_error(f"You must pay the exact bill amount of ${full_amount_due:.2f}.")
            return error_template(f"You must pay the exact bill amount of ${full_amount_due:.2f}.")
    
    return None


def record_payment_transactions(payment_account_id, account_id, amount, payee_name, account_type):
    """Records transactions for a bill payment."""
    trans_path = get_csv_path("transactions.csv")
    trans_data = pd.read_csv(trans_path)

    # Transaction for the source account (payment)
    transaction_id = generate_transaction_ID(trans_data)
    source_transaction = {
        'TransactionID': transaction_id,
        'AccountID': payment_account_id,
        'TransactionType': f"Bill Payment to {payee_name}",
        'Amount': -float(amount),  # Negative amount since money is leaving this account
        'TransDate': datetime.now().strftime("%Y-%m-%d")
    }
    trans_data.loc[len(trans_data)] = source_transaction

    # For credit cards and mortgages, also create a transaction for the destination account
    if account_type in ["Credit Card", "Mortgage Loan"]:
        dest_transaction_type = "Loan Payment Received" if account_type == "Mortgage Loan" else "Payment Received"
        
        dest_transaction_id = generate_transaction_ID(trans_data)
        dest_transaction = {
            'TransactionID': dest_transaction_id,
            'AccountID': account_id,
            'TransactionType': dest_transaction_type,
            'Amount': float(amount),  # Positive amount since money is being added to this account
            'TransDate': datetime.now().strftime("%Y-%m-%d")
        }
        trans_data.loc[len(trans_data)] = dest_transaction

    # Save updated transactions
    trans_data.to_csv(trans_path, index=False)


def process_credit_card_bill(bills_df, bill_id, bill_index, amount, full_amount_due, 
                          is_recurring, account_id, customer_id, bill_record, current_due_date):
    """Processes a credit card bill payment."""
    remaining_amount = full_amount_due - amount
    
    if remaining_amount > Decimal("0.00"):
        # Partial payment - update bill
        archive("bill", int(bill_id), remove_record=False)
        # Store remaining amount as negative value
        bills_df.at[bill_index, 'Amount'] = -remaining_amount
        bills_df.at[bill_index, 'Status'] = 'PartiallyPaid'
        bills_df.to_csv(get_csv_path("bills.csv"), index=False)
        
        flash_success(f"Partial payment of ${amount:.2f} applied. Remaining balance: ${remaining_amount:.2f}")
    else:
        # Full payment - mark as paid
        bills_df.at[bill_index, 'Status'] = 'Paid'
        bills_df.to_csv(get_csv_path("bills.csv"), index=False)
        
        # Check if new bill needed
        account = load_account_by_id(account_id)
        current_balance = Decimal(account["CurrBal"]).quantize(Decimal("0.00"))
        
        # CurrBal is negative for credit cards with a balance to pay
        if current_balance < Decimal("0.00") and is_recurring == 1:
            # Calculate new minimum payment as positive value
            new_min = max(Decimal("25.00"), abs(current_balance) * Decimal("0.02")).quantize(Decimal("0.00"))
            
            # Calculate next due date (30 days after previous due date)
            next_due_date = current_due_date + relativedelta(months=1)

            # Schedule new bill
            scheduleBillPayment(
                customerID=customer_id,
                payeeName=bill_record["PayeeName"],
                payeeAddress=bill_record["PayeeAddress"],
                # Store amount as negative value
                amount=-abs(current_balance),
                dueDate=next_due_date.isoformat(),
                paymentAccID=account_id,
                minPayment=new_min,  # MinPayment is positive
                billType='CreditCard',
                isRecurring=1
            )
            
            flash_success(f"Payment complete. Your next bill of ${abs(current_balance):.2f} is due on {next_due_date}.")
        else:
            # Archive the bill
            archive("bill", int(bill_id), remove_record=True)
            flash_success("Bill fully paid. Your balance is now $0.00.")
    
    return redirect(url_for("customer.customer_dashboard"))


def process_mortgage_bill(bills_df, bill_id, bill_index, amount, full_amount_due,
                        is_recurring, account_id, customer_id, bill_record,
                        current_due_date, new_balance):
    """Processes a mortgage bill payment."""
    # Mark bill as paid
    bills_df.at[bill_index, 'Status'] = 'Paid'
    bills_df.to_csv(get_csv_path("bills.csv"), index=False)
    
    # Check if mortgage is fully paid - new_balance should be 0 or positive
    if new_balance >= Decimal("0.00"):
        # Mortgage fully paid - archive
        archive("loan", account_id)
        archive("bill", int(bill_id), remove_record=True)
        flash_success("Mortgage fully paid off and archived.")
        return redirect(url_for("customer.customer_dashboard"))
    
    # Not fully paid - schedule next payment if recurring
    if is_recurring == 1:
        # Calculate next due date
        next_due_date = current_due_date + relativedelta(months=1)
        
        scheduleBillPayment(
            customerID=customer_id,
            payeeName=bill_record["PayeeName"],
            payeeAddress=bill_record["PayeeAddress"],
            # Store amount as negative value
            amount=-full_amount_due,
            dueDate=next_due_date.isoformat(),
            paymentAccID=account_id,
            minPayment=full_amount_due,  # MinPayment is positive
            billType='Mortgage',
            isRecurring=1
        )
        
        # Archive the current bill
        archive("bill", int(bill_id), remove_record=True)
        
        if amount > full_amount_due:
            flash_success(f"Mortgage payment of ${amount:.2f} complete (includes extra payment of ${(amount-full_amount_due):.2f}). Your next payment of ${full_amount_due:.2f} is due on {next_due_date}.")
        else:
            flash_success(f"Mortgage payment complete. Your next payment of ${full_amount_due:.2f} is due on {next_due_date}.")
    else:
        # Archive the bill
        archive("bill", int(bill_id), remove_record=True)
        flash_success(f"Mortgage payment of ${amount:.2f} complete.")
    
    return redirect(url_for("customer.customer_dashboard"))


def process_regular_bill(bills_df, bill_id, bill_index, amount, is_recurring,
                       customer_id, bill_record, account_id, current_due_date):
    """Processes a regular bill payment."""
    # Mark as paid
    bills_df.at[bill_index, 'Status'] = 'Paid'
    bills_df.to_csv(get_csv_path("bills.csv"), index=False)
    
    # If recurring, schedule the next one
    if is_recurring == 1:
        # Calculate next due date
        next_due_date = current_due_date + relativedelta(months=1)
        
        scheduleBillPayment(
            customerID=customer_id,
            payeeName=bill_record["PayeeName"],
            payeeAddress=bill_record["PayeeAddress"],
            # Store amount as negative value
            amount=-amount,
            dueDate=next_due_date.isoformat(),
            paymentAccID=account_id,
            minPayment=amount,  # MinPayment is positive
            billType=bill_record["BillType"],
            isRecurring=1
        )
        
        # Archive the current bill
        archive("bill", int(bill_id), remove_record=True)
        
        flash_success(f"Bill paid. Your next recurring payment of ${amount:.2f} is due on {next_due_date}.")
    else:
        # Archive the bill
        archive("bill", int(bill_id), remove_record=True)
        flash_success(f"Bill payment of ${amount:.2f} complete.")
    
    return redirect(url_for("customer.account_overview", account_id=account_id))


def create_new_bill(customer_id, payee_name, payee_address, amount, due_date_str, account_id, account_type):
    """Creates a new bill when no active bill exists."""
    result = scheduleBillPayment(
        customerID=customer_id,
        payeeName=payee_name,
        payeeAddress=payee_address,
        # Store amount as negative value
        amount=-amount,
        dueDate=due_date_str,
        paymentAccID=account_id
    )
    
    if result["status"] == "success":
        flash_success(result["message"])
    else:
        flash_error(result["message"])
        
    return get_redirect_url(account_id, account_type)

# =============================================================================
# API Endpoints
# =============================================================================

@customer_bp.route('/api/transactions/<int:account_id>')
@login_required("customer_id")
def get_transactions(account_id):
    """
    Retrieves transaction history for an account, split into current (last 30 days) 
    and past transactions.
    
    Returns:
        JSON: Transaction data or error message
    """
    try:
        # Load and process transaction data
        transactions_df = load_transactions_for_account(account_id)
        
        # Split transactions into current and past
        current_transactions, past_transactions = split_transactions_by_date(transactions_df)
        
        # Format and return the data
        return jsonify({
            "current_transactions": format_transaction_data(current_transactions),
            "past_transactions": format_transaction_data(past_transactions)
        })
    except Exception as e:
        logger.error(f"Error retrieving transactions: {e}", exc_info=True)
        return jsonify({"error": str(e)})


def load_transactions_for_account(account_id):
    """
    Loads transaction data for a specific account.
    
    Returns:
        DataFrame: Filtered transactions for the account
    """
    path = get_csv_path('transactions.csv')
    df = pd.read_csv(path)
    
    # Filter for the account and convert dates
    matching = df[df['AccountID'] == account_id].copy()
    if 'TransDate' in matching.columns:
        matching["TransDate"] = pd.to_datetime(matching["TransDate"], errors='coerce')
    
    return matching


def split_transactions_by_date(transactions_df):
    """
    Splits transactions into current (last 30 days) and past.
    
    Returns:
        tuple: (current_transactions, past_transactions) DataFrames
    """
    today = datetime.today()
    cutoff = today - relativedelta(months=1)
    
    current_df = transactions_df[transactions_df['TransDate'] >= cutoff]
    past_df = transactions_df[transactions_df['TransDate'] < cutoff]
    
    return current_df, past_df


def format_transaction_data(transactions_df):
    """
    Formats transaction data for JSON response.
    
    Returns:
        list: Formatted transaction dictionaries
    """
    return [
        {
            "TransDate": row["TransDate"].strftime("%Y-%m-%d"),
            "description": str(row["TransactionType"]).capitalize(),
            "amount": float(row["Amount"])
        }
        for _, row in transactions_df.iterrows()
    ]


@customer_bp.route('/archived-bills/<int:account_id>')
@login_required("customer_id")
def get_archived_bills(account_id: int):
    """
    Retrieve archived bills for a specific account.
    
    Returns:
        JSON: Archived bills data or error message
    """
    try:
        # Get customer ID and load archived bills
        customer_id = get_logged_in_customer()
        archived_bills = viewArchivedBills(customer_id)
        
        # Filter bills by account ID
        filtered_bills = [
            bill for bill in archived_bills 
            if int(bill.get("PaymentAccID", -1)) == account_id
        ]
        
        return jsonify({"archived_bills": filtered_bills})
    except Exception as e:
        logger.debug(f"Error in get_archived_bills for account {account_id}: {e}")
        return jsonify({"error": "Failed to load archived bills."}), 500


@customer_bp.route('/api/account-balance/<int:account_id>')
@login_required("customer_id")
def get_account_balance(account_id: int):
    """
    Retrieve the current balance and type of an account.
    
    Returns:
        JSON: Account balance information or error message
    """
    try:
        # Load account data
        account_data = load_account_data(account_id)
        
        return jsonify(account_data)
    except Exception as e:
        logger.error(f"Error retrieving balance for account {account_id}: {e}")
        return jsonify({"error": f"Failed to get balance: {str(e)}"}), 500


def load_account_data(account_id: int):
    """
    Loads account information including balance and account type.
    For credit cards, also calculates the minimum payment.
    
    Returns:
        dict: Account information
    """
    # Retrieve account information
    account, _, customer_id = get_account_by_id(account_id)
    account_type = account["AccountType"].upper()
    balance = float(account["CurrBal"])
    
    # Build response data
    account_data = {
        "balance": balance,
        "account_type": account_type,
        "amount_due": None
    }
    
    # For credit cards, calculate minimum payment
    if account_type == "CREDIT CARD":
        account_data["amount_due"] = float(calculate_min_payment(Decimal(str(balance))))
    
    return account_data


@customer_bp.route('/api/bill-info/<int:account_id>')
@login_required("customer_id")
def get_bill_info(account_id: int):
    """
    Retrieve bill information for an account.
    
    Returns:
        JSON: Bill information or status message
    """
    try:
        # Find active bill for the account
        bill_data = find_active_bill(account_id)
        
        if bill_data:
            return jsonify(bill_data)
        else:
            return jsonify({
                "message": "No active bill found for this account."
            })
    except Exception as e:
        logger.error(f"Error retrieving bill for account {account_id}: {e}")
        return jsonify({"error": f"Failed to get bill information: {str(e)}"}), 500


def find_active_bill(account_id: int):
    """
    Finds the active bill for an account.
    
    Returns:
        dict or None: Bill information if found, None otherwise
    """
    # Load bills data
    bills_df = load_csv("bills.csv")
    bills_df["PaymentAccID"] = bills_df["PaymentAccID"].astype(int)
    
    # Filter for active bills for this account
    matching = bills_df[
        (bills_df["PaymentAccID"] == account_id) & 
        (bills_df["Status"].isin(["Pending", "PartiallyPaid", "Late"]))
    ]
    
    if not matching.empty:
        # Convert dates and find earliest due bill
        matching.loc[:, "DueDate"] = pd.to_datetime(matching["DueDate"], errors="coerce")
        earliest_bill = matching.sort_values("DueDate").iloc[0]
        
        # Format bill data
        return {
            "bill_id": int(earliest_bill["BillID"]),
            "amount": float(earliest_bill["Amount"]),
            "min_payment": float(earliest_bill["MinPayment"]),
            "due_date": earliest_bill["DueDate"].strftime("%Y-%m-%d"),
            "status": earliest_bill["Status"]
        }
    
    return None