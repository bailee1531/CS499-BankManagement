# Sierra Yerges
import pandas as pd
import time
from datetime import date
from decimal import Decimal
from datetime import date, timedelta
import os
from scripts.transactionLog import generate_transaction_ID

def calculateCreditInterest():
    """
    Calculates monthly interest on unpaid balances for all credit card
    & home mortgage loan accounts, using APR values assigned during account creation.
    Also updates late bills to pending status, interest is only added to the account balance without changing the bill amount or minimum payment.

    Returns
    -------
    dict
        A dictionary containing the status and message.
        {"status": "success", "message": f"Interest of ${interest} applied to AccountID {account['AccountID']}."}

        Updates 'accounts.csv' with new balances including accrued interest.
        Updates 'bills.csv' to change status from 'Late' to 'Pending'.
    """
    # Get absolute path for accounts.csv
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    transPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/transactions.csv'))
    billsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/bills.csv'))

    # Check if files exist
    for filepath, filename in [(accountsPath, 'accounts.csv'), (transPath, 'transactions.csv'), (billsPath, 'bills.csv')]:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return [{"status": "error", "message": f"File {filename} does not exist or is empty."}]
    
    try:
        time.sleep(0.1) 

        accountsData = pd.read_csv(accountsPath)
        if accountsData.empty:
            return [{"status": "info", "message": "No accounts found. No interest applied."}]
        accountsData['CurrBal'] = accountsData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        
        # Load transaction data
        transData = pd.read_csv(transPath)
        
        # Load bills data - handle potential empty files with proper error messages
        try:
            billsData = pd.read_csv(billsPath)
        except pd.errors.EmptyDataError:
            return [{"status": "info", "message": "Bills file is empty. No interest applied."}]
        except Exception as e:
            return [{"status": "error", "message": f"Error reading bills.csv: {str(e)}"}]
    except Exception as e:
        return [{"status": "error", "message": f"Error loading data: {str(e)}"}]
    
    # Check if bills.csv is empty - if so, do nothing and return
    if billsData.empty:
        return [{"status": "info", "message": "No bills found. No interest applied."}]
    
    # Check if the DataFrame has the expected columns
    expected_columns = ['Amount', 'MinPayment', 'PaymentAccID', 'Status', 'BillID', 'DueDate']
    missing_columns = [col for col in expected_columns if col not in billsData.columns]
    
    if missing_columns:
        return [{"status": "error", "message": f"Missing columns in bills.csv: {', '.join(missing_columns)}"}]
    
    try:
        billsData['Amount'] = billsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        billsData['MinPayment'] = billsData['MinPayment'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
    except Exception as e:
        return [{"status": "error", "message": f"Error processing bills data: {str(e)}"}]

    # Identify all credit accounts (credit cards and home mortgage loans)
    creditAccounts = accountsData[(accountsData['AccountType'] == 'Credit Card') | (accountsData['AccountType'] == 'Mortgage Loan')]

    results = []

    # Apply interest calculation for each account
    for index, account in creditAccounts.iterrows():
        unpaidBalance = Decimal(str(account['CurrBal']))
        apr = Decimal(str(account['APR']))
        accID = account['AccountID']
        accType = account['AccountType']
        custID = account['CustomerID']

        # Check if there are any bills associated with this account
        # Convert PaymentAccID to string for comparison if it's not already
        if 'PaymentAccID' in billsData.columns:
            billsData['PaymentAccID'] = billsData['PaymentAccID'].astype(str)
            account_bills = billsData[billsData['PaymentAccID'] == str(accID)]
            if account_bills.empty:
                continue  # Skip this account if no bills are associated with it
        else:
            continue  # Skip if PaymentAccID column is missing

        monthlyInterestRate = apr / Decimal(100) / Decimal(12)
        
        late_bills = account_bills[account_bills['Status'] == 'Late'] if 'Status' in account_bills.columns else pd.DataFrame()
        
        # Apply interest only when there are late bills
        if not late_bills.empty:
            # Initialize total account interest
            total_account_interest = Decimal('0.00')
            
            # Handle Mortgage and Credit Card accounts differently
            if accType == 'Mortgage Loan':
                # For mortgage loans, calculate interest once based on entire account balance
                interest = (unpaidBalance * monthlyInterestRate).quantize(Decimal('0.00'))
                total_account_interest = interest
                # Update all late bills for this mortgage account
                for bill_idx, bill in late_bills.iterrows():
                    # Only update due date and status for mortgage bills
                    billsData.at[bill_idx, 'DueDate'] = (date.today() + timedelta(days=30)).isoformat()
                    billsData.at[bill_idx, 'Status'] = 'Pending'
                    
                    results.append({
                        "status": "success",
                        "message": f"Mortgage Bill ID {bill['BillID']} updated: Status changed from Late to Pending, due date extended."
                    })
            else:
                # Process each late bill for credit card accounts
                for bill_idx, bill in late_bills.iterrows():
                    # Original logic for credit cards
                    original_amount = Decimal(str(bill['Amount']))  # Should be negative (money owed)
                    
                    # Calculate bill interest (will be negative since original_amount is negative)
                    bill_interest = (original_amount * monthlyInterestRate).quantize(Decimal('0.00'))
                    
                    # Make bill amount more negative by adding negative interest
                    new_amount = (original_amount + bill_interest).quantize(Decimal('0.00'))
                    
                    # Update minimum payment (use 3% of abs of the new balance, keep positive)
                    new_min_payment = (abs(new_amount) * Decimal('0.03')).quantize(Decimal('0.00'))
                    
                    # Update the bills dataframe
                    billsData.at[bill_idx, 'Amount'] = new_amount
                    billsData.at[bill_idx, 'MinPayment'] = new_min_payment
                    billsData.at[bill_idx, 'DueDate'] = (date.today() + timedelta(days=30)).isoformat()
                    billsData.at[bill_idx, 'Status'] = 'Pending'
                    
                    # Add this bill's interest to total account interest (make positive for accounting)
                    total_account_interest += abs(bill_interest)
                    
                    results.append({
                        "status": "success",
                        "message": f"Bill ID {bill['BillID']} updated: Status changed from Late to Pending, new amount ${abs(new_amount)}, new minimum payment ${abs(new_min_payment)}."
                    })
            
            # Update account balance with total interest from all bills (both mortgage and credit cards)
            if abs(total_account_interest) > Decimal('0.00'):
                # Update balance by subtracting interest (making balance more negative)
                if accType == 'Mortgage Loan':
                    # For mortgage loans, make sure interest makes the balance more negative
                    updatedBalance = (unpaidBalance - abs(total_account_interest)).quantize(Decimal('0.00'))
                else:
                    # For credit cards, use the current approach
                    updatedBalance = (unpaidBalance - total_account_interest).quantize(Decimal('0.00'))
                
                # Update account balance in the dataframe - THIS IS THE CRITICAL STEP!
                accountsData.at[index, 'CurrBal'] = updatedBalance
                
                # Generate transaction ID and log the transaction
                transactionID = generate_transaction_ID(transData)
                newLog = {
                    'TransactionID': transactionID,
                    'AccountID': accID,
                    'TransactionType': 'Interest Charged',
                    'Amount': Decimal(total_account_interest).quantize(Decimal('0.00')),
                    'TransDate': date.today()
                }
                transData.loc[len(transData)] = newLog
                
                results.append({
                    "status": "success",
                    "message": f"Interest of ${total_account_interest} applied to AccountID {accID}."
                })
        else:
            continue  # No interest applied to accounts with no late bills

    # Only save if changes were made
    if results:
        try:
            # Save updated balances to accounts.csv
            accountsData.to_csv(accountsPath, index=False)
            
            # Save updated transaction logs
            transData['Amount'] = transData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            transData.to_csv(transPath, index=False)
            
            # Save updated bills
            billsData.to_csv(billsPath, index=False)
        except Exception as e:
            return [{"status": "error", "message": f"Error saving updated data: {str(e)}"}]
    
    # If no interest was applied, add an informative message
    if not results:
        results.append({
            "status": "info", 
            "message": "No interest applied. Either all accounts are paid or there are no late bills."
        })

    return results