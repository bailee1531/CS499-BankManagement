# Spring 2025 Authors: Bailee Segars, Sierra Yerges, Braden Doty
import pandas as pd
from decimal import Decimal
import os

def accrue_interest(accType):
    """
    Calculates interest accrued on balance in savings accounts and money market accounts, then updates the account information in the csv.

    Savings accounts have a fixed 4.0% APY and compound monthly.

    Money Market accounts have a fixed 3.0% APY and compound daily.

    Parameters
    ----------
    accType: string {Savings, Money Market}
        Account type to determine APY and compound rate.
    """
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    accInfo = pd.read_csv(accPath)
    accInfo['CurrBal'] = accInfo['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))

    monthlyRate = ((Decimal(0.04)/Decimal(12)) + 1) if accType == 'Savings' else ((Decimal(0.03)/Decimal(12)) + 1)

    accInfo['CurrBal'] = accInfo.apply(lambda row: Decimal(row['CurrBal']*monthlyRate).quantize(Decimal('0.00')) if row['AccountType'] == accType else row['CurrBal'], axis=1)
    accInfo.to_csv(accPath, index=False)