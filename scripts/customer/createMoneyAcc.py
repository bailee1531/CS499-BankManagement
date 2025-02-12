# Bailee Segars
from datetime import date
import pandas as pd
import random

# Deposit money to an account
# Account must be a checking account and have sufficient funds
# Only employees can directly deposit. Customer making transfers can indirectly deposit
# custID: Customer ID passed from web page
# accType: Account type customer selected to create on web page
# depositAmnt: How much money the user wants to initially deposit. Can be 0
def createAccount(custID, accType, depositAmnt):
    # Creates dataframe with current csv data
    accID = random.randint(200, 999) # generates a random ID
    accPath = 'csvFiles/accounts.csv'
    accInfo = pd.read_csv(accPath)

    newAccRow = {'AccountID': accID, 'CustomerID': custID, 'AccountType': accType, 'CurrBal': depositAmnt,'DateOpened': date.today()}
    accInfo.loc[len(accInfo)] = newAccRow
    accInfo.to_csv(accPath, index=False)