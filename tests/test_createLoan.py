# Sierra Yerges
# In root dir: python -m unittest tests/test_createLoan.py
import unittest
import pandas as pd
from decimal import Decimal
from unittest.mock import patch
from scripts.createLoan import createMortgageLoanAccount

class TestCreateMortgageLoanAccount(unittest.TestCase):
    """
    Unit tests for createMortgageLoanAccount function.

    This suite verifies:
    - Successful loan creation for valid customers.
    - Proper handling of APR ranges based on APRRangeID.
    - Behavior on edge cases (zero amount, negative terms).
    - Error response for invalid customers.
    """

    def mock_csvs(self, accounts=None, customer_data=None, log_data=None):
        """
        Returns a list of mocked DataFrames in the same order they're read:
        accounts.csv, customers.csv, logs.csv.
        """
        return [
            accounts if accounts is not None else pd.DataFrame(columns=[
                "AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"
            ]),
            customer_data if customer_data is not None else pd.DataFrame(columns=[
                "Username", "CustomerID", "APRRangeID"
            ]),
            log_data if log_data is not None else pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])
        ]

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_valid_customer_creates_account(self, mock_to_csv, mock_read_csv):
        """
        Test that a valid customer results in mortgage loan account creation.

        Verifies:
        - Customer exists with valid APRRangeID.
        - Loan is added to accounts.
        - Transaction is logged in logs.csv.
        """
        mock_read_csv.side_effect = self.mock_csvs(
            customer_data=pd.DataFrame([{"Username": "alice", "CustomerID": 123, "APRRangeID": 2}])
        )
        result = createMortgageLoanAccount(123, Decimal("-250000.00"), 30)
        self.assertEqual(result["status"], "success")
        self.assertIn("Mortgage loan account", result["message"])
        self.assertIn("30 years", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.createLoan.pd.read_csv")
    def test_invalid_customer(self, mock_read_csv):
        """
        Test error is returned when customer ID does not exist.

        Verifies:
        - No match in customers.csv.
        - Proper error response.
        """
        mock_read_csv.side_effect = self.mock_csvs(
            customer_data=pd.DataFrame(columns=["Username", "CustomerID", "APRRangeID"])
        )
        result = createMortgageLoanAccount(999, Decimal("-150000.00"), 15)
        self.assertEqual(result["status"], "error")
        self.assertIn("Customer 999 not found", result["message"])

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_zero_loan_amount(self, mock_to_csv, mock_read_csv):
        """
        Test behavior when the loan amount is zero.

        Verifies:
        - Loan is still created if allowed.
        - System handles it without crashing.
        """
        mock_read_csv.side_effect = self.mock_csvs(
            customer_data=pd.DataFrame([{"Username": "bob", "CustomerID": 124, "APRRangeID": 1}])
        )
        result = createMortgageLoanAccount(124, Decimal("0.00"), 15)
        self.assertEqual(result["status"], "success")
        self.assertIn("Mortgage loan account", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_negative_term_years(self, mock_to_csv, mock_read_csv):
        """
        Test that negative term values are accepted (if no validation).

        Verifies:
        - Account is still created with negative years.
        - Message includes negative term.
        """
        mock_read_csv.side_effect = self.mock_csvs(
            customer_data=pd.DataFrame([{"Username": "sam", "CustomerID": 125, "APRRangeID": 3}])
        )
        result = createMortgageLoanAccount(125, Decimal("-100000.00"), -5)
        self.assertEqual(result["status"], "success")
        self.assertIn("-5 years", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_apr_range_selection(self, mock_to_csv, mock_read_csv):
        """
        Test APR is assigned based on APRRangeID correctly.

        Verifies:
        - APRRangeID = 4 results in rate between 6.6 and 7.5.
        - Output message includes correct APR.
        """
        mock_read_csv.side_effect = self.mock_csvs(
            customer_data=pd.DataFrame([{"Username": "leo", "CustomerID": 126, "APRRangeID": 4}])
        )
        result = createMortgageLoanAccount(126, Decimal("-180000.00"), 20)
        self.assertEqual(result["status"], "success")
        self.assertRegex(result["message"], r"interest rate of (6\.\d{1,2}|7\.\d{1,2})")

if __name__ == "__main__":
    unittest.main()
    