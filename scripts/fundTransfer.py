# Spring 2025 Authors: Sierra Yerges, Braden Doty
import pandas as pd
import os
from decimal import Decimal
from scripts.withdrawMoney import withdraw
from scripts.makeDeposit import deposit

def transferFunds(srcAccID: int, destAccID: int, amount: Decimal) -> dict:
    """
    Transfers funds between two accounts by withdrawing from one and depositing into another.

    Parameters
    ----------
    srcAccID : int
        The account ID from which the funds will be withdrawn.
    destAccID : int
        The account ID that will receive the funds.
    amount : Decimal
        The amount of money to be transferred.

    Returns
    -------
    dict
        A dictionary indicating the status of the transfer.

        - If either account does not exist:
          {"status": "error", "message": "Source/Destination account {ID} not found."}

        - If the amount is zero or negative:
          {"status": "error", "message": "Transfer amount must be positive."}

        - If withdrawal from the source account fails:
          {"status": "error", "message": "Withdrawal failed. Transfer aborted."}

        - If deposit into the destination account fails:
          {"status": "error", "message": "Deposit failed. Transaction rolled back."}

        - If the transfer is successful:
          {"status": "success", "message": f"Successfully transferred ${amount} from Account {srcAccID} to Account {destAccID}."}

    Process
    -------
    1. Validates if both the source and destination accounts exist.
    2. Ensures the transfer amount is a positive value.
    3. Attempts to withdraw the specified amount from the source account.
    4. If the withdrawal is successful, deposits the amount into the destination account.
    5. If the deposit fails, reverses the withdrawal to maintain account balances.

    Notes
    -----
    - The function interacts with `accounts.csv` located in `../csvFiles/`.
    - This ensures **transaction integrity** by rolling back withdrawals if deposits fail.
    """
    # Get absolute path for accounts.csv
    accPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/accounts.csv'))
    
    # Load account data
    accInfo = pd.read_csv(accPath)

    # Validate that both accounts exist
    if srcAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Source account {srcAccID} not found."}
    if destAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Destination account {destAccID} not found."}

    # Ensure the transfer amount is valid
    if amount <= Decimal('0.00'):
        return {"status": "error", "message": "Transfer amount must be positive."}

    # Attempt to withdraw from the source account
    withdraw_result = withdraw(srcAccID, amount)
    if next(iter(withdraw_result.values())) == 'success':
        # If withdrawal succeeds, attempt to deposit into the destination account
        deposit_result = deposit(destAccID, amount)
        if next(iter(deposit_result.values())) == 'success':
            return {"status": "success", "message": f"Successfully transferred ${amount} from Account {srcAccID} to Account {destAccID}."}
        else:
            # Rollback withdrawal if deposit fails
            deposit(srcAccID, amount)  # Refund the withdrawn amount
            return {"status": "error", "message": "Deposit failed. Transaction rolled back."}
    else:
        return {"status": "error", "message": withdraw_result.get("message")}
