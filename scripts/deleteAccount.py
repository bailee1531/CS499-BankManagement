# Sierra Yerges
import pandas as pd
import os

def deleteAcc(custID: int, accID: int) -> dict:
    """
    Deletes an account if the balance is zero.

    Parameters
    ----------
    custID : int
        The Customer ID associated with the account.
    accID : int
        The Account ID of the account to be deleted.

    Returns
    -------
    dict
        A dictionary containing the status and a message.

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
    """
    # Get absolute path for accounts.csv
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    
    # Load account data
    accInfo = pd.read_csv(accPath)

    # Find the account in the dataset
    accIndex = accInfo[(accInfo['CustomerID'] == custID) & (accInfo['AccountID'] == accID)].index

    # Check if the account exists
    if accIndex.empty:
        return {"status": "error", "message": f"Account {accID} not found for Customer {custID}."}

    # Check if the account balance is zero
    if accInfo.loc[accIndex, 'CurrBal'].values[0] == 0:
        accInfo.drop(accIndex, inplace=True)
        accInfo.to_csv(accPath, index=False)
        return {"status": "success", "message": f"Account {accID} successfully deleted."}
    else:
        return {"status": "error", "message": f"Account {accID} cannot be deleted because it has a non-zero balance."}
    