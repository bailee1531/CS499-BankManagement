# Sierra Yerges
import pandas as pd
import os
from decimal import Decimal
from datetime import date
from transactionLog import generate_transaction_ID

def scheduleLoanPayment(customerID: int, loanID: int, amount: Decimal, dueDate: str, paymentAccID: int) -> dict:
    """
    Schedules a loan payment for a home mortgage account using the APR from accounts.csv.

    Parameters
    ----------
    customerID : int
        The Customer ID scheduling the payment.
    loanID : int
        The Loan ID for which the payment is being scheduled.
    amount : Decimal
        The amount to pay.
    dueDate : str
        The due date for the payment in YYYY-MM-DD format.
    paymentAccID : int
        The Account ID from which the payment will be made.

    Returns
    -------
    dict
        - If scheduling is successful:
          {"status": "success", "message": "Loan payment scheduled successfully."}
        - If scheduling fails:
          {"status": "error", "message": "Failure reason."}
    """
    # Get absolute paths for CSV files
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    customersPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/customers.csv'))
    loanPaymentsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/loanPayments.csv'))

    # Load accounts and customers data
    accountsData = pd.read_csv(accountsPath)
    customersData = pd.read_csv(customersPath)

    # Validate loan existence and customer ownership
    loanRecord = accountsData[
        (accountsData['AccountID'] == loanID) &
        (accountsData['CustomerID'] == customerID) &
        (accountsData['AccountType'] == 'Mortgage Loan')
    ]
    if loanRecord.empty:
        return {"status": "error", "message": f"Mortgage loan {loanID} not found for Customer {customerID}."}

    # Validate payment account existence
    paymentAccount = accountsData[
        (accountsData['CustomerID'] == customerID) &
        (accountsData['AccountID'] == paymentAccID)
    ]
    if paymentAccount.empty:
        return {"status": "error", "message": f"Payment source account {paymentAccID} not found for Customer {customerID}."}

    # Validate payment amount
    if amount <= Decimal('0.00'):
        return {"status": "error", "message": "Payment amount must be greater than zero."}

    # Validate due date format
    try:
        date.fromisoformat(dueDate)
    except ValueError:
        return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}

    # Load or create loan payments DataFrame
    if os.path.exists(loanPaymentsPath):
        loanPaymentsData = pd.read_csv(loanPaymentsPath)
    else:
        loanPaymentsData = pd.DataFrame(columns=['LoanPayID', 'LoanID', 'SchedPayDate', 'PayAmount', 'APR', 'PaidAmount', 'PaidDate'])

    # Retrieve APR from accounts data
    apr = loanRecord.iloc[0]['APR']

    # Generate transaction ID and LoanPayID
    transactionID = generate_transaction_ID(loanPaymentsData)
    loanPayID = len(loanPaymentsData) + 1

    # Append new loan payment to the DataFrame
    newLoanPayment = {
        'LoanPayID': loanPayID,
        'LoanID': loanID,
        'SchedPayDate': dueDate,
        'PayAmount': Decimal(amount).quantize(Decimal('0.00')),
        'APR': apr,
        'PaidAmount': "0.00",
        'PaidDate': ""
    }
    loanPaymentsData.loc[len(loanPaymentsData)] = newLoanPayment
    loanPaymentsData.to_csv(loanPaymentsPath, index=False)

    return {"status": "success", "message": "Loan payment scheduled successfully."}

def processScheduledLoanPayments() -> dict:
    """
    Processes all scheduled loan payments due today or earlier, updating PaidAmount and PaidDate.

    Returns
    -------
    dict
        - Returns status and message indicating the result of the processing.
    """
    # Get absolute paths for CSV files
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    loanPaymentsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/loanPayments.csv'))
    logPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))

    # Check if there are scheduled loan payments
    if not os.path.exists(loanPaymentsPath):
        return {"status": "error", "message": "No scheduled loan payments to process."}

    # Load data
    accountsData = pd.read_csv(accountsPath)
    loanPaymentsData = pd.read_csv(loanPaymentsPath)
    logData = pd.read_csv(logPath) if os.path.exists(logPath) else pd.DataFrame(columns=['AccountID', 'CustomerID', 'TransactionType', 'Amount', 'TransactionID'])

    today = date.today()
    remainingPayments = []

    # Process due payments
    for index, payment in loanPaymentsData.iterrows():
        dueDate = date.fromisoformat(payment['SchedPayDate'])
        if dueDate <= today and payment['PaidAmount'] == "0.00":
            accIndex = accountsData[accountsData['AccountID'] == payment['LoanID']].index

            # Validate payment account existence
            if accIndex.empty:
                remainingPayments.append(payment)
                continue

            balance = Decimal(accountsData.at[accIndex[0], 'CurrBal'])
            amount = Decimal(payment['PayAmount'])

            # Process payment if sufficient funds
            if balance >= amount:
                accountsData.at[accIndex[0], 'CurrBal'] = balance - amount
                loanPaymentsData.at[index, 'PaidAmount'] = str(amount)
                loanPaymentsData.at[index, 'PaidDate'] = today.isoformat()

                # Log processed payment
                newLog = {
                    'AccountID': payment['LoanID'],
                    'CustomerID': accountsData.at[accIndex[0], 'CustomerID'],
                    'TransactionType': 'LoanPayment',
                    'Amount': Decimal(amount).quantize(Decimal('0.00')),
                    'TransactionID': generate_transaction_ID(logData)
                }
                logData.loc[len(logData)] = newLog
            else:
                remainingPayments.append(payment)
        else:
            remainingPayments.append(payment)

    # Save updates
    accountsData.to_csv(accountsPath, index=False)
    loanPaymentsData.to_csv(loanPaymentsPath, index=False)
    logData.to_csv(logPath, index=False)

    return {"status": "success", "message": "Scheduled loan payments processing completed."}
