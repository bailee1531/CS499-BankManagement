# Bailee Segars
import pandas as pd
import random
import os

def create_teller(name):
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

    newEmployeeRow = {'EmployeeID': employeeID,
                      'EmployeeName': name,
                      'Position': 'Teller'}
    
    employeeInfo.loc[len(employeeInfo)] = newEmployeeRow
    employeeInfo.to_csv(employeePath, index=False)