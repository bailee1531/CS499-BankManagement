# Bailee Segars
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.calcInterest import accrue_interest


class TestDeposit(unittest.TestCase):
    """
    Unit tests for the accrue_interest function in calcInterest.py.

    This suite tests:
    - Successful interest accrual on current balance in valid account types
    """

    def _mock_accounts_df(self, accType="Savings", curr_bal="1000.00"):
        return pd.DataFrame([
            {"AccountType": accType, "CurrBal": curr_bal}
        ])

    
    @patch("scripts.calcInterest.pd.read_csv")
    def test_valid_account_types(self, mock_read_csv):
        """
        Test that accrual succeeds with valid account type
        """
        validTypes = ["Savings", "Money Market"]

        for type in validTypes:
            with self.subTest(accType=type):
                mock_read_csv.return_value = self._mock_accounts_df(type)

                accrue_interest(type)

if __name__ == "__main__":
    unittest.main()