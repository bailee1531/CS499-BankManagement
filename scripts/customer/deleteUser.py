# Spring 2025 Authors: Sierra Yerges, Bailee Segars
import os
import random
import pandas as pd
from Crypto.PublicKey import ECC

# Define CSV file paths
customers_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/customers.csv'))
employees_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/employees.csv'))
persons_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/persons.csv'))
accounts_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))
bills_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/bills.csv'))
log_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/logs.csv'))


def delete_user_button_pressed(user_type: str, user_id: int, password: str = None, is_admin: bool = False) -> dict:
    """
    Deletes a customer or teller account if they have no active accounts or bills.
    Admins can bypass password checks. Associated .pem key file is deleted if present.

    Parameters
    ----------
    user_type : str
        'Customer', 'Teller', or 'Admin'.
    user_id : int
        ID of the user to delete.
    password : str, optional
        Password to decrypt the private key (required for non-admins).
    is_admin : bool
        Whether the deletion is performed by an admin.

    Returns
    -------
    dict
        A result dictionary with status and message.
    """

    # Load CSVs
    try:
        persons_df = pd.read_csv(persons_path)
        accounts_df = pd.read_csv(accounts_path)
        bills_df = pd.read_csv(bills_path)
        log_df = pd.read_csv(log_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to load required files: {e}"}

    # Check for active accounts or bills
    if not accounts_df[accounts_df['CustomerID'] == user_id].empty \
       or not bills_df[bills_df['CustomerID'] == user_id].empty:
        return {"status": "error", "message": "User cannot be deleted. Active accounts or bills still exist."}

    # Password verification (non-admins only)
    if not is_admin:
        key_path = f"{user_id}privatekey.pem"
        if not os.path.exists(key_path):
            return {"status": "error", "message": "Private key file not found."}
        try:
            with open(key_path, 'rt') as f:
                ECC.import_key(f.read(), passphrase=password)
        except Exception:
            return {"status": "error", "message": "Incorrect password. Private key decryption failed."}

    # Remove from persons.csv
    persons_df = persons_df[persons_df['ID'] != user_id]
    try:
        persons_df.to_csv(persons_path, index=False)
    except Exception as e:
        return {"status": "error", "message": f"Failed to update persons.csv: {e}"}

    # Remove from customer or employee file
    if user_type == 'Customer':
        try:
            cust_df = pd.read_csv(customers_path)
            cust_df = cust_df[cust_df['CustomerID'] != user_id]
            cust_df.to_csv(customers_path, index=False)

            accounts_df = accounts_df[accounts_df['CustomerID'] != user_id]
            accounts_df.to_csv(accounts_path, index=False)
        except Exception as e:
            return {"status": "error", "message": f"Failed to update customers.csv: {e}"}
    elif user_type == 'Teller':
        try:
            emp_df = pd.read_csv(employees_path)
            emp_df = emp_df[emp_df['EmployeeID'] != user_id]
            emp_df.to_csv(employees_path, index=False)
        except Exception as e:
            return {"status": "error", "message": f"Failed to update employees.csv: {e}"}

    # Delete PEM key file
    pem_path = f"{user_id}privatekey.pem"
    if os.path.exists(pem_path):
        try:
            os.remove(pem_path)
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete PEM file: {e}"}
    
    log_id = random.randint(1299, 5999)
    while log_id in log_df['LogID'].values:
        log_id = random.randint(1299, 5999)

    newLog = {'LogID': log_id, 'UserID': user_id, 'LogMessage': 'Deleted User Account'}
    log_df.loc[len(log_df)] = newLog

    log_df.to_csv(log_path, index=False)

    return {"status": "success", "message": f"{user_type} account {user_id} successfully deleted."}
