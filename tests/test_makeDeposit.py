# Bailee Segars
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.makeDeposit import deposit


class TestDeposit(unittest.TestCase):
    """
    Unit tests for the deposit function in makeDeposit.py.

    This suite tests:
    - Successful deposit
    - Invalid account IDs
    """

    def _mock_accounts_df(self, curr_bal="1000.00"):
        return pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": "Checking", "CurrBal": curr_bal, "CreditLimit": "3000.00"},
        ])

    def _mock_success(self, *args):
        return {"status": "success", "message": "Success"}
    
    @patch("scripts.makeDeposit.deposit")
    @patch("scripts.makeDeposit.pd.read_csv")
    def test_valid_deposit(self, mock_read_csv, mock_deposit):
        """
        Test that the deposit is successful if the account ID is valid
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": "Checking", "CurrBal": "300.00", "CreditLimit": "3000.00"}
        ])
        mock_read_csv.return_value = mock_accounts_df
        mock_deposit.side_effect = self._mock_success

        result = deposit(101, Decimal("50.00"))
        self.assertEqual(result["status"], "success")


    @patch("scripts.makeDeposit.pd.read_csv")
    def test_invalid_accounts(self, mock_read_csv):
        """
        Test that deposit fails if the account ID is invalid.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": "Checking", "CurrBal": "300.00", "CreditLimit": "3000.00"}
        ])
        mock_read_csv.return_value = mock_accounts_df

        result = deposit(105, Decimal("50.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Destination account 105 not found."
        })

if __name__ == "__main__":
    unittest.main()