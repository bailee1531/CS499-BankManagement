# Sierra Yerges
from scripts.transactionLog import generate_transaction_ID
import pandas as pd
from datetime import date
from decimal import Decimal
import os

def calculateCreditInterest():
    """
    Calculates monthly interest on unpaid balances for all credit card
    & home mortgage loan accounts, using APR values assigned during account creation.

    Returns
    -------
    dict
        A dictionary containing the status and message.
        {"status": "success", "message": f"Interest of ${interest} applied to AccountID {account['AccountID']}."}

        Updates 'accounts.csv' with new balances including accrued interest.
    """
    # Get absolute path for accounts.csv
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))

    # Load account data
    accountsData = pd.read_csv(accountsPath)
    accountsData['CurrBal'] = accountsData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    # Load transaction data
    transData = pd.read_csv(transPath)

    # Identify all credit accounts (credit cards and home mortgage loans)
    creditAccounts = accountsData[(accountsData['AccountType'] == 'Credit Card') | (accountsData['AccountType'] == 'Mortgage Loan')]

    results = []

    # Apply interest calculation for each account
    for index, account in creditAccounts.iterrows():
        unpaidBalance = Decimal(str(account['CurrBal']))
        apr = Decimal(str(account['APR']))
        accID = account['AccountID']
        custID = account['CustomerID']

        if unpaidBalance > 0:
            # Monthly interest rate from APR
            monthlyInterestRate = apr / Decimal(100) / Decimal(12)

            # Calculate interest
            interest = (unpaidBalance * monthlyInterestRate).quantize(Decimal('0.00'))

            # Update the balance for the specific account
            updatedBalance = (unpaidBalance + interest).quantize(Decimal('0.00'))
            accountsData.at[index, 'CurrBal'] = updatedBalance

            # Generate transaction ID and log interest accrual
            transactionID = generate_transaction_ID(transData)
            newLog = {
                'TransactionID': transactionID,
                'AccountID': accID,
                'TransactionType': 'Interest Earned',
                'Amount': Decimal(interest).quantize(Decimal('0.00')),
                'TransDate': date.today()
            }
            transData.loc[len(transData)] = newLog

            # Log result for each account
            results.append({"status": "success", "message": f"Interest of ${interest} applied to AccountID {account['AccountID']}."})

    # Save updated balances
    accountsData.to_csv(accountsPath, index=False)
    # Log updated balances
    transData.to_csv(transPath, index=False)

    return results
