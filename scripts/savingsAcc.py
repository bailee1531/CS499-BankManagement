# Bailee Segars
import pandas as pd
from decimal import Decimal
import os

def accrue_interest():
    """
    Calculates interest accrued on balance in savings account, then updates the account information in the csv.

    Savings accounts have a fixed 4.0% APY and compound monthly.
    """
    monthlyRate = ((Decimal(0.04)/Decimal(12)) + 1)

    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)
    accInfo['CurrBal'] = accInfo.apply(lambda row: Decimal(row['CurrBal']*monthlyRate).quantize(Decimal('0.00')) if row['AccountType'] == 'Savings' else row['CurrBal'], axis=1)
    accInfo.to_csv(accPath)