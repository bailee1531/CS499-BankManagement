# Sierra Yerges
# archive.py

import pandas as pd
import os
from decimal import Decimal

# Define file paths
billsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/bills.csv'))
loansPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/accounts.csv'))  # Mortgage loans are stored here
archivedBillsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/archivedBills.csv'))
archivedLoansPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/archivedLoans.csv'))

def archive(recordType: str, recordID: int, remove_record: bool = False) -> dict:
    """
    Archives a bill or a fully paid home mortgage loan.
    
    For a 'bill' record: a snapshot is appended to archivedBills.csv.
    The active record is removed from bills.csv only if remove_record is True.
    
    Parameters
    ----------
    recordType : str
        Type of record to archive. Either 'bill' or 'loan'.
    recordID : int
        The ID of the bill or loan to be archived.
    remove_record : bool, optional
        If True, remove the record from the active CSV file (default is False).
    
    Returns
    -------
    dict
        A dictionary indicating success or failure.
    """
    if recordType == "bill":
        if not os.path.exists(billsPath):
            return {"status": "error", "message": "No bills to archive."}

        billsData = pd.read_csv(billsPath)

        # Locate the bill record
        billRecord = billsData[billsData['BillID'] == recordID]
        if billRecord.empty:
            return {"status": "error", "message": f"Bill with ID {recordID} not found."}

        # Archive: append a copy to archivedBills.csv
        archivedBillsData = pd.read_csv(archivedBillsPath) if os.path.exists(archivedBillsPath) else pd.DataFrame()
        if archivedBillsData.empty:
            archivedBillsData = billRecord.copy()
        else:
            archivedBillsData = pd.concat([archivedBillsData, billRecord], ignore_index=True)
        archivedBillsData['Amount'] = archivedBillsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedBillsData.to_csv(archivedBillsPath, index=False)

        # If removal is requested (i.e. fully paid), remove the active record.
        if remove_record:
            billsData = billsData[billsData['BillID'] != recordID]
            billsData['Amount'] = billsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
            billsData.to_csv(billsPath, index=False)
        return {"status": "success", "message": f"Bill with ID {recordID} archived successfully."}

    elif recordType == "loan":
        if not os.path.exists(loansPath):
            return {"status": "error", "message": "No mortgage loans to archive."}

        loansData = pd.read_csv(loansPath)
        loansData['CurrBal'] = loansData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        loanRecord = loansData[
            (loansData['AccountID'] == recordID) & 
            (loansData['AccountType'] == 'Mortgage Loan') & 
            (loansData['CurrBal'] == Decimal('0.00'))
        ]
        if loanRecord.empty:
            return {"status": "error", "message": f"Mortgage Loan with ID {recordID} is not fully paid off or does not exist."}

        archivedLoansData = pd.read_csv(archivedLoansPath) if os.path.exists(archivedLoansPath) else pd.DataFrame()
        if archivedLoansData.empty:
            archivedLoansData = loanRecord.copy()
        else:
            archivedLoansData = pd.concat([archivedLoansData, loanRecord], ignore_index=True)
        archivedLoansData['CurrBal'] = archivedLoansData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedLoansData['CreditLimit'] = archivedLoansData['CreditLimit'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedLoansData.to_csv(archivedLoansPath, index=False)

        # For loans, if we remove the record when fully paid.
        loansData = loansData[loansData['AccountID'] != recordID]
        loansData['CurrBal'] = loansData['CurrBal'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        loansData['CreditLimit'] = loansData['CreditLimit'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        loansData.to_csv(loansPath, index=False)

        return {"status": "success", "message": f"Mortgage Loan with ID {recordID} archived successfully."}
    else:
        return {"status": "error", "message": "Invalid record type. Use 'bill' or 'loan'."}


def viewArchivedBills(customerID: int) -> list:
    """
    Retrieves all archived bills for a given customer.

    Parameters
    ----------
    customerID : int
        The Customer ID whose archived bills are to be retrieved.

    Returns
    -------
    list
        A list of dictionaries representing each archived bill.
    """
    if not os.path.exists(archivedBillsPath):
        return [{"status": "error", "message": "No archived bills found."}]

    archivedBillsData = pd.read_csv(archivedBillsPath)
    customerBills = archivedBillsData[archivedBillsData['CustomerID'] == customerID].to_dict(orient='records')

    return customerBills if customerBills else [{"status": "error", "message": "No archived bills found for this customer."}]


def viewArchivedLoans(customerID: int) -> list:
    """
    Retrieves all archived home mortgage loans for a given customer.

    Parameters
    ----------
    customerID : int
        The Customer ID whose archived mortgage loans are to be retrieved.

    Returns
    -------
    list
        A list of dictionaries representing each archived mortgage loan.
    """
    if not os.path.exists(archivedLoansPath):
        return [{"status": "error", "message": "No archived mortgage loans found."}]

    archivedLoansData = pd.read_csv(archivedLoansPath)
    customerLoans = archivedLoansData[archivedLoansData['CustomerID'] == customerID].to_dict(orient='records')

    return customerLoans if customerLoans else [{"status": "error", "message": "No archived mortgage loans found for this customer."}]
