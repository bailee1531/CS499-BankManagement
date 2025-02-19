# Sierra Yerges
import pandas as pd
import os
from decimal import Decimal
from transactionLog import generate_transaction_ID

def payCreditCard(customerID: int, creditAccID: int, paymentAccID: int, amount: Decimal) -> dict:
    """
    Allows users to make payments towards their credit card balance.

    Parameters
    ----------
    customerID : int
        The Customer ID making the payment.
    creditAccID : int
        The Account ID of the credit card account.
    paymentAccID : int
        The Account ID from which the payment is being made.
    amount : Decimal
        The amount to pay towards the credit card.

    Returns
    -------
    dict
        - If payment is successful:
          {"status": "success", "message": "Payment of ${amount} made to Credit Card {creditAccID}."}
        - If payment fails (account not found, insufficient funds, invalid amount, etc.):
          {"status": "error", "message": "Failure reason"}
    """
    # Get absolute paths for accounts and logs
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    logPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))

    # Load account and log data
    accountsData = pd.read_csv(accountsPath)
    logData = pd.read_csv(logPath)

    # Locate the payment and credit card accounts
    creditIndex = accountsData[
        (accountsData['CustomerID'] == customerID) &
        (accountsData['AccountID'] == creditAccID) &
        (accountsData['AccountType'] == 'CreditCard')
    ].index

    paymentIndex = accountsData[
        (accountsData['CustomerID'] == customerID) &
        (accountsData['AccountID'] == paymentAccID)
    ].index

    # Validate account existence
    if creditIndex.empty:
        return {"status": "error", "message": f"Credit card account {creditAccID} not found for Customer {customerID}."}
    if paymentIndex.empty:
        return {"status": "error", "message": f"Payment source account {paymentAccID} not found for Customer {customerID}."}

    # Prevent users from paying a credit card with another credit card
    if 5000 <= paymentAccID <= 9999:
        return {"status": "error", "message": "Cannot use a credit card account to pay off another credit card."}

    # Ensure valid payment amount
    if amount <= Decimal('0.00'):
        return {"status": "error", "message": "Payment amount must be greater than zero."}

    # Get balances and convert to Decimal for accuracy
    creditBalance = Decimal(accountsData.at[creditIndex[0], 'CurrBal'])
    paymentBalance = Decimal(accountsData.at[paymentIndex[0], 'CurrBal'])

    # Ensure the payment account has enough funds
    if paymentBalance < amount:
        return {"status": "error", "message": "Insufficient funds in payment account."}

    # Deduct payment from source account and apply to credit card
    accountsData.at[paymentIndex[0], 'CurrBal'] = paymentBalance - amount
    accountsData.at[creditIndex[0], 'CurrBal'] = max(Decimal('0.00'), creditBalance - amount)  # Prevent negative balance

    # Generate transaction ID and log the transaction
    transactionID = generate_transaction_ID(logData)
    newLog = {
        'AccountID': creditAccID,
        'CustomerID': customerID,
        'TransactionType': 'CreditCardPayment',
        'Amount': float(amount),
        'TransactionID': transactionID
    }
    logData.loc[len(logData)] = newLog
    logData.to_csv(logPath, index=False)

    # Save updated balances
    accountsData.to_csv(accountsPath, index=False)

    return {"status": "success", "message": f"Payment of ${amount} made to Credit Card {creditAccID}."}
