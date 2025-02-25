# Sierra Yerges
import pandas as pd
import os

def calculateCreditCardInterest():
    """
    Calculates monthly interest on unpaid balances for all credit card accounts,
    using APR values assigned during account creation.

    Returns
    -------
    None
        Updates 'accounts.csv' with new balances including accrued interest.
    """
    # Get absolute path for accounts.csv
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))

    # Load account data
    accountsData = pd.read_csv(accountsPath)

    # Identify all credit card accounts
    creditCardAccounts = accountsData[accountsData['AccountType'] == 'Credit Card']

    for index, account in creditCardAccounts.iterrows():
        unpaidBalance = account['CurrBal']
        apr = account['APR'] if 'APR' in account and not pd.isna(account['APR']) else 25  # Default APR if missing

        if unpaidBalance > 0:
            # Monthly interest rate from APR
            monthlyInterestRate = apr / 100 / 12

            # Calculate and apply interest
            interest = unpaidBalance * monthlyInterestRate
            accountsData.at[index, 'CurrBal'] += round(interest, 2)

    # Save updated balances
    accountsData.to_csv(accountsPath, index=False)
