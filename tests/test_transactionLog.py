# Spring 2025 Authors: Bailee Segars
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.transactionLog import generate_transaction_ID

class TestDeposit(unittest.TestCase):
    """
    Unit tests for the generate_transaction_ID function in transactionLog.py

    This suite tests:
    - Successful unique transaction ID creation
    """
    
    def test_valid_ID(self):
        """
        Test that transaction ID generation returns a unique value
        """
        result = generate_transaction_ID({'TransactionID': 1001})
        self.assertNotEqual(result, 1001)

if __name__ == "__main__":
    unittest.main()