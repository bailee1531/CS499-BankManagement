# Sierra Yerges
import pandas as pd
import os
from scripts.transactionLog import generate_transaction_ID

def deleteAcc(custID: int, accID: int) -> dict:
    """
    Deletes an account if the balance is zero and logs the deletion.

    Parameters
    ----------
    custID : int
        The Customer ID associated with the account.
    accID : int
        The Account ID of the account to be deleted.

    Returns
    -------
    dict
        - If the account does not exist:
          {"status": "error", "message": "Account {accID} not found for Customer {custID}."}
        - If the account balance is not zero:
          {"status": "error", "message": "Account {accID} cannot be deleted because it has a non-zero balance."}
        - If the account is successfully deleted:
          {"status": "success", "message": "Account {accID} successfully deleted."}
          
    Notes
    -----
    - The function reads from `accounts.csv` located in `../csvFiles/`.
    - Only accounts with a zero balance can be deleted.
    - If an account is deleted, the updated dataset is saved back to the CSV file.
    - A deletion log entry is created in `logs.csv` for tracking.
    """

    # Define file paths
    accPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/accounts.csv'))
    logPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/logs.csv'))

    # Load account data
    accInfo = pd.read_csv(accPath)
    
    # Ensure 'CurrBal' is treated as a numeric value for proper comparisons
    accInfo['CurrBal'] = pd.to_numeric(accInfo['CurrBal'], errors='coerce')

    # Ensure logs.csv exists and has required columns
    if os.path.exists(logPath) and os.stat(logPath).st_size > 0:
        logInfo = pd.read_csv(logPath)
    else:
        logInfo = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

    # Find the account in the dataset
    accIndex = accInfo[(accInfo['CustomerID'] == custID) & (accInfo['AccountID'] == accID)].index

    # Check if the account exists
    if accIndex.empty:
        return {"status": "error", "message": f"Account {accID} not found for Customer {custID}."}

    # Check if the account balance is zero
    if accInfo.loc[accIndex, 'CurrBal'].values[0] != 0:
        return {"status": "error", "message": f"Account {accID} cannot be deleted because it has a non-zero balance."}

    # Generate a transaction ID
    transactionID = generate_transaction_ID(logInfo)

    # Log account deletion
    log_entry = pd.DataFrame([{
        "AccountID": accID,
        "CustomerID": custID,
        "TransactionType": "Account Deleted",
        "Amount": "0.00",  # No money involved
        "TransactionID": transactionID
    }])

    # Append log entry and save
    logInfo = pd.concat([logInfo, log_entry], ignore_index=True)
    logInfo.to_csv(logPath, index=False)

    # Remove account from dataset
    accInfo.drop(accIndex, inplace=True)
    accInfo.to_csv(accPath, index=False)

    return {"status": "success", "message": f"Account {accID} successfully deleted."}
