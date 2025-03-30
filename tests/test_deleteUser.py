# Sierra Yerges
# In root dir: python -m unittest tests/test_deleteUser.py
import unittest
from unittest.mock import patch, mock_open
import pandas as pd
from scripts.customer.deleteUser import delete_user_button_pressed

class TestDeleteUserFunction(unittest.TestCase):
    """
    Unit tests for delete_user_button_pressed function.

    These tests verify:
    - Proper deletion of customers or tellers under valid conditions.
    - Prevention of deletion with active accounts or bills.
    - Password verification using ECC key decryption.
    - Admin privileges bypass password check.
    - Cleanup of CSVs and private key (.pem) files.
    """

    @patch("scripts.customer.deleteUser.os.path.exists")
    @patch("scripts.customer.deleteUser.os.remove")
    @patch("scripts.customer.deleteUser.pd.read_csv")
    @patch("scripts.customer.deleteUser.pd.DataFrame.to_csv")
    @patch("scripts.customer.deleteUser.ECC.import_key")
    def test_customer_deletion_success(self, mock_import, mock_to_csv, mock_read_csv, mock_remove, mock_exists):
        """
        Test successful deletion of a customer with no active accounts or bills and valid password.
        """
        # Simulate all required files and PEM file existing
        mock_exists.side_effect = lambda path: True if path.endswith("privatekey.pem") or ".csv" in path else False

        # Provide mock data
        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 111, "UserType": "Customer"}]),  # persons.csv
            pd.DataFrame(columns=["AccountID", "CustomerID"]),    # accounts.csv (empty)
            pd.DataFrame(columns=["BillID", "CustomerID"]),       # bills.csv (empty)
            pd.DataFrame([{"CustomerID": 111}])                   # customers.csv
        ]

        # Simulate successful private key decryption
        with patch("builtins.open", mock_open(read_data="ECC KEY")):
            result = delete_user_button_pressed("Customer", 111, password="validpass", is_admin=False)

        # Assert successful deletion
        self.assertEqual(result["status"], "success")
        self.assertIn("successfully deleted", result["message"])
        mock_import.assert_called_once()
        mock_to_csv.assert_called()
        mock_remove.assert_called()

    @patch("scripts.customer.deleteUser.os.path.exists")
    @patch("scripts.customer.deleteUser.os.remove")
    @patch("scripts.customer.deleteUser.pd.read_csv")
    @patch("scripts.customer.deleteUser.pd.DataFrame.to_csv")
    def test_admin_deletes_teller_successfully(self, mock_to_csv, mock_read_csv, mock_remove, mock_exists):
        """
        Test that an admin can delete a teller account if no accounts or bills are linked.
        """
        mock_exists.side_effect = lambda path: True if path.endswith("privatekey.pem") or ".csv" in path else False

        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 888, "UserType": "Teller"}]),     # persons.csv
            pd.DataFrame(columns=["AccountID", "CustomerID"]),     # accounts.csv
            pd.DataFrame(columns=["BillID", "CustomerID"]),        # bills.csv
            pd.DataFrame([{"EmployeeID": 888}])                    # employees.csv
        ]

        result = delete_user_button_pressed("Teller", 888, is_admin=True)

        self.assertEqual(result["status"], "success")
        self.assertIn("successfully deleted", result["message"])
        mock_to_csv.assert_called()
        mock_remove.assert_called()

    @patch("scripts.customer.deleteUser.pd.read_csv")
    def test_deletion_fails_with_active_accounts(self, mock_read_csv):
        """
        Test user cannot be deleted if they have active accounts.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 222, "UserType": "Customer"}]),   # persons.csv
            pd.DataFrame([{"AccountID": 1, "CustomerID": 222}]),   # accounts.csv
            pd.DataFrame(columns=["BillID", "CustomerID"])         # bills.csv
        ]

        result = delete_user_button_pressed("Customer", 222, password="pass", is_admin=False)

        self.assertEqual(result["status"], "error")
        self.assertIn("Active accounts", result["message"])

    @patch("scripts.customer.deleteUser.os.path.exists", return_value=False)
    @patch("scripts.customer.deleteUser.pd.read_csv")
    def test_missing_key_file(self, mock_read_csv, mock_exists):
        """
        Test customer deletion fails if PEM key file does not exist.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 333, "UserType": "Customer"}]),
            pd.DataFrame(columns=["AccountID", "CustomerID"]),
            pd.DataFrame(columns=["BillID", "CustomerID"])
        ]

        result = delete_user_button_pressed("Customer", 333, password="any", is_admin=False)

        self.assertEqual(result["status"], "error")
        self.assertIn("Private key file not found", result["message"])

    @patch("scripts.customer.deleteUser.os.path.exists", return_value=True)
    @patch("scripts.customer.deleteUser.pd.read_csv")
    @patch("scripts.customer.deleteUser.ECC.import_key", side_effect=ValueError("Decryption failed"))
    def test_incorrect_password(self, mock_import, mock_read_csv, mock_exists):
        """
        Test decryption failure due to incorrect password blocks deletion.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 444}]),
            pd.DataFrame(columns=["AccountID", "CustomerID"]),
            pd.DataFrame(columns=["BillID", "CustomerID"])
        ]

        with patch("builtins.open", mock_open(read_data="ECC KEY")):
            result = delete_user_button_pressed("Customer", 444, password="wrong", is_admin=False)

        self.assertEqual(result["status"], "error")
        self.assertIn("decryption failed", result["message"])

    @patch("scripts.customer.deleteUser.os.path.exists", return_value=True)
    @patch("scripts.customer.deleteUser.os.remove")
    @patch("scripts.customer.deleteUser.pd.read_csv")
    @patch("scripts.customer.deleteUser.pd.DataFrame.to_csv")
    def test_admin_can_delete_without_password(self, mock_to_csv, mock_read_csv, mock_remove, mock_exists):
        """
        Test that admin can delete customer without password verification.
        """
        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 555, "UserType": "Customer"}]),
            pd.DataFrame(columns=["AccountID", "CustomerID"]),
            pd.DataFrame(columns=["BillID", "CustomerID"]),
            pd.DataFrame([{"CustomerID": 555}])
        ]

        result = delete_user_button_pressed("Customer", 555, is_admin=True)

        self.assertEqual(result["status"], "success")
        self.assertIn("successfully deleted", result["message"])
        mock_to_csv.assert_called()
        mock_remove.assert_called()

    @patch("scripts.customer.deleteUser.os.path.exists")
    @patch("scripts.customer.deleteUser.os.remove")
    @patch("scripts.customer.deleteUser.pd.read_csv")
    @patch("scripts.customer.deleteUser.pd.DataFrame.to_csv")
    @patch("scripts.customer.deleteUser.ECC.import_key")
    def test_teller_deletes_customer_with_password(self, mock_import, mock_to_csv, mock_read_csv, mock_remove, mock_exists):
        """
        Test that a teller (non-admin) can delete a customer account with a valid password.
        """
        mock_exists.side_effect = lambda path: True if path.endswith("privatekey.pem") or ".csv" in path else False

        mock_read_csv.side_effect = [
            pd.DataFrame([{"ID": 777, "UserType": "Customer"}]),
            pd.DataFrame(columns=["AccountID", "CustomerID"]),
            pd.DataFrame(columns=["BillID", "CustomerID"]),
            pd.DataFrame([{"CustomerID": 777}])
        ]

        with patch("builtins.open", mock_open(read_data="ECC KEY")):
            result = delete_user_button_pressed("Customer", 777, password="correctpass", is_admin=False)

        self.assertEqual(result["status"], "success")
        self.assertIn("successfully deleted", result["message"])
        mock_import.assert_called_once()
        mock_to_csv.assert_called()
        mock_remove.assert_called()

if __name__ == "__main__":
    unittest.main()
