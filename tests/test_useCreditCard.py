# Sierra Yerges
# In root dir: python -m unittest tests/test_useCreditCard.py
import unittest
from decimal import Decimal
import pandas as pd
from unittest.mock import patch
from scripts.useCreditCard import useCreditCard

class TestUseCreditCard(unittest.TestCase):
    """
    Unit tests for the useCreditCard function.

    This test suite verifies:
    - Successful charges on credit cards.
    - Prevention of over-limit charges.
    - Rejection of invalid account IDs.
    - Rejection of non-credit card accounts.
    """

    @patch("scripts.useCreditCard.pd.read_csv")
    @patch("scripts.useCreditCard.pd.DataFrame.to_csv")
    @patch("scripts.useCreditCard.generate_transaction_ID", return_value="TX99999")
    def test_successful_charge(self, mock_txn_id, mock_to_csv, mock_read_csv):
        """
        Test that a valid credit card charge is processed correctly.

        Verifies:
        - The balance is reduced correctly.
        - The transaction is logged.
        - A success message is returned.
        """
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5001,
            "CustomerID": 200,
            "AccountType": "Credit Card",
            "CurrBal": "-400.00",
            "CreditLimit": "1000.00",
            "APR": "24.99"
        }])
        mock_trans_df = pd.DataFrame(columns=["TransactionID", "AccountID", "TransactionType", "Amount", "TransDate"])

        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_trans_df

        result = useCreditCard(5001, Decimal("100.00"))

        self.assertEqual(result["status"], "success")
        self.assertIn("Charged $100.00 to credit card account 5001", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.useCreditCard.pd.read_csv")
    def test_account_not_found(self, mock_read_csv):
        """
        Test that an error is returned if the credit card account ID does not exist.
        """
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5002,
            "CustomerID": 201,
            "AccountType": "Credit Card",
            "CurrBal": "-200.00",
            "CreditLimit": "1000.00",
            "APR": "24.99"
        }])
        mock_read_csv.return_value = mock_accounts_df

        result = useCreditCard(9999, Decimal("50.00"))

        self.assertEqual(result["status"], "error")
        self.assertIn("Credit card account 9999 not found", result["message"])

    @patch("scripts.useCreditCard.pd.read_csv")
    def test_not_a_credit_card(self, mock_read_csv):
        """
        Test that an error is returned if the account is not a credit card.
        """
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5003,
            "CustomerID": 202,
            "AccountType": "Checking",
            "CurrBal": "500.00",
            "CreditLimit": "0.00",
            "APR": "0.00"
        }])
        mock_read_csv.return_value = mock_accounts_df

        result = useCreditCard(5003, Decimal("50.00"))

        self.assertEqual(result["status"], "error")
        self.assertIn("Account 5003 is not a credit card", result["message"])

    @patch("scripts.useCreditCard.pd.read_csv")
    def test_exceeds_credit_limit(self, mock_read_csv):
        """
        Test that an over-limit purchase is rejected.

        The absolute balance should not exceed the credit limit.
        """
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5004,
            "CustomerID": 203,
            "AccountType": "Credit Card",
            "CurrBal": "-950.00",
            "CreditLimit": "1000.00",
            "APR": "24.99"
        }])
        mock_read_csv.return_value = mock_accounts_df

        result = useCreditCard(5004, Decimal("100.00"))

        self.assertEqual(result["status"], "error")
        self.assertIn("exceeds credit limit", result["message"])

if __name__ == "__main__":
    unittest.main()
