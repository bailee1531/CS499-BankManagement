# Bailee Segars
import pandas as pd
from decimal import *
import os

def deposit(accID, amount) -> dict:
    """
    Deposit money into an account. Account must be a checking account.
    
    Only employees can directly deposit. Customers can perform indirect deposits by transferring funds.

    Parameters
    ----------
    accID: int
        Account ID passed from account selected on GUI.
    amount: decimal
        User-defined amount from GUI.

    Returns
    -------
    dict
        A dictionary containing the status and message.

        - If the account is not a checking or savings account:\n
        {"status": "error", "message": f"Incorrect account type selected. Cannot deposit {amount} to account {accID}."}
    """
    # Creates dataframe with csv data
    # Gets row for requested customer
    accPath = accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)
    custIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[custIndex, 'AccountType']
    currentBal = Decimal(accInfo.at[custIndex, 'CurrBal'])

    # Account type and balance validation
    if accType != 'Checking' and accType != 'Savings':
        return {"status": "error", "message": f"Incorrect account type selected. Cannot deposit {amount} to account {accID}."}

    # Completes withdrawal and updates csv file
    currentBal += Decimal(amount)
    accInfo.at[custIndex, 'CurrBal'] = Decimal(currentBal).quantize(Decimal('0.00'))
    accInfo.to_csv(accPath, index=False)

    return {"status": "success", "message": f"{amount} deposited to account {accID}."}