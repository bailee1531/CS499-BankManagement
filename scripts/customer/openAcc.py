# Spring 2025 Authors: Bailee Segars, Sierra Yerges
from datetime import date
from decimal import Decimal
import pandas as pd
import random
import os

def generate_account_ID(accInfo):
    """
    Generates a unique account ID for each new account.

    Parameters
    ----------
    accInfo: dataframe
        Dataframe of log information from accounts.csv.

    Returns
    -------
    accID: int
        ID associated with the account.
    """
    accID = random.randint(200, 999) # generates a random ID
    if accID not in accInfo:
        return accID
    generate_account_ID(accInfo)


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
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)

    log_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/logs.csv'))
    log_df = pd.read_csv(log_path)

    if depositAmnt >= 0:
        accID = generate_account_ID(accInfo)

        # Determine APR based on account type
        apr = None
        if accType.lower() == 'Savings':
            apr = 4.0
        elif accType.lower() == 'Money Market':
            apr = 3.0

        newAccRow = {'AccountID': accID,
                    'CustomerID': custID,
                    'AccountType': accType,
                    'CurrBal': Decimal(depositAmnt).quantize(Decimal('0.00')),
                    'DateOpened': date.today(),
                    'CreditLimit': None,
                    'APR': apr}
        accInfo.loc[len(accInfo)] = newAccRow
        accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        accInfo.to_csv(accPath, index=False)

        log_id = random.randint(1299, 5999)
        while log_id in log_df['LogID'].values:
            log_id = random.randint(1299, 5999)

        newLog = {'LogID': log_id, 'UserID': custID, 'LogMessage': f'Opened {accType} Account'}
        log_df.loc[len(log_df)] = newLog

        log_df.to_csv(log_path, index=False)

        return {"status": "success", "message": f"{accType} account {accID} created."}
    else:
        return {"status": "error", "message": "Cannot open an account with a negative deposit."}