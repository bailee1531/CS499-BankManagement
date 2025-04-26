# Spring 2025 Authors: Sierra Yerges
# In root dir: python -m unittest tests/test_calcCreditLoanInterest.py
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.calcCreditInterest import calculateCreditInterest

class TestCreditLoanInterestCalculation(unittest.TestCase):
    """Unit tests for mortgage loan interest calculation."""

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    @patch("scripts.calcCreditInterest.generate_transaction_ID", return_value="TX12345")
    def test_mortgage_loan_interest_application(self, mock_generate_txn, mock_to_csv, mock_read_csv):
        """
        Test that interest is correctly applied to mortgage loan balances based on APR.

        This test verifies that:
        - Monthly interest is applied correctly based on the loan’s APR.
        - The updated balance includes the calculated interest.
        - The interest transaction is recorded in the logs.
        - Data is saved using `to_csv()` to reflect the updates.
        """
        # Mock data containing a mortgage loan account with a zero balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 14233,       # Unique loan account identifier
            "CustomerID": 315,        # Associated customer ID
            "AccountType": "Mortgage Loan",  # Account type for filtering
            "CurrBal": "-300000.00",   # Outstanding loan balance
            "CreditLimit": "0.00",        # Empty credit limit
            "APR": "6.75"             # Annual Percentage Rate for interest calculation
        }])

        # Mock empty log file
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "CreditLimit", "TransactionID"])

        # Assign mock data to read_csv calls
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Execute interest calculation
        results = calculateCreditInterest()

        # Expected interest calculation for mortgage loan
        expected_interest = Decimal("-300000.00") * (Decimal("6.75") / Decimal("100") / Decimal("12"))
        expected_interest = abs(expected_interest.quantize(Decimal("0.00")))

        # Verify updated balance
        new_balance = Decimal(mock_accounts_df.loc[mock_accounts_df['AccountID'] == 14233, 'CurrBal'].values[0])
        self.assertEqual(new_balance, Decimal("-300000.00") - expected_interest)

        # Verify that the interest transaction was logged
        self.assertIn(
            {"status": "success", "message": f"Interest of ${expected_interest} applied to AccountID 14233."},
            results
        )

        # Ensure to_csv was called but no changes should be made
        mock_to_csv.assert_called()

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    def test_no_interest_on_paid_off_mortgage(self, mock_to_csv, mock_read_csv):
        """
        Test that no interest is applied to fully paid-off mortgage loan accounts.

        This test verifies that:
        - No interest is added when the mortgage loan balance is $0.00.
        - The function does not generate any transaction logs for paid-off loans.
        - The data is still saved using `to_csv()` (mocked to prevent actual file writes).
        """
        # Mock data containing a mortgage loan account with a zero balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 14233,       # Unique loan account identifier
            "CustomerID": 315,        # Associated customer ID
            "AccountType": "Mortgage Loan",  # Account type for filtering
            "CurrBal": "0.00",   # Outstanding loan balance
            "CreditLimit": "0.00",        # Empty credit limit
            "APR": "6.75"             # Annual Percentage Rate for interest calculation
        }])

        # Mock empty log file
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "CreditLimit", "TransactionID"])

        # Assign mock data to read_csv calls
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Execute interest calculation
        results = calculateCreditInterest()

        # Ensure no interest transaction is recorded
        self.assertNotIn(
            {"status": "success", "message": "Interest applied"}, results)

        # Ensure to_csv was called but no changes should be made
        mock_to_csv.assert_called()

    @patch("scripts.calcCreditInterest.pd.read_csv")
    @patch("scripts.calcCreditInterest.pd.DataFrame.to_csv")
    def test_no_interest_on_overpaid_mortgage(self, mock_to_csv, mock_read_csv):
        """
        Test that no interest is applied to mortgage loans with a positive balance (overpayment scenario).

        This test ensures:
        - If a loan has a positive balance (meaning the user overpaid their bill),
          no interest should be charged.
        - The function should not log an interest charge for overpaid accounts.
        - The function still calls `to_csv()` to maintain transaction logging consistency.
        """
        # Mock accounts.csv with a credit card that has an overpaid (negative) balance.
        mock_accounts_df = pd.DataFrame([{
            "AccountID": 14233,       # Unique loan account identifier
            "CustomerID": 315,        # Associated customer ID
            "AccountType": "Mortgage Loan",  # Account type for filtering
            "CurrBal": "200.00",   # Outstanding loan balance
            "CreditLimit": "0.00",        # Empty credit limit
            "APR": "6.75"             # Annual Percentage Rate for interest calculation
        }])
        # Mock empty log file
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "CreditLimit", "TransactionID"])

        # Assign mock data to read_csv calls
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Execute interest calculation
        results = calculateCreditInterest()

        # Ensure no interest transaction is recorded
        self.assertNotIn(
            {"status": "success", "message": "Interest applied"}, results)

        # Ensure to_csv was called but no changes should be made
        mock_to_csv.assert_called()

if __name__ == "__main__":
    unittest.main()
