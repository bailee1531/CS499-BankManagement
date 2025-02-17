# Bailee Segars
import pandas as pd
from decimal import Decimal
import os

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
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)

    if accID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Source account {accID} not found."}

    custIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[custIndex, 'AccountType']
    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    currentBal = Decimal(accInfo.at[custIndex, 'CurrBal'])

    # Account type and balance validation
    if accType != 'Checking' and accType != 'Savings':
        return {"status": "error", "message": f"Incorrect account type selected. Cannot withdraw {amount} from account {accID}."}
    if amount > currentBal:
        return {"status": "error", "message": f"Insufficient funds. Cannot withdraw {amount} from account {accID}."}

    # Completes withdrawal and updates csv file
    currentBal -= Decimal(amount).quantize(Decimal('0.00'))
    accInfo.at[custIndex, 'CurrBal'] = Decimal(currentBal).quantize(Decimal('0.00'))
    accInfo.to_csv(accPath, index=False)

    return {"status": "success", "message": f"Withdrew {amount} from account {accID}."}