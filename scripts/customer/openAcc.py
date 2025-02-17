# Bailee Segars
from datetime import date
from decimal import Decimal
import pandas as pd
import random
import os

def open_account(custID, accType, depositAmnt):
    """
    Allows customers to open an account (checking, savings, money market, etc).

    Parameters
    ----------
    custID: int
        Customer ID passed from the GUI
    accType: string
        Account type customer selected to create
    depositAmnt: decimal
        Amount of money user wants to initially deposit. Can be 0
    """
    # Creates dataframe with current csv data
    accID = random.randint(200, 999) # generates a random ID
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)
    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))

    newAccRow = {'AccountID': accID, 'CustomerID': custID, 'AccountType': accType, 'CurrBal': Decimal(depositAmnt).quantize(Decimal('0.00')),'DateOpened': date.today()}
    accInfo.loc[len(accInfo)] = newAccRow
    accInfo.to_csv(accPath, index=False)

open_account(754, 'Savings', 1200)