# Bailee Segars
from Crypto.PublicKey import ECC
import pandas as pd
import random
import os

def login_page_button_pressed(new_or_returning, username, password):
    """
    Handles user account creation and login authentication.

    Parameters
    ----------
    new_or_returning: {1, 2}
        Passed from GUI based on which button a user presses.

        - 1: 'Create Account' button pressed

        - 2: 'Login' button pressed

    username, password: string
        Passed from text fields on log in screen of GUI.

    See Also:
    ---------
    Digital signature standard at D.1.2: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf

    """
    custPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../csvFiles/accounts.csv'))

    def new_account(userID, pwd):
        """
        Creates a new private key for each new user, then saves private key to file associated with userID.

        Parameters
        ----------
        userID: int
            Random number between 200-999 generated when a user creates an account.
        pwd: string
            User created password in text field on GUI.

        Notes
        -----
        new_account uses ECC method `export_key` with the following parameters:
        - `format='PEM'`: Key is encoded in a PEM envelope
        - `use_pkcs8=True`: Uses PKCS#8 standard for encoding asymmetric private keys
        - `protection='PBKDF2WithHMAC-SHA512AndAES128-CBC'`: Uses SHA512 hash and AES256-CBC cipher
        - `compress=True`: Compresses the representation of the public key
        - `prot_params`: dict with the parameters to derive the encryption key
            - `iteration_count`: Repeatedly uses KDF algorithm to slow down brute force attacks. 210000 is recommended for PBKDF2 with SHA512

        """
        key = ECC.generate(curve='p256') # See DSS for information on p256 curve type
        with open(f'{userID}privatekey.pem', 'wt') as f:
            data = key.export_key(format='PEM',
                                passphrase=pwd,
                                use_pkcs8=True,
                                protection='PBKDF2WithHMAC-SHA512AndAES128-CBC',
                                compress=True,
                                prot_params={'iteration_count':210000})
            f.write(data)

    def existing_account(userID, pwd) -> dict:
        """
        Imports an ECC key and uses the given password to decrypt the private key.

        Parameters
        ----------
        userID: int
            Number associated with username.
        pwd: string
            Password user entered in text field.

        Returns
        -------
        dict
            A dictionary containing the status and message.

            - If username and/or password entered incorrectly:\n
            {"status": "error", "message": f"Incorrect username or password. Please try again"}
        """
        with open(f'{userID}privatekey.pem', 'rt') as f:
            data = f.read()
            key = ECC.import_key(data, pwd)

    # Imports customer csv as a dataframe
    userID = pd.read_csv(custPath)

    # Create account
    if new_or_returning == 1:
        newID = random.randint(200, 999) # generates a random ID
        new_account(newID, password)     # generates a new private key
        newUserRow = {'username': username, 'CustomerID': newID}    # creates dict of new user information
        userID.loc[len(userID)] = newUserRow                        # adds information from dict to end of dataframe
        userID.to_csv(custPath, index=False)                 # exports dataframe to customer.csv to overwrite with new information
    # Login
    elif new_or_returning == 2:
        try:
            oldID = userID.loc[userID['username'] == username, 'CustomerID'].iloc[0]    # finds userID from username
            existing_account(oldID, password)                                           # imports private key
        except ValueError:
            return {"status": "error", "message": f"Incorrect username or password. Please try again"}  # if password is incorrect. Should make actual error on GUI