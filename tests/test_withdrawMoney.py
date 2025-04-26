# Spring 2025 Authors: Bailee Segars
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.withdrawMoney import withdraw


class TestDeposit(unittest.TestCase):
    """
    Unit tests for the withdraw function in withdrawMoney.py.

    This suite tests:
    - Successful withdrawl
    - Failed withdrawal with insufficient funds
    - Invalid account IDs
    """

    def _mock_accounts_df(self, accType="Checking", curr_bal="1000.00"):
        return pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": accType, "CurrBal": curr_bal, "CreditLimit": "3000.00"},
        ])

    def _mock_success(self, *args):
        return {"status": "success", "message": "Success"}
    
    @patch("scripts.withdrawMoney.withdraw")
    @patch("scripts.withdrawMoney.pd.read_csv")
    def test_valid_account_types(self, mock_read_csv, mock_withdraw):
        """
        Test that withdrawal succeeds with correct account type and sufficient funds
        """
        validTypes = ["Checking", "Savings"]

        for type in validTypes:
            with self.subTest(accType=type):
                mock_read_csv.return_value = self._mock_accounts_df(type)
                mock_withdraw.side_effect = self._mock_success

                result = withdraw(101, Decimal("100.00"))
                self.assertEqual(result["status"], "success")

    @patch("scripts.withdrawMoney.withdraw")
    @patch("scripts.withdrawMoney.pd.read_csv")
    def test_insufficient_funds(self, mock_read_csv, mock_withdraw):
        """
        Test that withdrawal fails if source account has insufficient funds.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": "Checking", "CurrBal": "50.00", "CreditLimit": "3000.00"},
        ])
    
        mock_read_csv.return_value = mock_accounts_df
        mock_withdraw.return_value = {"status": "error", "message": "Insufficient funds"}

        result = withdraw(101, Decimal("100.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Insufficient funds. Cannot withdraw 100.00 from account 101."
        })

    @patch("scripts.withdrawMoney.pd.read_csv")
    def test_invalid_accounts(self, mock_read_csv):
        """
        Test that withdrawal fails if the account ID is invalid.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 202, "AccountType": "Checking", "CurrBal": "300.00", "CreditLimit": "3000.00"}
        ])
        mock_read_csv.return_value = mock_accounts_df

        result = withdraw(105, Decimal("50.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Source account 105 not found."
        })

if __name__ == "__main__":
    unittest.main()