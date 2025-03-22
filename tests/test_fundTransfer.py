# Sierra Yerges
# In root dir: python -m unittest tests/test_fundTransfer.py
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.fundTransfer import transferFunds


class TestFundTransfer(unittest.TestCase):
    """
    Unit tests for the transferFunds function in fundTransfer.py.

    This suite tests:
    - Successful fund transfer
    - Transfer with insufficient funds
    - Invalid account IDs
    - Invalid transfer amounts
    """

    @patch("scripts.fundTransfer.deposit")
    @patch("scripts.fundTransfer.withdraw")
    @patch("scripts.fundTransfer.pd.read_csv")
    def test_successful_transfer(self, mock_read_csv, mock_withdraw, mock_deposit):
        """
        Test that a valid transfer between two accounts deducts and credits the correct amounts.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": "Checking", "CurrBal": "500.00"},
            {"AccountID": 202, "CustomerID": 1, "AccountType": "Savings", "CurrBal": "100.00"},
        ])
        mock_read_csv.return_value = mock_accounts_df
        mock_withdraw.return_value = {"status": "success", "message": "Withdraw successful"}
        mock_deposit.return_value = {"status": "success", "message": "Deposit successful"}

        result = transferFunds(101, 202, Decimal("100.00"))

        self.assertEqual(result, {
            "status": "success",
            "message": "Successfully transferred $100.00 from Account 101 to Account 202."
        })

    @patch("scripts.fundTransfer.deposit")
    @patch("scripts.fundTransfer.withdraw")
    @patch("scripts.fundTransfer.pd.read_csv")
    def test_insufficient_funds(self, mock_read_csv, mock_withdraw, mock_deposit):
        """
        Test that transfer fails if source account has insufficient funds.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": "Checking", "CurrBal": "50.00"},
            {"AccountID": 202, "CustomerID": 1, "AccountType": "Savings", "CurrBal": "100.00"},
        ])
        mock_read_csv.return_value = mock_accounts_df
        mock_withdraw.return_value = {"status": "error", "message": "Insufficient funds"}

        result = transferFunds(101, 202, Decimal("100.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Withdrawal failed. Transfer aborted."
        })

    @patch("scripts.fundTransfer.deposit")
    @patch("scripts.fundTransfer.withdraw")
    @patch("scripts.fundTransfer.pd.read_csv")
    def test_invalid_accounts(self, mock_read_csv, mock_withdraw, mock_deposit):
        """
        Test that transfer fails if either account ID is invalid.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": "Checking", "CurrBal": "300.00"}
        ])
        mock_read_csv.return_value = mock_accounts_df

        result = transferFunds(101, 9999, Decimal("50.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Destination account 9999 not found."
        })

    @patch("scripts.fundTransfer.pd.read_csv")
    def test_invalid_transfer_amount(self, mock_read_csv):
        """
        Test that transfer fails if amount is zero or negative.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": "Checking", "CurrBal": "300.00"},
            {"AccountID": 202, "CustomerID": 1, "AccountType": "Savings", "CurrBal": "200.00"},
        ])
        mock_read_csv.return_value = mock_accounts_df

        result = transferFunds(101, 202, Decimal("0.00"))

        self.assertEqual(result, {
            "status": "error",
            "message": "Transfer amount must be positive."
        })


if __name__ == "__main__":
    unittest.main()
