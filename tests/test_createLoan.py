# Sierra Yerges
# In root dir: python -m unittest tests/test_createLoan.py
import unittest
from decimal import Decimal
import pandas as pd
from unittest.mock import patch
from scripts.createLoan import createMortgageLoanAccount

class TestCreateMortgageLoanAccount(unittest.TestCase):
    """
    Unit tests for createMortgageLoanAccount function.

    This suite covers:
    - Successful account creation for valid customers.
    - Error handling for invalid customers.
    - Edge cases such as zero loan amount or negative term.
    - APR range selection based on APRRangeID.
    """

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_valid_customer_creates_account(self, mock_to_csv, mock_read_csv):
        """
        Test that a mortgage loan account is created for a valid customer.

        Verifies:
        - Customer exists and account is added.
        - Response contains success status and loan duration.
        - Data is written via to_csv.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"]),
            pd.DataFrame([{"CustomerID": 123, "APRRangeID": 2}])
        ]

        result = createMortgageLoanAccount(123, Decimal("250000.00"), 30)

        self.assertEqual(result["status"], "success")
        self.assertIn("Mortgage loan account", result["message"])
        self.assertIn("30 years", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.createLoan.pd.read_csv")
    def test_invalid_customer(self, mock_read_csv):
        """
        Test that an error is returned if the customer ID does not exist.

        Verifies:
        - Empty customer dataset returns error.
        - Appropriate error message is returned.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame(columns=["AccountID"]),
            pd.DataFrame(columns=["CustomerID", "APRRangeID"])
        ]

        result = createMortgageLoanAccount(999, Decimal("150000.00"), 15)

        self.assertEqual(result["status"], "error")
        self.assertIn("Customer 999 not found", result["message"])

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_zero_loan_amount(self, mock_to_csv, mock_read_csv):
        """
        Test edge case where the loan amount is zero.

        Verifies:
        - Function still creates account if allowed.
        - Response includes success message.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"]),
            pd.DataFrame([{"CustomerID": 124, "APRRangeID": 1}])
        ]

        result = createMortgageLoanAccount(124, Decimal("0.00"), 15)

        self.assertEqual(result["status"], "success")
        self.assertIn("Mortgage loan account", result["message"])

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_negative_term_years(self, mock_to_csv, mock_read_csv):
        """
        Test edge case where the loan term is negative.

        Verifies:
        - Function does not crash on negative terms.
        - Still creates a loan entry if no validation is implemented.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"]),
            pd.DataFrame([{"CustomerID": 125, "APRRangeID": 3}])
        ]

        result = createMortgageLoanAccount(125, Decimal("100000.00"), -5)

        self.assertEqual(result["status"], "success")
        self.assertIn("-5 years", result["message"])

    @patch("scripts.createLoan.pd.read_csv")
    @patch("scripts.createLoan.pd.DataFrame.to_csv")
    def test_apr_range_selection(self, mock_to_csv, mock_read_csv):
        """
        Test that APR is correctly assigned based on APRRangeID.

        Verifies:
        - APR falls within expected range for APRRangeID = 4 (6.6 to 7.5).
        - Message reflects range assignment.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"]),
            pd.DataFrame([{"CustomerID": 126, "APRRangeID": 4}])
        ]

        result = createMortgageLoanAccount(126, Decimal("180000.00"), 20)

        self.assertEqual(result["status"], "success")
        self.assertRegex(result["message"], r"interest rate of (6\.|7\.)")  # Matches 6.x or 7.x APRs

if __name__ == "__main__":
    unittest.main()
