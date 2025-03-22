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

    def _mock_accounts_df(self, src_type, dest_type, src_bal="1000.00", dest_bal="500.00"):
        return pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": src_type, "CurrBal": src_bal},
            {"AccountID": 202, "CustomerID": 1, "AccountType": dest_type, "CurrBal": dest_bal},
        ])

    def _mock_success(self, *args, **kwargs):
        return {"status": "success", "message": "Success"}

    def _mock_blocked(self, *args, **kwargs):
        return {"status": "error", "message": "Not allowed"}

    @patch("scripts.fundTransfer.deposit")
    @patch("scripts.fundTransfer.withdraw")
    @patch("scripts.fundTransfer.pd.read_csv")
    def test_valid_account_type_transfers(self, mock_read_csv, mock_withdraw, mock_deposit):
        valid_combinations = [
            ("Checking", "Checking"),
            ("Checking", "Savings"),
            ("Checking", "Credit Card"),
            ("Checking", "Mortgage Loan"),
            ("Savings", "Checking"),
            ("Savings", "Savings"),
            ("Savings", "Credit Card"),
            ("Savings", "Mortgage Loan"),
        ]

        for src, dest in valid_combinations:
            with self.subTest(src_type=src, dest_type=dest):
                mock_read_csv.return_value = self._mock_accounts_df(src, dest)
                mock_withdraw.side_effect = self._mock_success
                mock_deposit.side_effect = self._mock_success

                result = transferFunds(101, 202, Decimal("100.00"))
                self.assertEqual(result["status"], "success")

    @patch("scripts.fundTransfer.deposit")
    @patch("scripts.fundTransfer.withdraw")
    @patch("scripts.fundTransfer.pd.read_csv")
    def test_invalid_account_type_transfers(self, mock_read_csv, mock_withdraw, mock_deposit):
        invalid_combinations = [
            ("Credit Card", "Checking"),
            ("Credit Card", "Savings"),
            ("Credit Card", "Mortgage Loan"),
            ("Mortgage Loan", "Checking"),
            ("Mortgage Loan", "Savings"),
            ("Mortgage Loan", "Credit Card"),
        ]

        for src, dest in invalid_combinations:
            with self.subTest(src_type=src, dest_type=dest):
                mock_read_csv.return_value = self._mock_accounts_df(src, dest)
                mock_withdraw.side_effect = self._mock_blocked
                mock_deposit.side_effect = self._mock_blocked

                result = transferFunds(101, 202, Decimal("100.00"))
                self.assertEqual(result["status"], "error")
                self.assertIn("fail", result["message"].lower() or "not allowed")

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
    def test_invalid_transfer_amounts(self, mock_read_csv):
        """
        Test that transfer fails if amount is zero or negative.
        """
        # Mock valid accounts
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 101, "CustomerID": 1, "AccountType": "Checking", "CurrBal": "300.00"},
            {"AccountID": 202, "CustomerID": 1, "AccountType": "Savings", "CurrBal": "200.00"},
        ])
        mock_read_csv.return_value = mock_accounts_df

        for invalid_amount in [Decimal("0.00"), Decimal("-100.00")]:
            with self.subTest(amount=invalid_amount):
                result = transferFunds(101, 202, invalid_amount)
                self.assertEqual(result, {
                    "status": "error",
                    "message": "Transfer amount must be positive."
                })

if __name__ == "__main__":
    unittest.main()
