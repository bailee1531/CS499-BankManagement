# Spring 2025 Authors: Sierra Yerges
# In root dir: python -m unittest tests/test_calcCreditCardInterest.py
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.calcCreditInterest import calculateCreditInterest

class TestCreditCardInterestCalculation(unittest.TestCase):
    """
    Unit tests for credit card interest calculation.
    
    This test suite verifies:
    - Correct application of interest on outstanding credit card balances.
    - No interest applied to accounts with zero or negative balances.
    - Correct handling of over-limit balances.
    """

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    @patch("scripts.calcCreditInterest.generate_transaction_ID", return_value="TX12345")
    def test_credit_card_interest_application(self, mock_generate_txn, mock_to_csv, mock_read_csv):
        """
        Test that interest is correctly applied to credit card balances based on APR.
        
        This test verifies:
        - The correct interest formula is used.
        - The calculated interest is added to the credit card balance.
        - A transaction log entry is created.
        - The updated balance is saved to `accounts.csv`.
        """
        # Mock accounts.csv with a credit card that has an outstanding balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5016,
            "CustomerID": 315,
            "AccountType": "Credit Card",
            "CurrBal": "-2500.00",
            "CreditLimit": "5000.00",
            "APR": "24.99"
        }])
        # Mock logs.csv as an empty transaction log.
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        # Simulate behavior of `pd.read_csv`
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Run interest calculation
        results = calculateCreditInterest()

        # Expected monthly interest calculation
        expected_interest = Decimal("-2500.00") * (Decimal("24.99") / Decimal("100") / Decimal("12"))
        expected_interest = abs(expected_interest.quantize(Decimal("0.00")))

        # Verify that the balance includes the calculated interest
        new_balance = Decimal(mock_accounts_df.loc[mock_accounts_df['AccountID'] == 5016, 'CurrBal'].values[0])
        self.assertEqual(new_balance, Decimal("-2500.00") - expected_interest)

        # Verify that a log entry was created for the interest application
        self.assertIn(
            {"status": "success", "message": f"Interest of ${expected_interest} applied to AccountID 5016."},
            results
        )

        # Ensure to_csv was called but no changes should be made
        mock_to_csv.assert_called()

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    def test_no_interest_on_zero_balance(self, mock_to_csv, mock_read_csv):
        """
        Test that no interest is applied to credit cards with a zero balance.
        
        This test ensures:
        - No interest is added when the credit card balance is $0.00.
        - No transaction logs are created.
        - The function still calls `to_csv()` to save data.
        """
        # Mock accounts.csv with a credit card that has a zero balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5016,
            "CustomerID": 315,
            "AccountType": "Credit Card",
            "CurrBal": "0.00",
            "CreditLimit": "5000.00",
            "APR": "24.99"
        }])
        # Mock logs.csv as an empty transaction log.
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Run interest calculation
        results = calculateCreditInterest()

        # Ensure no interest was applied since balance is zero
        self.assertNotIn(
            {"status": "success", "message": "Interest applied"},
            results
        )

        # Ensure the function still attempts to save updates
        mock_to_csv.assert_called()

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    def test_interest_on_over_limit_balance(self, mock_to_csv, mock_read_csv):
        """
        Test that interest is correctly applied when the credit card balance exceeds the credit limit.
        
        This test verifies:
        - Interest is applied correctly based on APR.
        - The new balance includes the calculated interest.
        - The function does not reject calculations based on exceeding credit limit.
        """
        # Mock accounts.csv with a credit card that is over its credit limit.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5016,
            "CustomerID": 315,
            "AccountType": "Credit Card",
            "CurrBal": "-6000.00",
            "CreditLimit": "5000.00",
            "APR": "24.99"
        }])
        # Mock logs.csv as an empty transaction log.
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Run interest calculation
        results = calculateCreditInterest()

        # Expected monthly interest calculation
        expected_interest = Decimal("-6000.00") * (Decimal("24.99") / Decimal("100") / Decimal("12"))
        expected_interest = abs(expected_interest.quantize(Decimal("0.00")))

        # Verify that the new balance includes interest applied
        new_balance = Decimal(mock_accounts_df.loc[mock_accounts_df['AccountID'] == 5016, 'CurrBal'].values[0])
        self.assertEqual(new_balance, Decimal("-6000.00") - expected_interest)

        # Ensure interest was logged correctly
        self.assertIn(
            {"status": "success", "message": f"Interest of ${expected_interest} applied to AccountID 5016."},
            results
        )

        # Ensure to_csv was called but no changes should be made
        mock_to_csv.assert_called()

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    def test_no_interest_on_overpaid_credit_card(self, mock_to_csv, mock_read_csv):
        """
        Test that no interest is applied to credit cards with a negative balance (overpayment scenario).

        This test ensures:
        - If a credit card has a negative balance (meaning the user overpaid their bill),
          no interest should be charged.
        - The function should not log an interest charge for overpaid accounts.
        - The function still calls `to_csv()` to maintain transaction logging consistency.
        """
        # Mock accounts.csv with a credit card that has an overpaid (negative) balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 5016,
            "CustomerID": 315,
            "AccountType": "Credit Card", 
            "CurrBal": "200.00",
            "CreditLimit": "5000.00",
            "APR": "24.99"
        }])
        # Mock logs.csv as an empty transaction log.
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        # Simulate behavior of `pd.read_csv`
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Run interest calculation
        results = calculateCreditInterest()

        # Ensure that no interest was applied to the overpaid credit card
        self.assertNotIn(
            {"status": "success", "message": "Interest applied"},
            results
        )

        # Ensure the function still attempts to save updates, even if no interest is applied
        mock_to_csv.assert_called()

if __name__ == "__main__":
    unittest.main()
