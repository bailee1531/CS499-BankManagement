# Sierra Yerges
import pandas as pd

# Delete an account if the balance is zero
# custID: Customer ID associated with the account
# accID: Account ID the customer wants to delet
def deleteAcc(custID, accID):
    # accounts.csv path
    accPath = '../csvFiles/accounts.csv'
    # Load account data
    accInfo = pd.read_csv(accPath)

    # Find account in dataset
    accIndex = accInfo[(accInfo['CustomerID'] == custID) & (accInfo['AccountID'] == accID)].index

    # Check if account exists
    if accIndex.empty:
        return {"status": "error", "message": f"Account {accID} not found for Customer {custID}."}
    
    # Check if account balance is zero
    if accInfo.loc[accIndex, 'CurrBal'].values[0] == 0:
        accInfo.drop(accIndex, inplace=True)
        accInfo.to_csv(accPath, index=False)
        return {"status": "success", "message": f"Account {accID} successfully deleted."}
    else:
        return {"status": "error", "message": f"Account {accID} cannot be deleted because it has a non-zero balance."}
