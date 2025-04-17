# Bailee Segars
from scripts.transactionLog import generate_transaction_ID
from decimal import Decimal
from datetime import date
import pandas as pd
import os

def directDeposit(accID, amount) -> dict:
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
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))
    accInfo = pd.read_csv(accPath)
    transInfo = pd.read_csv(transPath)

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

    # Generate transaction ID and log the transaction
    transactionID = generate_transaction_ID(transInfo)
    newTrans = {
        'TransactionID': transactionID,
        'AccountID': accID,
        'TransactionType': 'Direct Deposit',
        'Amount': Decimal(amount).quantize(Decimal('0.00')),
        'TransDate': date.today()
    }

    transInfo.loc[len(accInfo)] = newTrans
    transInfo.to_csv(transPath, index=False)

    return {"status": "success", "message": f"{amount} deposited to account {accID}."}

def deposit(accID, amount) -> dict:
    """
    Deposit money into an account. Function to transfer funds.
    
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
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))
    accInfo = pd.read_csv(accPath)
    transInfo = pd.read_csv(transPath)

    if accID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Destination account {accID} not found."}
    
    accIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[accIndex, 'AccountType']
    custID = accInfo.at[accIndex, 'CustomerID']
    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    currentBal = Decimal(accInfo.at[accIndex, 'CurrBal'])

    # Account type and balance validation
    if accType not in ['Checking', 'Savings', 'Credit Card', 'Mortgage Loan']:
        return {"status": "error", "message": f"Incorrect account type selected. Cannot deposit {amount} to account {accID}."}

    # Completes deposit and updates csv file
    if accType in ['Credit Card', 'Mortgage Loan']:
        if accType == 'Credit Card':
            transaction_type = 'Payment to Credit Card'
        else:
            transaction_type = 'Payment to Mortgage Loan'
    else:
        transaction_type = 'Deposit to account'
    
    currentBal += Decimal(amount).quantize(Decimal('0.00'))
    accInfo['CreditLimit'] = accInfo['CreditLimit'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    accInfo.at[accIndex, 'CurrBal'] = Decimal(currentBal).quantize(Decimal('0.00'))
    accInfo.to_csv(accPath, index=False)

    # Generate transaction ID and log the transaction
    transactionID = generate_transaction_ID(transInfo)
    newTrans = {
        'TransactionID': transactionID,
        'AccountID': accID,
        'TransactionType': transaction_type,
        'Amount': Decimal(amount).quantize(Decimal('0.00')),
        'TransDate': date.today()
    }

    transInfo.loc[len(transInfo)] = newTrans
    transInfo.to_csv(transPath, index=False)

    return {"status": "success", "message": f"{amount} deposited to account {accID}."}