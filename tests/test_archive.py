# Spring 2025 Authors: Sierra Yerges
# In root dir: python -m unittest tests/test_archive.py
import unittest
from unittest.mock import patch
import pandas as pd
from scripts.archive import archive, viewArchivedBills, viewArchivedLoans

class TestArchiveFunctions(unittest.TestCase):
    """
    Unit tests for archive and view functions in archive.py.

    Covers:
    - Archiving bills and loans.
    - Error handling for invalid IDs and record types.
    - Viewing archived records including edge cases for missing or empty data.
    """

    @patch("scripts.archive.os.path.exists", return_value=True)
    @patch("scripts.archive.pd.read_csv")
    @patch("scripts.archive.pd.DataFrame.to_csv")
    def test_archive_valid_bill(self, mock_to_csv, mock_read_csv, mock_exists):
        """
        Test archiving a valid bill record.

        Verifies:
        - Correct bill is archived.
        - Archived file is updated via to_csv.
        """
        mock_bills_df = pd.DataFrame([{"BillID": 1001, "CustomerID": 1, "Amount": "50.00"}])
        mock_archived_df = pd.DataFrame(columns=["BillID", "CustomerID", "Amount"])
        mock_read_csv.side_effect = [mock_bills_df, mock_archived_df]

        result = archive("bill", 1001)
        self.assertEqual(result["status"], "success")
        self.assertIn("archived successfully", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.archive.os.path.exists", return_value=True)
    @patch("scripts.archive.pd.read_csv")
    @patch("scripts.archive.pd.DataFrame.to_csv")
    def test_archive_bill_not_found(self, mock_to_csv, mock_read_csv, mock_exists):
        """
        Test archiving a non-existent bill.

        Verifies:
        - Returns an error if bill ID is not found.
        """
        mock_bills_df = pd.DataFrame([{"BillID": 1002, "CustomerID": 1, "Amount": "75.00"}])
        mock_archived_df = pd.DataFrame(columns=["BillID", "CustomerID", "Amount"])
        mock_read_csv.side_effect = [mock_bills_df, mock_archived_df]

        result = archive("bill", 9999)
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])

    @patch("scripts.archive.os.path.exists", side_effect=lambda path: "accounts.csv" in path or "archivedLoans.csv" in path)
    @patch("scripts.archive.pd.read_csv")
    @patch("scripts.archive.pd.DataFrame.to_csv")
    def test_archive_valid_loan(self, mock_to_csv, mock_read_csv, mock_exists):
        """
        Test archiving a valid mortgage loan with $0 balance.

        Verifies:
        - Loan is archived successfully.
        - to_csv is called to persist archive.
        """
        mock_loan_df = pd.DataFrame([{
            "AccountID": 5001,
            "CustomerID": 2,
            "AccountType": "Mortgage Loan",
            "CurrBal": "0.00",
            "Amount": "200000.00",
            "CreditLimit": "0.00"
        }])
        mock_archived_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "Amount", "CreditLimit"])
        mock_read_csv.side_effect = [mock_loan_df, mock_archived_df]

        result = archive("loan", 5001)
        self.assertEqual(result["status"], "success")
        self.assertIn("archived successfully", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.archive.os.path.exists", return_value=True)
    @patch("scripts.archive.pd.read_csv")
    def test_view_archived_bills(self, mock_read_csv, mock_exists):
        """
        Test viewing archived bills for a customer with existing archived records.
        """
        mock_archived = pd.DataFrame([
            {"BillID": 1001, "CustomerID": 1, "Amount": "50.00"},
            {"BillID": 1002, "CustomerID": 2, "Amount": "60.00"}
        ])
        mock_read_csv.return_value = mock_archived

        results = viewArchivedBills(1)
        self.assertIsInstance(results, list)
        self.assertEqual(results[0]["CustomerID"], 1)

    @patch("scripts.archive.os.path.exists", return_value=False)
    def test_view_archived_bills_file_missing(self, mock_exists):
        """
        Test viewing bills when the archivedBills.csv file does not exist.

        Verifies:
        - Error message is returned if file is missing.
        """
        results = viewArchivedBills(999)
        self.assertEqual(results[0]["status"], "error")
        self.assertIn("No archived bills", results[0]["message"])

    @patch("scripts.archive.os.path.exists", return_value=True)
    @patch("scripts.archive.pd.read_csv")
    def test_view_archived_loans_empty(self, mock_read_csv, mock_exists):
        """
        Test viewing archived loans returns error if no loans exist for the customer.

        Verifies:
        - Even with correct columns, empty data returns an error response.
        """
        mock_archived = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "Amount", "CreditLimit"])
        mock_read_csv.return_value = mock_archived

        results = viewArchivedLoans(999)
        self.assertEqual(results[0]["status"], "error")
        self.assertEqual(results[0]["message"], "No archived mortgage loans found for this customer.")

    def test_invalid_record_type(self):
        """
        Test passing an unsupported record type to archive().

        Verifies:
        - Function returns proper error message for unsupported types.
        """
        result = archive("investment", 123)
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid record type", result["message"])


if __name__ == "__main__":
    unittest.main()
