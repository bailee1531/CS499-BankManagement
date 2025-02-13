# Bailee Segars
import pandas as pd
from decimal import *

def withdraw(accID, amount) -> dict:
    """
    Withdraw money from an account. Account must be a checking or savings account and have sufficient funds.
    
    Only employees can directly withdraw. Customer making transfers can indirectly withdraw.

    Parameters
    ----------
    accID: int
        Account ID passed from account selected on web page.
    amount: decimal
        User-defined amount to withdraw.

    Returns
    -------
    dict
        A dictionary containing the status and message.

        - If the account is not a checking or savings account:\n
        {"status": "error", "message": f"Incorrect account type selected. Cannot withdraw {amount} from account {accID}."}

        - If withdrawal amount requested is larger than available balance:\n
        {"status": "error", "message": f"Insufficient funds. Cannot withdraw {amount} from account {accID}."}
    """
    # Creates dataframe with csv data
    # Gets row for requested customer
    accPath = 'csvFiles/accounts.csv'
    accInfo = pd.read_csv(accPath)
    custIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[custIndex, 'AccountType']
    currentBal = accInfo.at[custIndex, 'CurrBal']

    # Account type and balance validation
    if accType != 'Checking' and accType != 'Savings':
        return {"status": "error", "message": f"Incorrect account type selected. Cannot withdraw {amount} from account {accID}."}
    if amount > currentBal:
        return {"status": "error", "message": f"Insufficient funds. Cannot withdraw {amount} from account {accID}."}

    # Completes withdrawal and updates csv file
    Decimal(currentBal) -= Decimal(amount)
    accInfo.at[custIndex, 'CurrBal'] = Decimal(currentBal)
    accInfo.to_csv(accPath, index=False)