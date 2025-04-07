# Sierra Yerges
# In root dir: python -m unittest tests/test_createCreditCard.py
import unittest
from unittest.mock import patch
import pandas as pd
from scripts.createCreditCard import openCreditCardAccount

class TestOpenCreditCardAccount(unittest.TestCase):

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_valid_customer_credit_card_creation(self, mock_to_csv, mock_read_csv):
        """Test standard account creation for valid customer."""
        customer_df = pd.DataFrame([{"Username": "testuser", "CustomerID": 101, "APRRangeID": 1}])
        accounts_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        logs_df = pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result = openCreditCardAccount(101)
        self.assertEqual(result["status"], "success")
        self.assertIn("Credit card account", result["message"])

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_unrecognized_apr_range_id_defaults(self, mock_to_csv, mock_read_csv):
        """Test fallback to default APR range when APRRangeID is invalid."""
        customer_df = pd.DataFrame([{"Username": "testuser", "CustomerID": 102, "APRRangeID": 999}])
        accounts_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        logs_df = pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result = openCreditCardAccount(102)
        self.assertEqual(result["status"], "success")
        self.assertIn("Credit card account", result["message"])

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_apr_range_bounds(self, mock_to_csv, mock_read_csv):
        """Test APR assigned within expected bounds for APRRangeID = 4."""
        customer_df = pd.DataFrame([{"Username": "user103", "CustomerID": 103, "APRRangeID": 4}])
        accounts_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        logs_df = pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result = openCreditCardAccount(103)
        self.assertEqual(result["status"], "success")
        apr_value = float(result["message"].split()[-2].replace('%', ''))
        self.assertGreaterEqual(apr_value, 27.1)
        self.assertLessEqual(apr_value, 30)

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_account_id_uniqueness_logic(self, mock_to_csv, mock_read_csv):
        """Test account ID is generated uniquely even if many IDs already exist."""
        customer_df = pd.DataFrame([{"Username": "user104", "CustomerID": 104, "APRRangeID": 2}])
        accounts_df = pd.DataFrame([{"AccountID": i, "CustomerID": 999, "AccountType": "Credit Card",
                                     "CurrBal": 0.0, "DateOpened": "2025-01-01",
                                     "CreditLimit": 1000, "APR": 22.5} for i in range(5000, 9999)])
        logs_df = pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result = openCreditCardAccount(104)
        self.assertEqual(result["status"], "success")

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_customer_not_found(self, mock_to_csv, mock_read_csv):
        """Test error is returned when customer ID is not found."""
        customer_df = pd.DataFrame([{"Username": "user105", "CustomerID": 105, "APRRangeID": 3}])
        accounts_df = pd.DataFrame()
        logs_df = pd.DataFrame()

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result = openCreditCardAccount(999)  # nonexistent ID
        self.assertEqual(result["status"], "error")
        self.assertIn("Customer 999 not found", result["message"])

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_multiple_credit_card_creations(self, mock_to_csv, mock_read_csv):
        """Test multiple credit card creations for same customer (unique accounts)."""
        customer_df = pd.DataFrame([{"Username": "user106", "CustomerID": 106, "APRRangeID": 2}])
        accounts_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        logs_df = pd.DataFrame(columns=["LogID", "UserID", "LogMessage"])

        mock_read_csv.side_effect = lambda path: (
            customer_df if "customers.csv" in path else
            accounts_df if "accounts.csv" in path else
            logs_df
        )

        result1 = openCreditCardAccount(106)
        result2 = openCreditCardAccount(106)

        self.assertEqual(result1["status"], "success")
        self.assertEqual(result2["status"], "success")
        self.assertNotEqual(result1["message"].split()[3], result2["message"].split()[3])  # account ID

if __name__ == "__main__":
    unittest.main()