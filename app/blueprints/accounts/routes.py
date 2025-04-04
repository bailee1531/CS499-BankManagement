"""
accounts/routes.py

Defines routes for handling personal accounts, credit cards, and mortgage applications.
"""
import pandas as pd
from decimal import Decimal

from flask import (
    Blueprint, render_template, session, flash, redirect, url_for, request, Response
)

# Internal utility and form imports
from scripts import createCreditCard, createLoan
from app.blueprints.sharedUtilities import get_csv_path, flash_success, flash_error
from app.blueprints.accounts.forms import MortgageForm

# Initialize blueprint
accounts_bp = Blueprint('accounts', __name__, template_folder='templates')


# -----------------------------------------------------------------------------
# Route: /personal
# Displays the personal accounts page or redirects to deposit form if a type is selected
# -----------------------------------------------------------------------------
@accounts_bp.route('/personal', methods=['GET'])
def personal_accounts() -> Response:
    """
    Display personal accounts page or redirect to deposit form if an account type is provided.

    Returns:
        Response: Rendered personal accounts page or redirection to deposit form.
    """
    account_type: str = request.args.get("account_type")

    if account_type:
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

        # Set pending account info in session and redirect to deposit form
        session['pending_account_type'] = account_type
        session['pending_account_name'] = valid_types[account_type]
        return redirect(url_for("registration.deposit_form"))

    return render_template('accounts/personal_accounts.html')


# -----------------------------------------------------------------------------
# Route: /credit-cards
# Handles credit card actions (e.g., Travel Visa card)
# -----------------------------------------------------------------------------
@accounts_bp.route('/credit-cards')
def credit_cards() -> Response:
    """
    Handle credit card operations, including opening a Travel Visa credit card.

    Returns:
        Response: Rendered credit card page or redirection after processing.
    """
    card_to_open: str = request.args.get('open')

    if card_to_open:
        if "customer_id" not in session:
            flash_error("You must be logged in to open a credit card.")
            return redirect(url_for("auth.customer_login", next=request.url))

        customer_id: int = session["customer_id"]

        if card_to_open.lower() == 'travel-visa':
            try:
                accounts_df = pd.read_csv(get_csv_path("accounts.csv"))

                # Check if the user already has a credit card
                existing_card = accounts_df[
                    (accounts_df["CustomerID"] == customer_id) &
                    (accounts_df["AccountType"] == "Credit Card")
                ]
                if not existing_card.empty:
                    flash("You already have a Travel Visa credit card.", "warning")
                    return redirect(url_for("accounts.credit_cards"))

                # Create the credit card account
                createCreditCard.openCreditCardAccount(customer_id)
                flash_success("Travel Visa credit card opened successfully!")
                return redirect(url_for("customer.customer_dashboard"))

            except Exception as e:
                flash_error(f"Unable to open Travel Visa account: {str(e)}")
                return redirect(url_for("accounts.credit_cards"))

        flash_error("Invalid credit card selection.")
        return redirect(url_for("accounts.credit_cards"))

    return render_template('accounts/credit_cards.html')


# Route for viewing about us page
@accounts_bp.route('/about_us')
def about_us():
    return render_template('accounts/about_us.html')

# -----------------------------------------------------------------------------
# Route: /loans
# Displays general loan info page
# -----------------------------------------------------------------------------
@accounts_bp.route('/loans')
def loans() -> Response:
    """
    Render loan information page.

    Returns:
        Response: Rendered loan information page.
    """
    return render_template('accounts/loan_info.html')


# -----------------------------------------------------------------------------
# Route: /customer/mortgage
# Handles GET/POST for mortgage loan application
# -----------------------------------------------------------------------------
@accounts_bp.route('/customer/mortgage', methods=['GET', 'POST'])
def mortgage_application():
    """
    Route for mortgage loan application.

    Returns:
        Response: Redirects to dashboard on success, otherwise renders the application form.
    """
    form = MortgageForm()

    if form.validate_on_submit():
        loan_amount = Decimal(form.loan_amount.data)
        loan_term = form.loan_term.data
        customer_id = session.get("customer_id")

        if not customer_id:
            flash_error("Customer not logged in or session expired.")
            return redirect(url_for('auth.customer_login'))

        try:
            accounts_df = pd.read_csv(get_csv_path("accounts.csv"))

            # Check for existing mortgage
            existing_mortgage = accounts_df[
                (accounts_df["CustomerID"] == customer_id) &
                (accounts_df["AccountType"].str.lower() == "mortgage loan")
            ]
            if not existing_mortgage.empty:
                flash_error("You already have a mortgage loan account. Only one is allowed per customer.")
                return redirect(url_for("customer.customer_dashboard"))

        except Exception as e:
            flash_error(f"Error checking existing mortgage accounts: {str(e)}")
            return redirect(url_for("customer.customer_dashboard"))

        # Attempt to create new mortgage loan
        result = createLoan.createMortgageLoanAccount(customer_id, loan_amount, loan_term)
        if result.get("status") == "success":
            flash_success(result.get("message"))
            return redirect(url_for('customer.customer_dashboard'))
        else:
            flash_error(result.get("message"))

    return render_template(
        'accounts/mortgage_application.html',
        form=form,
        form_action=url_for('accounts.mortgage_application')
    )


# -----------------------------------------------------------------------------
# Route: /page-error
# -----------------------------------------------------------------------------
@accounts_bp.route('/page_error')
def page_error():
    """
    Route for error page.

    Returns:
    --------
    Response: Redirects to the error page.
    """
    return render_template("accounts/not_found.html")
