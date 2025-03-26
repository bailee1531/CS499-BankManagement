from flask import Blueprint, render_template, request, redirect, url_for, flash

# Create a blueprint for the accounts-related pages.
# This helps modularize the application for better organization and reuse.
# The 'url_prefix' means all routes in this blueprint will start with '/accounts'.
accounts_bp = Blueprint(
    'accounts',  # Blueprint name
    __name__,    # Blueprint import name (usually __name__)
    url_prefix='/accounts',  # Prefix for all routes in this blueprint
    template_folder='templates'  # Location of the template files
)

# Route for viewing personal accounts
@accounts_bp.route('/personal')
def personal_accounts():
    return render_template('accounts/personal_accounts.html')

# Route for viewing credit card accounts
@accounts_bp.route('/credit-cards')
def credit_cards():
    return render_template('accounts/credit_cards.html')

# Route for viewing mortgage account
@accounts_bp.route('/mortgage')
def mortgage():
    return render_template('accounts/mortgage.html')

# Route for the user dashboard
# Accepts both GET and POST requests
@accounts_bp.route('/account-dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if request.method == 'POST':
        # Get the account type from the submitted form data
        account_type = request.form.get('account_type', 'personal')  # Default to 'personal' if not provided
    else:
        account_type = None  # Default value on GET request
    
    # Render the dashboard template, passing the account type to the frontend
    return render_template('accounts/user_dashboard.html', account_type=account_type)
