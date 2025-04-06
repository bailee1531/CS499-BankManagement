# Bailee Segars
import pandas as pd
import random
import os
from scripts.customer.webLogin import login_page_button_pressed

def create_teller(firstName, lastName):
    """
    Creates a new teller account.

    Parameters
    ----------
    name: string
        Employee's name.
    """
    employeePath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/employees.csv'))
    employeeInfo = pd.read_csv(employeePath)

    employeeID = random.randint(1299, 5999)
    while employeeID in employeeInfo['EmployeeID'].values:
        employeeID = random.randint(1299, 5999)

    username = firstName + '.' + lastName
    newEmployeeRow = {'Username': username,
                      'EmployeeID': employeeID,
                      'Position': 'Teller'}
    
    employeeInfo.loc[len(employeeInfo)] = newEmployeeRow
    employeeInfo.to_csv(employeePath, index=False)

    # PEM key for teller account
    login_page_button_pressed(
    1,               # new_or_returning
    "Teller",        # type
    username,        # username
    str(employeeID), # password
    firstName,
    lastName,
    "N/A",
    "teller@email.com",
    "000-000-0000",
    "123-45-6789",
    "What is your favorite?",
    "Nothing."
)

