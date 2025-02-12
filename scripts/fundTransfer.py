# Sierra Yerges
import pandas as pd
from withdrawMoney import withdraw
from makeDeposit import deposit

def transferFunds(srcAccID: int, destAccID: int, amount: float) -> dict:
    """
    Transfers funds between two accounts by withdrawing from one and depositing into another.

    Parameters
    ----------
    srcAccID : int
        The source account ID from which funds are being transferred.
    destAccID : int
        The destination account ID to receive the transferred funds.
    amount : float
        The amount of money to be transferred.

    Returns
    -------
    dict
        A dictionary containing the status and a message.

        - If the source or destination account does not exist:
          {"status": "error", "message": "Source/Destination account {ID} not found."}
        
        - If the transfer amount is invalid (zero or negative):
          {"status": "error", "message": "Transfer amount must be positive."}
        
        - If the withdrawal from the source account fails:
          {"status": "error", "message": "Withdrawal failed. Transfer aborted."}
        
        - If the deposit into the destination account fails:
          {"status": "error", "message": "Deposit failed. Transaction rolled back."}
        
        - If the transfer is successful:
          {"status": "success", "message": "Successfully transferred ${amount} from Account {srcAccID} to Account {destAccID}."}

    Notes
    -----
    - The function reads from `accounts.csv` located in `../csvFiles/`.
    - This function first withdraws funds from the source account.
    - If the withdrawal is successful, it attempts to deposit the funds into the destination account.
    - If the deposit fails, the function **rolls back** the withdrawal to maintain data integrity.
    """
    # Path to the accounts CSV file
    accPath = '../csvFiles/accounts.csv'
    
    # Load account data
    accInfo = pd.read_csv(accPath)

    # Validate that both accounts exist
    if srcAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Source account {srcAccID} not found."}
    if destAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Destination account {destAccID} not found."}

    # Ensure the transfer amount is valid
    if amount <= 0:
        return {"status": "error", "message": "Transfer amount must be positive."}

    # Attempt to withdraw from the source account
    withdraw_result = withdraw(srcAccID, amount)
    if withdraw_result:
        # If withdrawal succeeds, attempt to deposit into the destination account
        deposit_result = deposit(destAccID, amount)
        if deposit_result:
            return {"status": "success", "message": f"Successfully transferred ${amount} from Account {srcAccID} to Account {destAccID}."}
        else:
            # Rollback withdrawal if deposit fails
            deposit(srcAccID, amount)  # Refund the withdrawn amount
            return {"status": "error", "message": "Deposit failed. Transaction rolled back."}
    else:
        return {"status": "error", "message": "Withdrawal failed. Transfer aborted."}
