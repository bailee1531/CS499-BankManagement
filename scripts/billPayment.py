# Sierra Yerges
from scripts.transactionLog import generate_transaction_ID
from scripts.archive import archive
import random
import pandas as pd
from decimal import Decimal
import os
from datetime import date, timedelta
from typing import Dict, List, Union, Optional

# Standardized file path handling
def get_file_path(relative_path: str) -> str:
    """Returns absolute path to a CSV file in the csvFiles directory"""
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(base_dir, f'../csvFiles/{relative_path}'))

# Helper function to generate a unique bill ID
def generate_unique_bill_id(bills_df: pd.DataFrame) -> int:
    """Generate a unique bill ID that doesn't exist in the bills DataFrame"""
    if bills_df.empty or 'BillID' not in bills_df.columns:
        return 1
    
    max_attempts = 10
    for _ in range(max_attempts):
        bill_id = random.randint(1, 50000)
        if bill_id not in bills_df['BillID'].values:
            return bill_id
    
    # If we couldn't find a random unique ID, use max + 1
    return bills_df['BillID'].max() + 1

# Helper function to convert to Decimal with proper quantization
def to_decimal(value) -> Decimal:
    """Convert a value to Decimal with 2 decimal places"""
    return Decimal(str(value)).quantize(Decimal('0.00'))

def scheduleBillPayment(
    customerID: int, 
    payeeName: str, 
    payeeAddress: str, 
            amount: Union[Decimal, float, str], 
    dueDate: str, 
    paymentAccID: int, 
    minPayment: Union[Decimal, float, str] = Decimal("0.00"), 
    billType: str = "Regular", 
    isRecurring: int = 0
) -> Dict[str, str]:
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
    amount : Decimal, float, or str
        The amount to pay (use negative value for amounts owed).
    dueDate : str
        The due date for the payment in YYYY-MM-DD format.
    paymentAccID : int
        The Account ID from which the payment will be made.
    minPayment : Decimal, float, or str
        The minimum required payment for the bill (use positive value).
    billType : str
        Type of bill (CreditCard, Mortgage, Regular)
    isRecurring : int
        Flag indicating if bill should recur (1=yes, 0=no)

    Returns
    -------
    dict
        - If scheduling is successful:
          {"status": "success", "message": "Bill payment scheduled successfully."}
        - If scheduling fails:
          {"status": "error", "message": "Failure reason."}
    """
    billsPath = get_file_path('bills.csv')

    # Load bills data
    try:
        billsData = pd.read_csv(billsPath)
    except FileNotFoundError:
        billsData = pd.DataFrame(columns=[
            'BillID', 'CustomerID', 'PayeeName', 'PayeeAddress', 'Amount', 
            'DueDate', 'PaymentAccID', 'MinPayment', 'BillType', 'IsRecurring', 'Status'
        ])

    # Generate a unique Bill ID
    billID = generate_unique_bill_id(billsData)
    
    # Ensure amount is negative (money owed) but minPayment is positive
    decimal_amount = to_decimal(amount)
    if decimal_amount > 0:
        decimal_amount = -decimal_amount
        
    decimal_min_payment = to_decimal(minPayment)
    if decimal_min_payment < 0:
        decimal_min_payment = -decimal_min_payment  # Ensure minimum payment is positive

    # Append new bill payment to DataFrame
    newBillPayment = {
        'BillID': billID,
        'CustomerID': customerID,
        'PayeeName': payeeName,
        'PayeeAddress': payeeAddress,
        'Amount': float(decimal_amount),
        'DueDate': dueDate,
        'PaymentAccID': paymentAccID,
        'MinPayment': float(decimal_min_payment),
        'BillType': billType,
        'IsRecurring': isRecurring,
        'Status': 'Pending'
    }

    billsData = pd.concat([billsData, pd.DataFrame([newBillPayment])], ignore_index=True)
    billsData.to_csv(billsPath, index=False)

    return {"status": "success", "message": "Bill payment scheduled successfully."}

def viewScheduledBills(customerID: int) -> List[Dict]:
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
    billsPath = get_file_path('bills.csv')

    if not os.path.exists(billsPath):
        return [{"status": "error", "message": "No scheduled bills found."}]

    billsData = pd.read_csv(billsPath)
    customerBills = billsData[billsData['CustomerID'] == customerID].to_dict(orient='records')

    return customerBills if customerBills else [{"status": "error", "message": "No scheduled bills found for this customer."}]

def processScheduledBills() -> List[Dict[str, str]]:
    """
    Processes all scheduled bill payments due today or overdue.
    - Marks bills that are overdue as "Late"
    - For recurring and mortgage bills: Makes payments from available accounts
    - Handles bill payment transactions
    
    Returns
    -------
    list
        A list of dictionaries with status and message about each processed bill
    """
    accountsPath = get_file_path('accounts.csv')
    billsPath = get_file_path('bills.csv')
    transPath = get_file_path('transactions.csv')
    archivedBillsPath = get_file_path('archivedBills.csv')

    if not os.path.exists(billsPath):
        return [{"status": "error", "message": "No scheduled bills to process."}]

    accountsData = pd.read_csv(accountsPath)
    billsData = pd.read_csv(billsPath)
    transData = pd.read_csv(transPath) if os.path.exists(transPath) else pd.DataFrame()
    archivedBillsData = pd.read_csv(archivedBillsPath) if os.path.exists(archivedBillsPath) else pd.DataFrame()

    today = date.today()
    results = []

    # Convert to decimal for precise calculations
    accountsData['CurrBal'] = accountsData['CurrBal'].apply(to_decimal)
    billsData['Amount'] = billsData['Amount'].apply(to_decimal)
    billsData['MinPayment'] = billsData['MinPayment'].apply(to_decimal)

    for index, bill in billsData.iterrows():
        try:
            # Parse the due date
            dueDate = date.fromisoformat(bill['DueDate'])
        except (ValueError, TypeError) as e:
            results.append({
                "status": "error",
                "message": f"Invalid date format for bill {bill.get('BillID', 'unknown')}: {str(e)}"
            })
            continue

        # 1) Purely overdue & still unpaid → mark Late and skip payment logic
        if dueDate < today and bill['Status'] in ['Pending', 'PartiallyPaid']:
            billsData.at[index, 'Status'] = 'Late'
            results.append({
                "status": "error",
                "message": f"Bill {bill['BillID']} is overdue. Marked as Late."
            })
            continue

        # 2) Bills due today & still unpaid = handle payments or auto-pay logic
        if dueDate == today and bill['Status'] in ['Pending', 'PartiallyPaid']:
            # Get bill details
            bill_id = bill['BillID']
            custID = bill['CustomerID']
            payee_name = bill['PayeeName']
            payee_address = bill['PayeeAddress']
            payment_account_id = bill['PaymentAccID']
            bill_amount = to_decimal(bill['Amount'])  # This is negative (money owed)
            min_payment = to_decimal(bill['MinPayment'])  # This is negative (money owed)
            bill_type = bill['BillType']
            is_recurring = bill['IsRecurring']

            # Locate payment account
            accIndex = accountsData[accountsData['AccountID'] == payment_account_id].index
            if accIndex.empty:
                results.append({"status": "error", "message": f"Payment account {payment_account_id} not found."})
                continue

            account_row = accountsData.iloc[accIndex[0]]
            balance = to_decimal(account_row['CurrBal'])

            # Process by bill type
            if bill_type == 'Mortgage' or is_recurring == 1:
                payment_sources = accountsData[
                    (accountsData['CustomerID'] == custID) &
                    (accountsData['AccountType'].isin(['Checking', 'Savings']))
                ]
                
    # Finalize data
    billsData['Status'] = billsData['Status'].astype(str).str.replace('\n', '', regex=False).str.strip()
    billsData.to_csv(billsPath, index=False, lineterminator='\n')
    accountsData.to_csv(accountsPath, index=False)
    if not transData.empty:
        transData.to_csv(transPath, index=False)

    return results

def generate_monthly_credit_card_statements() -> Dict[str, str]:
    """
    Generates monthly statements for credit card accounts by creating bills
    for accounts open for at least 1 month without active bills
    
    Returns
    -------
    dict
        Status and message about the operation results
    """
    # Set up paths
    accounts_path = get_file_path('accounts.csv')
    bills_path = get_file_path('bills.csv')

    # Check if required files exist
    if not os.path.exists(accounts_path) or not os.path.exists(bills_path):
        return {"status": "error", "message": "Required CSV file(s) not found."}

    # Load data
    accounts_df = pd.read_csv(accounts_path)
    bills_df = pd.read_csv(bills_path)


    accounts_df['CurrBal'] = accounts_df['CurrBal'].apply(to_decimal)
    bills_df['Amount'] = bills_df['Amount'].apply(to_decimal)
    bills_df['MinPayment'] = bills_df['MinPayment'].apply(to_decimal)
    
    # Convert DueDate to datetime.date objects
    if 'DueDate' in bills_df.columns and not bills_df.empty:
        bills_df['DueDate'] = pd.to_datetime(bills_df['DueDate'], errors='coerce').dt.date
    
    # Set time references
    today = date.today()
    one_month_ago = today - timedelta(days=30)
    
    # Find all credit card accounts
    credit_card_accounts = accounts_df[accounts_df['AccountType'] == 'Credit Card']
    
    # Create new bills for credit card accounts without active bills
    bills_created = 0
    
    for _, account in credit_card_accounts.iterrows():
        account_id = account['AccountID']
        customer_id = account['CustomerID']
        current_balance = to_decimal(account['CurrBal'])
        
        # Credit card accounts have negative balances when money is owed
        if current_balance >= Decimal('0.00'):
            continue
        
        # Check account opening date
        if 'DateOpened' in account and pd.notna(account['DateOpened']):
            try:
                date_opened = pd.to_datetime(account['DateOpened']).date()
                
                # Skip if account is less than a month old
                if date_opened > one_month_ago:
                    continue
            except Exception:
                # If there's any error parsing the date, skip this account
                continue
        else:
            # Skip if DateOpened is missing
            continue
        
        # Check for existing active bills
        # Convert PaymentAccID to string for comparison if it's not already
        if 'PaymentAccID' in bills_df.columns:
            bills_df['PaymentAccID'] = bills_df['PaymentAccID'].astype(str)
            account_bills = bills_df[
                (bills_df['PaymentAccID'] == str(account_id)) & 
                (bills_df['Status'].isin(['Pending', 'PartiallyPaid', 'Late', 'Past Due']))
            ]
            
            # Only create a new bill if no active bills exist
            if account_bills.empty:
                # Calculate minimum payment (2% of balance or $25, whichever is greater)
                # Note: current_balance is negative, so we need abs() to get the positive amount owed
                min_payment = max(Decimal('25.00'), abs(current_balance) * Decimal('0.02')).quantize(Decimal('0.00'))
                
                # Create new bill - make sure amount is negative (money owed)
                bill_id = generate_unique_bill_id(bills_df)
                new_bill = {
                    'BillID': bill_id,
                    'CustomerID': customer_id,
                    'PayeeName': "Evergreen Bank",
                    'PayeeAddress': "Somewhere In The World",
                    'Amount': float(current_balance),  # Already negative
                    'DueDate': (today + timedelta(days=30)).isoformat(),
                    'PaymentAccID': account_id,
                    'MinPayment': float(min_payment),  # Negative
                    'BillType': 'CreditCard',
                    'IsRecurring': 1,
                    'Status': 'Pending'
                }
                
                # Append the new bill
                bills_df = pd.concat([bills_df, pd.DataFrame([new_bill])], ignore_index=True)
                bills_created += 1
        
    # Save bills data
    bills_df.to_csv(bills_path, index=False)
    
    return {
        "status": "success", 
        "message": f"Created {bills_created} new credit card bill(s)."
    }