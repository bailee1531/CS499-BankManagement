# Bailee Segars
from transactionLog import generate_transaction_ID
from decimal import Decimal
import pandas as pd
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
        return {"status": "error", "message": f"Incorrect account type selected. Cannot withdraw {amount} from account {accID}."}
    if amount > currentBal:
        return {"status": "error", "message": f"Insufficient funds. Cannot withdraw {amount} from account {accID}."}

    # Completes withdrawal and updates csv file
    currentBal -= Decimal(amount).quantize(Decimal('0.00'))
    accInfo['CreditLimit'] = accInfo['CreditLimit'].apply(lambda x: f"{Decimal(str(x)):.2f}" if pd.notna(x) else "")
    accInfo.at[accIndex, 'CurrBal'] = Decimal(currentBal).quantize(Decimal('0.00'))
    accInfo.to_csv(accPath, index=False)

    transactionID = generate_transaction_ID(logInfo)
    newLogEntry = pd.DataFrame([{
        'AccountID': accID,
        'CustomerID': custID,
        'TransactionType': 'Withdrawal',
        'Amount': Decimal(amount).quantize(Decimal('0.00')),
        'TransactionID': transactionID
    }])

    newLogEntry.to_csv(logPath, index=False, mode='a', header=not os.path.exists(logPath))

    return {"status": "success", "message": f"Withdrew {amount} from account {accID}."}