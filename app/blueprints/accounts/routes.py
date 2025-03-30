from flask import Blueprint, render_template, session, flash, redirect, url_for, request, Response
import pandas as pd

from scripts.customer import openAcc
from scripts import createCreditCard
from app.blueprints.utilities import (
    get_csv_path, get_logged_in_customer,
    get_customer_accounts, user_has_account_type,
    login_required, flash_success, flash_error
)

accounts_bp = Blueprint('accounts', __name__, template_folder='templates')

@accounts_bp.route('/personal', methods=['GET'])
def personal_accounts() -> Response:
    """
    Display personal accounts page or redirect to deposit form if an account type is provided.

    Returns:
        Response: Rendered template for personal accounts or a redirection response.
    """
    account_type: str = request.args.get("account_type")  # e.g., "checking", "savings", etc.

    if account_type:
        # Ensure customer is logged in by checking for customer_id in session
        if "customer_id" not in session:
            flash_error("You must be logged in to open an account.")
            return redirect(url_for("auth.customer_login", next=request.url))

        valid_types = {
            "checking": "Regular Checking Account",
            "savings": "Savings Account",
            "money-market": "Money Market Account"
        }

        if account_type not in valid_types:
            flash_error("Invalid account type selected.")
            return redirect(url_for("accounts.personal_accounts"))

        # Set pending account information in session and redirect to deposit step
        session['pending_account_type'] = account_type
        session['pending_account_name'] = valid_types[account_type]
        return redirect(url_for("auth.deposit_form"))

    return render_template('accounts/personal_accounts.html')


@accounts_bp.route('/credit-cards')
def credit_cards() -> Response:
    """
    Handle credit card operations, including opening a Travel Visa credit card.

    Returns:
        Response: Rendered template for credit cards or redirection after processing.
    """
    card_to_open: str = request.args.get('open')
    if card_to_open:
        # Ensure customer is logged in by checking for customer_id in session
        if "customer_id" not in session:
            flash_error("You must be logged in to open a credit card.")
            return redirect(url_for("auth.customer_login", next=request.url))

        customer_id: int = session["customer_id"]

        if card_to_open.lower() == 'travel-visa':
            try:
                # Read current accounts from CSV and check if the credit card already exists
                accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
                existing_card = accounts_df[
                    (accounts_df["CustomerID"] == customer_id) &
                    (accounts_df["AccountType"] == "Credit Card")
                ]
                if not existing_card.empty:
                    flash("You already have a Travel Visa credit card.", "warning")
                    return redirect(url_for("accounts.credit_cards"))

                createCreditCard.openCreditCardAccount(customer_id)
                flash_success("Travel Visa credit card opened successfully!")
                return redirect(url_for("accounts.user_dashboard"))
            except Exception as e:
                flash_error(f"Unable to open Travel Visa account: {str(e)}")
                return redirect(url_for("accounts.credit_cards"))
        else:
            flash_error("Invalid credit card selection.")
            return redirect(url_for("accounts.credit_cards"))

    return render_template('accounts/credit_cards.html')


@accounts_bp.route('/mortgage')
def mortgage() -> Response:
    """
    Render mortgage information page.

    Returns:
        Response: Rendered template for mortgage information.
    """
    return render_template('accounts/mortgage.html')


@accounts_bp.route('/accounts')
@login_required("customer_id")
def user_dashboard() -> Response:
    """
    Render the user's dashboard displaying their accounts.

    Returns:
        Response: Rendered template for the user's dashboard.
    """
    customer_id: int = get_logged_in_customer()
    try:
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
        accounts_list = []

    return render_template("accounts/user_dashboard.html", accounts=accounts_list)


@accounts_bp.route('/account/<int:account_id>')
@login_required("customer_id")
def account_detail(account_id: int) -> Response:
    """
    Display detailed information for a specific account.

    Args:
        account_id (int): The ID of the account to display.

    Returns:
        Response: Rendered template with account details or redirection on error.
    """
    try:
        accounts_df = pd.read_csv(get_csv_path("accounts.csv"))
        account_row = accounts_df[accounts_df["AccountID"] == account_id]
        if account_row.empty:
            flash_error("Account not found.")
            return redirect(url_for("accounts.user_dashboard"))
        account = account_row.iloc[0].to_dict()
    except Exception as e:
        flash_error("Error retrieving account details.")
        return redirect(url_for("accounts.user_dashboard"))

    return render_template("accounts/account_detail.html", account=account)

@accounts_bp.route("/admin-dashboard")
def admin_dashboard():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../csvFiles/employees.csv"))
    df = pd.read_csv(csv_path)
    tellers = df[df["Position"] == "Teller"].to_dict(orient="records")
    return render_template("auth/admin_dashboard.html", tellers=tellers)