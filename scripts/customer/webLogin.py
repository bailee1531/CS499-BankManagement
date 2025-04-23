# Bailee Segars
from Crypto.PublicKey import ECC
import pandas as pd
import hashlib
import random
import os

def login_page_button_pressed(new_or_returning, type, username: str, password, *argv):
    """
    Handles user account creation and login authentication.

    Parameters
    ----------
    new_or_returning: {1, 2}
        Passed from GUI based on which button a user presses.

        - 1: 'Create Account' button pressed

        - 2: 'Login' button pressed

    type, username, password, ssn, q1, q2: string
        Passed from text fields on log in screen of GUI.

    See Also:
    ---------
    Digital signature standard at D.1.2: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf

    """
    custPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/customers.csv'))
    perPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/persons.csv'))
    employeePath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/employees.csv'))
    logsPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/logs.csv'))

    def new_account(userID) -> dict:
        """
        Creates a new private key for each new user, then saves private key to file associated with userID.

        Parameters
        ----------
        userID: int
            Random number between 200-999 generated when a user creates an account.

        Returns
        -------
        dict
            A dictionary containing the status and message.

            If the account is created:
            - {"status": "success", "message": "Successfully created account"}

        Notes
        -----
        - APR range ID is assigned using: hash(ssn) % 4 + 1
        - new_account uses ECC method `export_key` with the following parameters:
            - `format='PEM'`: Key is encoded in a PEM envelope
            - `use_pkcs8=True`: Uses PKCS#8 standard for encoding asymmetric private keys
            - `protection='PBKDF2WithHMAC-SHA512AndAES256-CBC'`: Uses SHA512 hash and AES256-CBC cipher
            - `compress=True`: Compresses the representation of the public key
            - `prot_params`: dict with the parameters to derive the encryption key
                - `iteration_count`: Repeatedly uses KDF algorithm to slow down brute force attacks. 210000 is recommended for PBKDF2 with SHA512
        """
        key = ECC.generate(curve='p256') # See DSS for information on p256 curve type
        with open(f'{userID}privatekey.pem', 'wt') as f:
            data = key.export_key(format='PEM',
                                passphrase=password,
                                use_pkcs8=True,
                                protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
                                compress=True,
                                prot_params={'iteration_count':210000})
            f.write(data)

        if type == 'Customer':
            aprRangeID = hash(ssn) % 4 + 1  # Generates ID between 1 and 4
            
            newCustRow = {'Username': username,
                        'CustomerID': newID,
                        'APRRangeID': aprRangeID}        # creates dict of new user information
            custInfo.loc[len(custInfo)] = newCustRow     # adds information from dict to end of dataframe
            custInfo.to_csv(custPath, index=False)       # exports dataframe to customer.csv to overwrite with new information

            logID = random.randint(1299, 5999)
            while logID in logInfo['LogID'].values:
                logID = random.randint(1299, 5999)

            print(logID)
            newLogRow = {'LogID': logID, 'UserID': newID, 'LogMessage': 'New Customer Created'}
            logInfo.loc[len(logInfo)] = newLogRow
            logInfo.to_csv(logsPath, index=False)
        else:
            employeeIndex = employeeInfo[(employeeInfo['EmployeeID'] == newID)]
            if employeeIndex.empty:
                return {"status": "error", "message": "Cannot create user account until employee account has been created by the administrator."}

            logID = random.randint(1299, 5999)
            while logID in logInfo['LogID'].values:
                logID = random.randint(1299, 5999)
            newLogRow = {'LogID': logID, 'UserID': newID, 'LogMessage': 'Teller Has Set Up Log In'}
            logInfo.loc[len(logInfo)] = newLogRow
            logInfo.to_csv(logsPath, index=False)
            
        newPerRow = {'UserType': type,
                     'ID': newID,
                     'LastName': lastName,
                     'FirstName': firstName,
                     'Address': address,
                     'Email': email,
                     'PhoneNum': phoneNum,
                     'Question1': hashlib.sha512(q1.encode()).hexdigest(),
                     'Question2': hashlib.sha512(q2.encode()).hexdigest()}
        perInfo.loc[len(perInfo)] = newPerRow
        perInfo.to_csv(perPath, index=False)
        return {"status": "success", "message": "Successfully created account"}

    def existing_account(userID) -> dict:
        """
        Imports an ECC key and uses the given password to decrypt the private key.

        Parameters
        ----------
        userID: int
            Number associated with username.

        Returns
        -------
        dict
            A dictionary containing the status and message.

            If username and/or password entered incorrectly:
            - {"status": "error", "message": "Incorrect username or password. Please try again"}

            If username and password are correct:
            - {"status": "success", "message": f"Successfully logged in as {username}"}
        """
        with open(f'{userID}privatekey.pem', 'rt') as f:
            try:
                data = f.read()
                key = ECC.import_key(data, password)
            except ValueError:
                return {"status": "error", "message": "Incorrect username or password. Please try again"}
        return {"status": "success", "message": f"Successfully logged in as {username}"}   

    # Imports customer csv as a dataframe
    perInfo = pd.read_csv(perPath)
    custInfo = pd.read_csv(custPath)
    employeeInfo = pd.read_csv(employeePath)
    logInfo = pd.read_csv(logsPath)

    # Create account
    if new_or_returning == 1:
        firstName = argv[0]
        lastName = argv[1]
        address = argv[2]
        email = argv[3]
        phoneNum = argv[4]
        ssn = argv[5]
        q1 = argv[6]
        q2 = argv[7]
        if type == 'Customer':
            newID = random.randint(200, 999) # generates a random ID
            while newID in perInfo['ID'].values:
                newID = random.randint(200, 999)
        else:
            newID = employeeInfo.loc[employeeInfo['Username'] == username, 'EmployeeID'].iloc[0]
        return new_account(newID)     # generates a new private key
    # Login
    elif new_or_returning == 2:
        if type == 'Customer':
            oldID = custInfo.loc[custInfo['Username'] == username, 'CustomerID'].iloc[0]    # finds userID from username
        else:
            oldID = employeeInfo.loc[employeeInfo['Username'] == username, 'EmployeeID'].iloc[0]
        return existing_account(oldID)