# Sierra Yerges
import pandas as pd
import random
import os
from decimal import Decimal
from datetime import date, timedelta

def createMortgageLoanAccount(customerID: int, loanAmount: Decimal, termYears: int) -> dict:
    """
    Creates a home mortgage loan account using APRRangeID for mortgage rate range
    and stores it in accounts.csv.

    Parameters
    ----------
    customerID : int
        The Customer ID for whom the mortgage loan account is being created.
    loanAmount : Decimal
        The total loan amount requested by the customer.
    termYears : int
        The loan term in years.

    Returns
    -------
    dict
        - If account creation is successful:
          {"status": "success", "message": "Mortgage loan account {accountID} created with an interest rate of {interestRate}% for {termYears} years."}
        - If the customer ID is invalid:
          {"status": "error", "message": "Customer {customerID} not found."}
    """
    # Get absolute path for accounts.csv
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    # Get absolute path for customer.csv file
    customerPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/customers.csv'))

    # Load account data
    accountsData = pd.read_csv(accountsPath)
    customerData = pd.read_csv(customerPath)

    # Validate customer existence
    customerRow = customerData[customerData['CustomerID'] == customerID]
    if customerRow.empty:
        return {"status": "error", "message": f"Customer {customerID} not found."}

    # Define APR ranges based on APRRangeID
    apr_ranges = {
        1: (3.0, 4.0),
        2: (4.1, 5.5),
        3: (5.6, 6.5),
        4: (6.6, 7.5)
    }

    # Retrieve APRRangeID and select the corresponding APR range
    apr_range_id = customerRow.iloc[0]['APRRangeID']
    apr_range = apr_ranges.get(apr_range_id, (3.0, 4.0))
    interestRate = round(random.uniform(*apr_range), 2)

    # Generate a unique Account ID (between 10000-19999 for mortgage loans)
    accountID = random.randint(10000, 19999)
    while accountID in accountsData['AccountID'].values:
        accountID = random.randint(10000, 19999)

    # Set the start and end date for the loan
    startDate = date.today()
    endDate = startDate + timedelta(days=termYears * 365)

    # Create a dictionary with new mortgage loan account details
    newLoanAccount = {
        "AccountID": accountID,
        "CustomerID": customerID,
        "AccountType": "Mortgage Loan",
        "CurrBal": Decimal(loanAmount).quantize(Decimal('0.00')),
        "DateOpened": startDate,
        "CreditLimit": None,
        "APR": interestRate
    }

    # Append the new account details to the DataFrame
    accountsData = pd.concat([accountsData, pd.DataFrame([newLoanAccount])], ignore_index=True)
    accountsData.to_csv(accountsPath, index=False)

    return {"status": "success", "message": f"Mortgage loan account {accountID} created with an interest rate of {interestRate}% for {termYears} years."}
