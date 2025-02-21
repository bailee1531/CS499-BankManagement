# Bailee Segars
from transactionLog import generate_transaction_ID
from decimal import Decimal
import pandas as pd
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
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    logPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))
    accInfo = pd.read_csv(accPath)
    logInfo = pd.read_csv(logPath)

    if accID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Source account {accID} not found."}
    
    accIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[accIndex, 'AccountType']
    custID = accInfo.at[accIndex, 'CustomerID']
    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    currentBal = Decimal(accInfo.at[accIndex, 'CurrBal'])

    # Account type and balance validation
    if accType != 'Checking' and accType != 'Savings':
        return {"status": "error", "message": f"Incorrect account type selected. Cannot deposit {amount} to account {accID}."}

    # Completes withdrawal and updates csv file
    currentBal += Decimal(amount).quantize(Decimal('0.00'))
    accInfo.at[accIndex, 'CurrBal'] = Decimal(currentBal).quantize(Decimal('0.00'))
    accInfo.to_csv(accPath, index=False)

    transactionID = generate_transaction_ID(logInfo)
    newLog = {'AccountID': accID, 'CustomerID': custID, 'TransactionType': 'Deposit', 'Amount': amount,'TransactionID': transactionID}
    logInfo.loc[len(accInfo)] = newLog
    logInfo.to_csv(logPath, index=False)

    return {"status": "success", "message": f"{amount} deposited to account {accID}."}
