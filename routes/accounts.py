import os
import pandas as pd
from flask import Blueprint, render_template, session, flash, redirect, url_for, current_app

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts", template_folder="templates")

@accounts_bp.route('/personal')
def personal_accounts():
    return render_template('accounts/personal_accounts.html')

@accounts_bp.route('/credit-cards')
def credit_cards():
    return render_template('accounts/credit_cards.html')

@accounts_bp.route('/mortgage')
def mortgage():
    return render_template('accounts/mortgage.html')

@accounts_bp.route('/<int:account_id>')
def account_detail(account_id):
    accounts_csv_path = os.path.join(current_app.root_path, "..", "csvFiles", "accounts.csv")
    
    try:
        accounts_df = pd.read_csv(accounts_csv_path)
        account_row = accounts_df[accounts_df["AccountID"] == account_id]
        if account_row.empty:
            flash("Account not found.", "danger")
            return redirect(url_for("dashboard.user_dashboard"))

        account = account_row.iloc[0].to_dict()
    except Exception as e:
        flash("Error retrieving account details.", "danger")
        return redirect(url_for("dashboard.user_dashboard"))
    
    return render_template("accounts/account_detail.html", account=account)
