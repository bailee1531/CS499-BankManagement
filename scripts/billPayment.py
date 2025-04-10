# Sierra Yerges
from scripts.transactionLog import generate_transaction_ID
import random
import pandas as pd
from decimal import Decimal
import os
from datetime import date, timedelta

def scheduleBillPayment(customerID: int, payeeName: str, payeeAddress: str, amount: Decimal, dueDate: str, paymentAccID: int, minPayment=Decimal("0.00")) -> dict:
    """
    Schedules a bill payment for the customer.

    Parameters
    ----------
    customerID : int
        The Customer ID scheduling the payment.
    payeeName : str
        Name of the payee.
    payeeAddress : str
        Address of the payee.
    amount : Decimal
        The amount to pay.
    dueDate : str
        The due date for the payment in YYYY-MM-DD format.
    paymentAccID : int
        The Account ID from which the payment will be made.
    minPayment : Decimal
        The minimum required payment for the bill.

    Returns
    -------
    dict
        - If scheduling is successful:
          {"status": "success", "message": "Bill payment scheduled successfully."}
        - If scheduling fails:
          {"status": "error", "message": "Failure reason."}
    """
    billsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/bills.csv'))

    # Load bills data
    billsData = pd.read_csv(billsPath)

    # Generate a unique Account ID that does not conflict with existing IDs
    billID = random.randint(1, 50000)
    while billID in billsData['BillID'].values:
        billID = random.randint(1, 50000)

    # Append new bill payment to DataFrame
    newBillPayment = {
        'BillID': billID,
        'CustomerID': customerID,
        'PayeeName': payeeName,
        'PayeeAddress': payeeAddress,
        'Amount': Decimal(amount).quantize(Decimal('0.00')),
        'DueDate': dueDate,
        'PaymentAccID': paymentAccID,
        'MinPayment': Decimal(minPayment).quantize(Decimal('0.00'))
    }

    billsData.loc[len(billsData)] = newBillPayment
    billsData.to_csv(billsPath, index=False)

    return {"status": "success", "message": "Bill payment scheduled successfully."}

def viewScheduledBills(customerID: int) -> list:
    """
    Retrieves all scheduled bills for a given customer.

    Parameters
    ----------
    customerID : int
        The Customer ID whose bills are to be retrieved.

    Returns
    -------
    list
        A list of dictionaries representing each scheduled bill.
    """
    billsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/bills.csv'))

    if not os.path.exists(billsPath):
        return [{"status": "error", "message": "No scheduled bills found."}]

    billsData = pd.read_csv(billsPath)
    customerBills = billsData[billsData['CustomerID'] == customerID].to_dict(orient='records')

    return customerBills if customerBills else [{"status": "error", "message": "No scheduled bills found for this customer."}]

def processScheduledBills() -> list:
    """
    Processes all scheduled bill payments due today.

    Returns
    -------
    list
        A list of dictionaries indicating the result of processing each bill.
    """
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    billsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/bills.csv'))
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))

    if not os.path.exists(billsPath):
        return [{"status": "error", "message": "No scheduled bills to process."}]

    accountsData = pd.read_csv(accountsPath)
    billsData = pd.read_csv(billsPath)
    transData = pd.read_csv(transPath)

    today = date.today()
    results = []

    for index, bill in billsData.iterrows():
        dueDate = date.fromisoformat(bill['DueDate'])
        # If bill is due today
        if dueDate == today:
            accIndex = accountsData[accountsData['AccountID'] == bill['PaymentAccID']].index
            if accIndex.empty:
                results.append({"status": "error", "message": f"Payment account {bill['PaymentAccID']} not found."})
                continue

            accountType = accountsData.at[accIndex[0], 'AccountType']

            # Re-apply Decimal formatting before balance operations
            accountsData['CurrBal'] = accountsData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            balance = accountsData.at[accIndex[0], 'CurrBal']
            billsData['Amount'] = billsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            amount = Decimal(bill['Amount']).quantize(Decimal('0.00'))

            success = False
            # Checking and savings account used to pay bills
            if accountType == 'Credit Card':
                creditLimit = accountsData.at[accIndex[0], 'CreditLimit']
                creditLimit = Decimal(str(creditLimit))

                if balance + amount > creditLimit:
                    overLimitFee = Decimal('35.00')
                    dueDate = (date.today() + timedelta(days=30)).isoformat()

                    scheduleBillPayment(
                        bill['CustomerID'],
                        'Evergreen Bank Credit Department',
                        '301 Sparkman Dr NW, Huntsville, AL 35899',
                        overLimitFee,
                        dueDate,
                        bill['PaymentAccID'],
                        Decimal('35.00')
                    )

                    results.append({"status": "error", "message": f"Over-limit fee of ${overLimitFee} billed and due by {dueDate}."})
                    continue
                # Allow payment by increasing credit card balance
                accountsData.at[accIndex[0], 'CurrBal'] = balance + amount
                transactionID = generate_transaction_ID(transData)
                success = True
            elif balance >= amount:
                # Deduct payment from source account
                accountsData.at[accIndex[0], 'CurrBal'] = balance - amount
                transactionID = generate_transaction_ID(transData)
                success = True
            if success:
                newDueDate = dueDate + timedelta(days=30)
                billsData.at[index, 'DueDate'] = newDueDate.isoformat()

                newTransaction = {
                    'TransactionID': transactionID,
                    'AccountID': bill['PaymentAccID'],
                    'TransactionType': f"Bill Payment to {bill['PayeeName']}",
                    'Amount': Decimal(amount).quantize(Decimal('0.00')),
                    'TransDate': date.today()
                }
                transData.loc[len(transData)] = newTransaction

                results.append({"status": "success", "message": f"Bill payment of ${amount} to {bill['PayeeName']} processed successfully. Due Date updated to {newDueDate}."})
            else:
                results.append({"status": "error", "message": f"Insufficient funds for payment to {bill['PayeeName']}."})

    accountsData['CurrBal'] = accountsData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    accountsData['CreditLimit'] = accountsData['CreditLimit'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    accountsData.to_csv(accountsPath, index=False)
    billsData['Amount'] = billsData['Amount'].apply(lambda x: f"{Decimal(str(x)):.2f}" if pd.notna(x) else "")
    billsData['MinPayment'] = billsData['MinPayment'].apply(lambda x: f"{Decimal(str(x)):.2f}" if pd.notna(x) else "")
    billsData.to_csv(billsPath, index=False)
    transData['Amount'] = transData['Amount'].apply(lambda x: f"{Decimal(str(x)):.2f}" if pd.notna(x) else "")
    transData.to_csv(transPath, index=False)

    return results


def generate_monthly_credit_card_statements():
    """
    Updates MinPayment for overdue credit card bills based on balance:
    - $25 if amount < $1000
    - 2% of amount if amount >= $1000
    """
    base_dir = os.path.dirname(os.path.realpath(__file__))
    accounts_path = os.path.abspath(os.path.join(base_dir, '../csvFiles/accounts.csv'))
    bills_path = os.path.abspath(os.path.join(base_dir, '../csvFiles/bills.csv'))

    if not os.path.exists(accounts_path) or not os.path.exists(bills_path):
        return {"status": "error", "message": "Required CSV file(s) not found."}

    accounts_df = pd.read_csv(accounts_path)
    bills_df = pd.read_csv(bills_path)

    # Find all credit card accounts
    credit_card_ids = accounts_df[accounts_df['AccountType'] == 'Credit Card']['AccountID'].astype(int).tolist()

    today = date.today()
    updated_count = 0

    bills_df['Amount'] = bills_df['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    bills_df['DueDate'] = pd.to_datetime(bills_df['DueDate']).dt.date


    bills_df['MinPayment'] = pd.to_numeric(bills_df['MinPayment'], errors='coerce')
    
    for idx, row in bills_df.iterrows():
        if int(row['PaymentAccID']) in credit_card_ids and row['DueDate'] < today:
            amount = row['Amount']
            new_min = Decimal('25.00') if amount < Decimal('1000.00') else (amount * Decimal('0.02')).quantize(Decimal('0.00'))
            bills_df.at[idx, 'MinPayment'] = float(Decimal(new_min))
            updated_count += 1

    if updated_count > 0:
        bills_df['MinPayment'] = bills_df['MinPayment'].apply(lambda x: f"{Decimal(str(x)):.2f}" if pd.notna(x) else "")
        bills_df.to_csv(bills_path, index=False)
        return {"status": "success", "message": f"{updated_count} overdue credit card bill(s) updated."}
    else:
        return {"status": "success", "message": "No overdue credit card bills found."}
