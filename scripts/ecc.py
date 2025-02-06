import pandas as pd
import random
from Crypto.PublicKey import ECC

# Digital signature standard at D.1.2: https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.186-4.pdf

# Creates a new private key for each new user
# Saves private key to file associated with userID
# format=PEM: Key is encoded in a PEM envelope (ASCII)
# passphrase=pwd: Password user created for account
# use_pkcs8=True: Uses PKCS#8 representation
    # PKCS#8: Standard for encoding asymmetric private keys
    # Offers the best way to securely encrypt the key (vs. PKCS#1)
# protection: 'PBKDF2WithHMAC-' + hash + 'And' + cipher
    # hash: SHA512
    # cipher: AES256-CBC
# compress=True: Compresses the representation of the public key (x coordinate only)
# prot_params: dict with the parameters to derive the encryption key
    # iteration_count: Repeatedly uses KDF algorithm to slow down brute force attacks
    # 210000 is recommended for PBKDF2 with SHA512
def new_account(userID, pwd):
    key = ECC.generate(curve='p256') # See DSS for information on p256 curve type
    with open(f'{userID}privatekey.pem', 'wt') as f:
        data = key.export_key(format='PEM',
                              passphrase=pwd,
                              use_pkcs8=True,
                              protection='PBKDF2WithHMAC-SHA512AndAES128-CBC',
                              compress=True,
                              prot_params={'iteration_count':210000})
        f.write(data)

# Imports an ECC key and uses the given password to decrypt the private key
def existing_account(userID, pwd):
    with open(f'{userID}privatekey.pem', 'rt') as f:
        data = f.read()
        key = ECC.import_key(data, pwd)

# console output. Removing once we have gui
print("Welcome to the bank!\n")
print("Enter the number of the menu option you'd like to select\n")
new_or_returning = int(input("1. Create Account\n2. Login\n"))
username = input("Enter your username.\n")
password = input("Enter your password.\n")

# imports customer csv as a dataframe
userID = pd.read_csv('customers.csv')

# if the user wants to create an account
if new_or_returning == 1:
    newID = random.randint(200, 999) # generates a random ID
    new_account(newID, password)     # generates a new private key
    print("You can now log in!\n")
    newUserRow = {'username': username, 'CustomerID': newID}    # creates dict of new user information
    userID.loc[len(userID)] = newUserRow                        # adds information from dict to end of dataframe
    userID.to_csv('customers.csv', index=False)                 # exports dataframe to customer.csv to overwrite with new information
# if the user has an account
elif new_or_returning == 2:
    try:
        oldID = userID.loc[userID['username'] == username, 'CustomerID'].iloc[0]    # finds userID from username
        existing_account(oldID, password)                                           # imports private key
    except ValueError:
        print('Incorrect username or password. Please try again\n')                 # if password is incorrect
