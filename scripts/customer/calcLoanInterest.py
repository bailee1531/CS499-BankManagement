# Sierra Yerges
import pandas as pd
import os
from decimal import Decimal
from datetime import date, timedelta

def calculateProRatedInterest(loanStartDate: str, currentBalance: Decimal, apr: Decimal) -> Decimal:
    """
    Calculates pro-rated monthly interest based on loan start date, APR, and current balance.

    Parameters
    ----------
    loanStartDate : str
        Date the loan was opened (YYYY-MM-DD).
    currentBalance : Decimal
        Outstanding balance at the end of the previous month.
    apr : Decimal
        Annual Percentage Rate of the loan.

    Returns
    -------
    Decimal
        Calculated monthly interest amount.
    """
    today = date.today()
    startDate = date.fromisoformat(loanStartDate)
    firstDayOfMonth = today.replace(day=1)
    lastDayOfPreviousMonth = firstDayOfMonth - timedelta(days=1)
    daysInMonth = lastDayOfPreviousMonth.day

    # Calculate active days for the first partial month
    if startDate.month == today.month and startDate.year == today.year:
        activeDays = (lastDayOfPreviousMonth - startDate).days + 1
        activeDays = max(activeDays, 0)
    else:
        activeDays = daysInMonth

    # Daily interest calculation
    dailyInterestRate = apr / Decimal('100') / Decimal('365')
    interest = (currentBalance * dailyInterestRate * Decimal(activeDays)).quantize(Decimal('0.00'))
    return interest

def calculateMonthlyLoanInterest():
    """
    Calculate monthly loan interest with pro-rated logic.

    """
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))

    if not os.path.exists(accountsPath):
        return {"status": "error", "message": "accounts.csv not found."}

    accountsData = pd.read_csv(accountsPath)
    mortgageLoans = accountsData[accountsData['AccountType'] == 'Mortgage Loan']
    totalInterestApplied = Decimal('0.00')

    # Apply interest calculation for each loan
    for index, loan in mortgageLoans.iterrows():
        previousBalance = Decimal(str(loan['CurrBal']))
        apr = Decimal(str(loan['APR']))
        startDate = loan['DateOpened']

        if previousBalance > 0:
            interest = calculateProRatedInterest(startDate, previousBalance, apr)
            accountsData.at[index, 'CurrBal'] = previousBalance + interest
            totalInterestApplied += interest

    # Save updated balances
    accountsData.to_csv(accountsPath, index=False)

    return {"status": "success", "message": f"Pro-rated monthly loan interest calculated and applied successfully. Total interest applied: ${totalInterestApplied}."}
