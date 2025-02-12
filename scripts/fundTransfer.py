# Sierra Yerges
import pandas as pd
from withdrawMoney import withdraw
from makeDeposit import deposit

# Transfer funds between two accounts by withdrawing from one and depositing into another
# srcAccID: Source account ID from which money is being transferred
# destAccID: Destination account ID to receive the funds
# amount: Amount to transfer
def transferFunds(srcAccID, destAccID, amount):
    # accounts.csv path
    accPath = '../csvFiles/accounts.csv'
    # Load account data
    accInfo = pd.read_csv(accPath)

    # Validate accounts exist
    if srcAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Source account {srcAccID} not found."}
    if destAccID not in accInfo['AccountID'].values:
        return {"status": "error", "message": f"Destination account {destAccID} not found."}

    # Ensure valid amount
    if amount <= 0:
        return {"status": "error", "message": "Transfer amount must be positive."}
    
    # Withdraw from source account
    withdraw_result = withdraw(srcAccID, amount)
    if withdraw_result:
        # If withdrawal is successful, deposit into destination account
        deposit_result = deposit(destAccID, amount)
        if deposit_result:
            return {"status": "success", "message": f"Successfully transferred ${amount} from Account {srcAccID} to Account {destAccID}."}
        else:
            # Rollback withdrawal if deposit fails
            deposit(srcAccID, amount)  # Refund the amount back to the source
            return {"status": "error", "message": "Deposit failed. Transaction rolled back."}
    else:
        return {"status": "error", "message": "Withdrawal failed. Transfer aborted."}
    