# Bailee Segars
import pandas as pd
import os

def modify_info(userID: int, modifyReq: dict) -> dict:
    perPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/persons.csv'))

    # Load person data
    perInfo = pd.read_csv(perPath)

    userIndex = perInfo.loc[perInfo['ID'] == userID].index[0]

    for key, value in modifyReq.items():
        try:
            perInfo.at[userIndex, key] = value
            perInfo.to_csv(perPath, index=False)
        except:
            return {"status": "error", "message": f"{key} not found."}
        return {"status": "success", "message": f"{key} successfully changed to {value}."}