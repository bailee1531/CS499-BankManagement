# Bailee Segars
import pandas as pd

# Deposit money to an account
# Account must be a checking account and have sufficient funds
# Only employees can directly deposit. Customer making transfers can indirectly deposit
# accID: Account ID passed from account selected on web page
# amount: Amount in text field on web page
def deposit(accID, amount):
    # Creates dataframe with csv data
    # Gets row for requested customer
    accPath = '../csvFiles/accounts.csv'
    accInfo = pd.read_csv(accPath)
    custIndex = accInfo.loc[accInfo['AccountID'] == accID].index[0]
    accType = accInfo.at[custIndex, 'AccountType']
    currentBal = accInfo.at[custIndex, 'CurrBal']

    message = ''

    # Account type and balance validation
    if accType != 'Checking' and accType != 'Savings':
        message = 'Cannot deposit to this account type. Please choose a checking or savings account.'
        exit()

    # Completes withdrawal and updates csv file
    currentBal += amount
    accInfo.at[custIndex, 'CurrBal'] = currentBal
    accInfo.to_csv(accPath, index=False)

    return message