
import os
import pandas as pd
from flask import Blueprint, render_template, session, flash, redirect, url_for, current_app

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard", template_folder="templates")

@dashboard_bp.route('/')
def user_dashboard():
    if "customerID" not in session:
        flash("You must be logged in to view your dashboard", "danger")
        return redirect(url_for("public.login"))

    customer_id = session["customerID"]
    accounts_csv_path = os.path.join(current_app.root_path, "..", "csvFiles", "accounts.csv")

    try:
        accounts_df = pd.read_csv(accounts_csv_path)
        customer_accounts_df = accounts_df[accounts_df["CustomerID"] == customer_id]

        accounts_list = []
        for _, row in customer_accounts_df.iterrows():
            accounts_list.append({
                "account_id": row["AccountID"],
                "account_type": row["AccountType"],
                "curr_bal": row["CurrBal"],
            })
    except Exception as e:
        flash("Error retrieving account information.", "danger")
        accounts_list = []

    return render_template("dashboard/user_dashboard.html", accounts=accounts_list)
