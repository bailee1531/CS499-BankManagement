# Spring 2025 Authors: Bailee Segars
from Crypto.PublicKey import ECC
import pandas as pd
import hashlib
import os

def forgot_password(userID, q1, q2, newPwd):
    """
    Checks validity of hashed answers to security questions and changes the password.

    Parameters
    ----------
    userID: int
        Number associated with username.
    q1: string
        Answer user entered in the text field for question 1.
    q2: string
        Answer user entered in the text field for question 2.
    newPwd: string
        Password user entered in text field.

    Returns
    -------
    dict
        A dictionary containing the status and message.

        If account number does not exist:
        - return {"status": "error", "message": f"Source account {userID} not found."}

        If the answers to both security questions are correct and the password is changed:
        - {"status": "success", "message": "Successfully changed password"}

        If at least one of the answers is incorrect:
        - {"status": "error", "message": "Incorrect answer to at least one security question"}
    """
    perPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/persons.csv'))
    userInfo = pd.read_csv(perPath)

    if userID not in userInfo['ID'].values:
        return {"status": "error", "message": f"Source account {userID} not found."}

    userIndex = userInfo.loc[userInfo['ID'] == userID].index[0]
    answer1 = userInfo.at[userIndex, 'Question1']
    answer2 = userInfo.at[userIndex, 'Question2']

    if (answer1 == hashlib.sha512(q1.encode()).hexdigest()) and (answer2 == hashlib.sha512(q2.encode()).hexdigest()):
        key = ECC.generate(curve='p256')
        with open(f'{userID}privatekey.pem', 'wt') as f:
            data = key.export_key(format='PEM',
                                passphrase=newPwd,
                                use_pkcs8=True,
                                protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
                                compress=True,
                                prot_params={'iteration_count':210000})
            f.write(data)
        return {"status": "success", "message": "Successfully changed password"}
    else:
        return {"status": "error", "message": "Incorrect answer to at least one security question"}