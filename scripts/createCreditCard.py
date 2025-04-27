# Spring 2025 Authors: Sierra Yerges, Bailee Segars
import pandas as pd
import random
import os
from datetime import date
from decimal import Decimal

def openCreditCardAccount(customerID: int) -> dict:
    """
    Opens a new credit card account with APR assigned based on APR range ID.

    Parameters
    ----------
    customerID : int
        The Customer ID for whom the credit card account is being created.

    Returns
    -------
    dict
        - If account creation is successful:
          {"status": "success", "message": "Credit card account {accountID} created with a ${creditLimit} limit at {apr}% APR."}
        - If the customer ID is invalid:
          {"status": "error", "message": "Customer {customerID} not found."}
    """
    # Get absolute path for accounts.csv file
    accountsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    # Get absolute path for customer.csv file
    customerPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/customers.csv'))
    # Get absolute path for transactions.csv file
    log_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))

    # Load all existing log data
    log_df = pd.read_csv(log_path)
    
    # Load all existing account data into a DataFrame
    customerData = pd.read_csv(customerPath)

    # Filter the DataFrame for the user with the specified customerID
    userRow = customerData[customerData['CustomerID'] == customerID]

    # Check if the customer exists; return an error message if not found
    if userRow.empty:
        return {"status": "error", "message": f"Customer {customerID} not found."}

    # Define APR ranges based on APRRangeID assigned at account creation
    apr_ranges = {
        1: (19.6, 20),
        2: (20.1, 24),
        3: (24.1, 27),
        4: (27.1, 30)
    }

    # Retrieve APRRangeID and select the corresponding APR range
    apr_range_id = userRow.iloc[0]['APRRangeID']
    apr_range = apr_ranges.get(apr_range_id, (19.6, 20))

    # Generate a random APR within the specified range
    apr = round(random.uniform(*apr_range), 2)

    # Load all existing account data into a DataFrame
    accountsData = pd.read_csv(accountsPath)

    # Filter the DataFrame for the user with the specified customerID
    userRow = accountsData[accountsData['CustomerID'] == customerID]

    # Generate a unique Account ID that does not conflict with existing IDs
    accountID = random.randint(5000, 9999)
    while accountID in accountsData['AccountID'].values:
        accountID = random.randint(5000, 9999)

    limit = random.choice([1000, 3000, 7000, 15000])

    # Create a dictionary with new credit card account details
    newAccount = {
        "AccountID": accountID,
        "CustomerID": customerID,
        "AccountType": "Credit Card",
        "CurrBal": Decimal('0.00'),
        "DateOpened": date.today(),
        "CreditLimit": Decimal(limit).quantize(Decimal('0.00')),
        "APR": apr
    }

    # Append the new account details to the DataFrame and save back to CSV
    newAccountDf = pd.DataFrame([newAccount])
    if accountsData.empty:
        accountsData = newAccountDf.copy()
    else:
        accountsData = pd.concat([accountsData, newAccountDf], ignore_index=True)
    accountsData["CurrBal"] = accountsData["CurrBal"].apply(lambda x: f"{Decimal(x):.2f}")
    accountsData["CreditLimit"] = accountsData["CreditLimit"].apply(lambda x: f"{Decimal(x):.2f}")
    accountsData.to_csv(accountsPath, index=False)

    log_id = random.randint(1299, 5999)
    while log_id in log_df['LogID'].values:
        log_id = random.randint(1299, 5999)


    newLog = {'LogID': log_id, 'UserID': customerID, 'LogMessage': 'Opened a Credit Card'}

    log_df.loc[len(log_df)] = newLog

    log_df.to_csv(log_path, index=False)

    # Return a success message with account details
    return {"status": "success", "message": f"Credit card account {accountID} created with a {apr}% APR."}