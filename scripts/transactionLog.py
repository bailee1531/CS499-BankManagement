# Spring 2025 Authors: Bailee Segars, Sierra Yerges
import pandas as pd
import random

def generate_transaction_ID(logInfo) -> int:
    """
    Generates a unique transaction ID for each transaction.

    Parameters
    ----------
    logInfo: dataframe
        Dataframe of log information from logs.csv.

    Returns
    -------
    transactionID: int
        ID associated with the transaction.
    """
    transactionID = random.randint(999, 9999) # generates a random ID
    if transactionID not in logInfo:
        return transactionID
    generate_transaction_ID(logInfo)