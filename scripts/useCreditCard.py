# Sierra Yerges
import pandas as pd
from decimal import Decimal
from datetime import date
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.transactionLog import generate_transaction_ID

def useCreditCard(accID, amount) -> dict:
    """
    Use the credit card for purchases. Increases the amount owed (negative balance).

    Parameters
    ----------
    accID : int
        The credit card account ID being used.
    amount : Decimal
        The purchase amount.

    Returns
    -------
    dict
        Result message indicating success or failure.
    """
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))

    accInfo = pd.read_csv(accPath)
    transInfo = pd.read_csv(transPath)

    if accID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Credit card account {accID} not found."}

    accIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[accIndex, 'AccountType']

    if accType != 'Credit Card':
        return {"status": "error", "message": f"Account {accID} is not a credit card."}

    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    accInfo['CreditLimit'] = accInfo['CreditLimit'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    currentBal = Decimal(accInfo.at[accIndex, 'CurrBal'])
    creditLimit = Decimal(accInfo.at[accIndex, 'CreditLimit'])

    # Check if new balance exceeds credit limit
    proposed_balance = currentBal - Decimal(amount).quantize(Decimal('0.00'))
    if abs(proposed_balance) > creditLimit:
        return {"status": "error", "message": f"Purchase exceeds credit limit for account {accID}."}

    # Apply the charge (increase owed amount)
    newBal = currentBal - Decimal(amount).quantize(Decimal('0.00'))
    accInfo.at[accIndex, 'CurrBal'] = newBal
    accInfo.to_csv(accPath, index=False)

    # Log the transaction
    transactionID = generate_transaction_ID(transInfo)
    newTrans = {
        'TransactionID': transactionID,
        'AccountID': accID,
        'TransactionType': 'Credit Card Charge',
        'Amount': Decimal(amount).quantize(Decimal('0.00')),
        'TransDate': date.today()
    }

    transInfo.loc[len(transInfo)] = newTrans
    transInfo['Amount'] = transInfo['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    transInfo.to_csv(transPath, index=False)

    return {"status": "success", "message": f"Charged ${amount} to credit card account {accID}."}
