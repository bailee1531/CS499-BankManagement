# Sierra Yerges
import pandas as pd
import os
from decimal import Decimal

# Define file paths
billsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/bills.csv'))
loansPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/accounts.csv'))  # Mortgage loans are stored here
archivedBillsPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/archivedBills.csv'))
archivedLoansPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../csvFiles/archivedLoans.csv'))

def archive(recordType: str, recordID: int) -> dict:
    """
    Archives a canceled bill or a fully paid home mortgage loan.

    Parameters
    ----------
    recordType : str
        Type of record to archive. Either 'bill' or 'loan'.
    recordID : int
        The ID of the bill or loan to be archived.

    Returns
    -------
    dict
        A dictionary indicating success or failure.
    """
    if recordType == "bill":
        if not os.path.exists(billsPath):
            return {"status": "error", "message": "No bills to archive."}

        billsData = pd.read_csv(billsPath)

        # Locate and archive the canceled bill
        billRecord = billsData[billsData['BillID'] == recordID]
        if billRecord.empty:
            return {"status": "error", "message": f"Bill with ID {recordID} not found."}

        archivedBillsData = pd.read_csv(archivedBillsPath)

        if archivedBillsData.empty:
            archivedBillsData = billRecord
        else:
            archivedBillsData = pd.concat([archivedBillsData, billRecord], ignore_index=True)
        archivedBillsData['Amount'] = archivedBillsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedBillsData.to_csv(archivedBillsPath, index=False)

        # Remove the bill from active records
        billsData = billsData[billsData['BillID'] != recordID]
        billsData['Amount'] = billsData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        billsData.to_csv(billsPath, index=False)

        return {"status": "success", "message": f"Bill with ID {recordID} archived successfully."}

    elif recordType == "loan":
        if not os.path.exists(loansPath):
            return {"status": "error", "message": "No mortgage loans to archive."}

        loansData = pd.read_csv(loansPath)

        # Locate the paid-off mortgage loan
        loanRecord = loansData[
            (loansData['AccountID'] == recordID) & (loansData['AccountType'] == 'Mortgage Loan') & (Decimal(loansData['CurrBal'].iloc[0]) == Decimal('0.00'))
        ]
        if loanRecord.empty:
            return {"status": "error", "message": f"Mortgage Loan with ID {recordID} is not fully paid off or does not exist."}

        archivedLoansData = pd.read_csv(archivedLoansPath)

        if archivedLoansData.empty:
            archivedLoansData = loanRecord
        else:
            archivedLoansData = pd.concat([archivedLoansData, loanRecord], ignore_index=True)
        archivedLoansData['CurrBal'] = archivedLoansData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedLoansData['CreditLimit'] = archivedLoansData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        archivedLoansData.to_csv(archivedLoansPath, index=False)

        # Remove the mortgage loan from active records
        loansData = loansData[loansData['AccountID'] != recordID]
        loansData['CurrBal'] = loansData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
        loansData['CreditLimit'] = loansData['Amount'].apply(lambda x: Decimal(str(x)).quantize(Decimal('0.00')))
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

print(archive('bill',41131))
print(viewArchivedBills(315))
print(viewArchivedLoans(315))