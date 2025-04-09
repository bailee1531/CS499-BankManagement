# Bailee Segars
import pandas as pd
import random
import os

def create_teller(firstName, lastName):
    """
    Creates a new teller account.

    Parameters
    ----------
    name: string
        Employee's name.
    """
    employeePath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/employees.csv'))
    logPath = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../csvFiles/logs.csv'))
    employeeInfo = pd.read_csv(employeePath)
    logData = pd.read_csv(logPath)

    employeeID = random.randint(1299, 5999)
    while employeeID in employeeInfo['EmployeeID'].values:
        employeeID = random.randint(1299, 5999)

    username = firstName + '.' + lastName
    newEmployeeRow = {'Username': username,
                      'EmployeeID': employeeID,
                      'Position': 'Teller'}
    
    employeeInfo.loc[len(employeeInfo)] = newEmployeeRow
    employeeInfo.to_csv(employeePath, index=False)

    log_id = random.randint(1299, 5999)
    while log_id in logData['LogID'].values:
        log_id = random.randint(1299, 5999)

    newLog = {'LogID': log_id, 'UserID': employeeID, 'LogMessage': 'Created a New Teller Account'}
    logData.loc[len(logData)] = newLog

    logData.to_csv(logPath, index=False)
