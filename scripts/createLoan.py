# Spring 2025 Authors: Sierra Yerges, Bailee Segars, Braden Doty
import pandas as pd
import random
import os
from decimal import Decimal
from datetime import date, timedelta
from scripts.billPayment import scheduleBillPayment

def createMortgageLoanAccount(customerID: int, loanAmount: Decimal, termYears: int) -> dict:
    """
    Creates a home mortgage loan account and schedules the first monthly payment bill.

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
    # Get absolute path for logs.csv file
    logPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))

    # Load account data
    accountsData = pd.read_csv(accountsPath)
    customerData = pd.read_csv(customerPath)
    logData = pd.read_csv(logPath)

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
        "CurrBal": -Decimal(loanAmount).quantize(Decimal('0.00')),
        "DateOpened": startDate,
        "CreditLimit": None,
        "APR": interestRate
    }

    # Append the new account details to the DataFrame
    newLoanDf = pd.DataFrame([newLoanAccount], columns=accountsData.columns)
    if accountsData.empty:
        accountsData = newLoanDf
    else:
        accountsData = pd.concat([accountsData, newLoanDf], ignore_index=True)
    accountsData['CurrBal'] = accountsData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    accountsData['CreditLimit'] = accountsData['CreditLimit'].apply(
        lambda x: Decimal(str(x)).quantize(Decimal('0.00')) if pd.notna(x) and str(x) not in ["", "None"] else None
    )
    accountsData.to_csv(accountsPath, index=False)

    log_id = random.randint(1299, 5999)
    while log_id in logData['LogID'].values:
        log_id = random.randint(1299, 5999)

    newLog = {'LogID': log_id, 'UserID': customerID, 'LogMessage': 'Opened a Mortgage Loan Account'}
    logData.loc[len(logData)] = newLog
    logData.to_csv(logPath, index=False)

    # Calculate monthly payment (principal + interest)
    monthly_interest_rate = Decimal(interestRate) / Decimal(100) / Decimal(12)
    total_payments = termYears * 12
    monthly_payment = (
        Decimal(loanAmount) * 
        (monthly_interest_rate * (1 + monthly_interest_rate) ** total_payments) / 
        ((1 + monthly_interest_rate) ** total_payments - 1)
    ).quantize(Decimal('0.01'))
    
    # Schedule the first monthly payment bill
    first_bill_due_date = (date.today() + timedelta(days=30)).isoformat()
    
    bill_result = scheduleBillPayment(
        customerID=customerID,
        payeeName="Evergreen Bank Mortgage",
        payeeAddress="Somewhere In The World",
        amount=monthly_payment,
        dueDate=first_bill_due_date,
        paymentAccID=accountID,
        minPayment=monthly_payment,  # Minimum payment is the monthly payment
        billType='Mortgage',
        isRecurring=1  # Mortgage bills are recurring
    )
    
    # Return success message with account details
    return {"status": "success", "message": f"Mortgage loan account {accountID} created with an interest rate of {interestRate}% for {termYears} years. Monthly payment: ${monthly_payment}. First payment due on {first_bill_due_date}."}