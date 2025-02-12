# Bailee Segars
import pandas as pd

# Withdraw money from an account
# Account must be a checking account and have sufficient funds
# Only employees can perform withdrawal
# accID: Account ID passed from account selected on web page
# amount: Amount in text field on web page
def withdraw(accID, amount):
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
        message = 'Cannot perform withdrawal on this account type. Please choose a checking or savings account.'
        exit()
    if amount > currentBal:
        message = 'Insufficient funds.'
        exit()

    # Completes withdrawal and updates csv file
    currentBal -= amount
    accInfo.at[custIndex, 'CurrBal'] = currentBal
    accInfo.to_csv(accPath, index=False)

    return message
