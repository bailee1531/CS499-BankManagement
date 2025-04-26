# Spring 2025 Authors: Bailee Segars
import unittest
from decimal import Decimal
import pandas as pd
from unittest.mock import patch
from scripts.customer.openAcc import open_account

class TestOpenAccount(unittest.TestCase):
    """
    Unit tests for open_account function.

    This suite covers:
    - Valid initial balance
    - Invalid initial balance
    """

    def _mock_accounts_df(self, accType, newBal="1000.00"):
        return pd.DataFrame([
            {"CustomerID": 151, "AccountType": accType, "CurrBal": newBal},
        ])

    @patch("scripts.customer.openAcc.pd.read_csv")
    @patch("scripts.customer.openAcc.pd.DataFrame.to_csv")
    def test_invalid_account(self, mock_to_csv, mock_read_csv):
        """
        Test that an account is not opened with a negative balance.
        """
        validAccounts = ['Checking', 'Savings', 'Money Market']

        for account in validAccounts:
            with self.subTest(accType=account):
                mock_read_csv.return_value = self._mock_accounts_df(account)
                result = open_account(151, account, Decimal("-50.00"))
                mock_to_csv.assert_not_called()
                self.assertEqual(result["status"], "error")

    @patch("scripts.customer.openAcc.pd.read_csv")
    @patch("scripts.customer.openAcc.pd.DataFrame.to_csv")
    def test_valid_account(self, mock_to_csv, mock_read_csv):
        """
        Test that an account is opened with a non-negative balance.
        """
        validAccounts = ['Checking', 'Savings', 'Money Market']

        for account in validAccounts:
            with self.subTest(accType=account):
                mock_read_csv.return_value = self._mock_accounts_df(account)
                result = open_account(151, account, Decimal("50.00"))
                mock_to_csv.assert_called()
                self.assertEqual(result["status"], "success")

if __name__ == "__main__":
    unittest.main()