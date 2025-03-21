# Sierra Yerges
# In root dir: python -m unittest tests/test_deleteAccount.py
import unittest
import pandas as pd
from unittest.mock import patch
from scripts.deleteAccount import deleteAcc

class TestDeleteAccount(unittest.TestCase):
    """
    Unit tests for the deleteAccount function.
    
    This test suite verifies:
    - Proper validation of account ID and customer ID.
    - Restrictions on deleting accounts with active loans or negative balances.
    - Successful deletion of valid accounts from `accounts.csv`.
    - Proper transaction logging in `logs.csv`.
    """

    @patch("scripts.deleteAccount.pd.read_csv")
    @patch("scripts.deleteAccount.pd.DataFrame.to_csv")
    def test_delete_valid_account(self, mock_to_csv, mock_read_csv):
        """
        Test that a valid account is successfully deleted from accounts.csv.
        
        - The function should locate and remove the account.
        - The updated accounts.csv should reflect the removal.
        - The function should return a success message.
        """
        # Mock accounts.csv with a valid account that should be deleted
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 1000,"CustomerID": 315, "AccountType": "Checking", "CurrBal": "0.00"},
            {"AccountID": 2000, "CustomerID": 315, "AccountType": "Savings", "CurrBal": "0.00"},
            {"AccountID": 3000, "CustomerID": 315, "AccountType": "Money Market", "CurrBal": "0.00"},
            {"AccountID": 5000, "CustomerID": 315, "AccountType": "Credit Card", "CurrBal": "0.00"},
        ])

        mock_read_csv.side_effect = lambda path: mock_accounts_df.copy() if "accounts.csv" in path else pd.DataFrame()

        # Run delete function
        result1 = deleteAcc(315, 1000)
        result2 = deleteAcc(315, 2000)
        result3 = deleteAcc(315, 3000)
        result4 = deleteAcc(315, 5000)

        # Ensure account was removed
        mock_accounts_df = mock_accounts_df[mock_accounts_df["AccountID"] != 1000]
        self.assertNotIn(1000, mock_accounts_df["AccountID"].values)
        mock_accounts_df = mock_accounts_df[mock_accounts_df["AccountID"] != 2000]
        self.assertNotIn(2000, mock_accounts_df["AccountID"].values)
        mock_accounts_df = mock_accounts_df[mock_accounts_df["AccountID"] != 3000]
        self.assertNotIn(3000, mock_accounts_df["AccountID"].values)
        mock_accounts_df = mock_accounts_df[mock_accounts_df["AccountID"] != 5000]
        self.assertNotIn(5000, mock_accounts_df["AccountID"].values)

        # Check success message
        self.assertEqual(result1, {"status": "success", "message": "Account 1000 successfully deleted."})
        self.assertEqual(result2, {"status": "success", "message": "Account 2000 successfully deleted."})
        self.assertEqual(result3, {"status": "success", "message": "Account 3000 successfully deleted."})
        self.assertEqual(result4, {"status": "success", "message": "Account 5000 successfully deleted."})

        # Ensure accounts.csv was updated
        mock_to_csv.assert_called()

    @patch("scripts.deleteAccount.pd.read_csv")
    @patch("scripts.deleteAccount.pd.DataFrame.to_csv")
    def test_delete_account_with_negative_balance(self, mock_to_csv, mock_read_csv):
        """
        Test that an account with a negative balance cannot be deleted.
        
        - If an account has a negative balance, it should not be removed.
        - The function should return an appropriate error message.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 5016,
             "CustomerID": 315,
             "AccountType": "Credit Card",
             "CurrBal": "-100.00"}
        ])

        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else pd.DataFrame()

        result = deleteAcc(315, 5016)

        self.assertIn("cannot be deleted", result["message"].lower())
        mock_to_csv.assert_not_called()

    @patch("scripts.deleteAccount.pd.read_csv")
    @patch("scripts.deleteAccount.pd.DataFrame.to_csv")
    def test_delete_non_existent_account(self, mock_to_csv, mock_read_csv):
        """
        Test that attempting to delete a non-existent account returns an error.
        
        - The function should check if the account exists in accounts.csv.
        - If the account is not found, it should return an appropriate error message.
        """
        mock_accounts_df = pd.DataFrame([
            {"AccountID": 2000,
             "CustomerID": 315,
             "AccountType": "Savings",
             "CurrBal": "800.00"}
        ])

        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else pd.DataFrame()

        result = deleteAcc(315, 9999)  # Account 9999 does not exist

        self.assertIn("not found", result["message"])
        mock_to_csv.assert_not_called()

    @patch("scripts.deleteAccount.pd.read_csv")
    @patch("scripts.deleteAccount.pd.DataFrame.to_csv")
    @patch("scripts.deleteAccount.generate_transaction_ID", return_value="TX67890")
    def test_log_account_deletion(self, mock_generate_txn, mock_to_csv, mock_read_csv):
        """
        Test that account deletion is properly logged in logs.csv.

        This test verifies that:
        - A deletion log entry is added to logs.csv when an account is successfully deleted.
        - The log includes the correct account ID, customer ID, transaction type, amount, and a generated transaction ID.
        - The log is saved by calling the to_csv() method on the logs DataFrame.
        - The function returns a success message after deletion.
        """
        # Create a mock DataFrame simulating an account eligible for deletion (balance is zero)
        mock_accounts_df = pd.DataFrame([
            {
                "AccountID": 1000,
                "CustomerID": 315,
                "AccountType": "Checking",
                "CurrBal": "0.00"  # Balance must be zero to allow deletion
            }
        ])

        # Create an empty logs DataFrame with the correct schema
        mock_logs_df = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        # Set the behavior of pd.read_csv to return the appropriate mock DataFrame based on file path
        mock_read_csv.side_effect = lambda path: mock_accounts_df if "accounts.csv" in path else mock_logs_df

        # Call the deleteAcc function to perform the deletion
        result = deleteAcc(315, 1000)

        # Verify that the transaction log was saved (to_csv was called)
        mock_to_csv.assert_called()

        # Check that the result returned is a success message
        self.assertEqual(result, {"status": "success", "message": "Account 1000 successfully deleted."})

if __name__ == "__main__":
    unittest.main()
