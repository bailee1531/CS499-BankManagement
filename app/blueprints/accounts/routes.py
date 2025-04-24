"""
accounts/routes.py

Defines routes for handling personal accounts, credit cards, and mortgage applications.
"""
import pandas as pd
from decimal import Decimal
from datetime import date, timedelta

from flask import (
    Blueprint, render_template, session, redirect, url_for, request, Response
)

# Import shared utilities for checking account type and managing flash messages
from app.blueprints.sharedUtilities import (
    user_has_account_type, get_csv_path, 
    flash_success, flash_error, get_customer_accounts, login_required
)
# Internal utility and form imports
from scripts import createCreditCard, createLoan
from scripts.billPayment import scheduleBillPayment
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
    from scripts.customer import openAcc
    account_type: str = request.args.get("account_type")
    customer_id = session.get("customer_id")

    if account_type:
        if "customer_id" not in session:
            flash_error("You must be logged in to open an account.")
            return redirect(url_for("auth.customer_login", next=request.url))

        valid_types = {
            "Checking": "Checking Account",
            "Savings": "Savings Account",
            "Money Market": "Money Market Account"
        }

        if account_type not in valid_types:
            flash_error("Invalid account type selected.")
            return redirect(url_for("accounts.personal_accounts"))

        # Set pending account info in session and redirect to customer dashboard
        session['pending_account_type'] = account_type
        openAcc.open_account(customer_id, account_type, 0.00)   # Customers can't deposit money, so start with 0 account balance
        session.pop('pending_account_type', None)
        return redirect(url_for("customer.customer_dashboard"))

    return render_template('accounts/personal_accounts.html')


# -----------------------------------------------------------------------------
# Route: /credit-cards
# Handles credit card actions 
# -----------------------------------------------------------------------------
@accounts_bp.route('/credit-cards')
def credit_cards() -> Response:
    """
    Handle credit card operations, including opening a credit card.
    Returns:
        Response: Rendered credit card page or redirection after processing.
    """
    card_to_open = request.args.get('open')

    if card_to_open:
        try:
            # Retrieve customer_id from session
            customer_id = session.get("customer_id")
            if not customer_id:
                flash_error("You must be logged in to open an account.")
                return redirect(url_for("auth.customer_login", next=request.url))

            if card_to_open.lower() == 'credit-card':
                accounts_df = get_customer_accounts(customer_id)
                credit_cards = accounts_df[accounts_df["AccountType"] == "Credit Card"]

                if len(credit_cards) >= 1:
                    flash_error("You can only have up to 1 credit cards.")
                    return redirect(url_for("accounts.credit_cards"))

                # Create the credit card account
                result = createCreditCard.openCreditCardAccount(customer_id)

                # Only show success if account was created successfully
                if result.get("status") == "success":
                    flash_success("Credit card opened successfully!")
                    return redirect(url_for("customer.customer_dashboard"))
                else:
                    flash_error(result.get("message"))
                    return redirect(url_for("accounts.credit_cards"))

            flash_error("Invalid credit card selection.")
            return redirect(url_for("accounts.credit_cards"))

        except Exception as e:
            flash_error(f"Unable to open credit card account: {str(e)}")
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
@login_required("customer_id")
def mortgage_application():

    form = MortgageForm()

    if form.validate_on_submit():
        loan_amount = Decimal(form.loan_amount.data)
        loan_term = form.loan_term.data
        customer_id = session.get("customer_id")

        # Enforce minimum loan amount
        if loan_amount < Decimal("50.00"):
            flash_error("The minimum loan amount is $50.")
            return render_template(
                'accounts/mortgage_application.html',
                form=form,
                form_action=url_for('accounts.mortgage_application')
            )
        
        if loan_term > 50:
            flash_error("Loan term cannot exceed 50 years.")
            return render_template(
                'accounts/mortgage_application.html',
                form=form,
                form_action=url_for('accounts.mortgage_application')
            )
    
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
