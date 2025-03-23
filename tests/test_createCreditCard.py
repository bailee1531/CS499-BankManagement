# Sierra Yerges
# In root dir: python -m unittest tests/test_createCreditCard.py
import unittest
from unittest.mock import patch
from decimal import Decimal
import pandas as pd
from scripts.createCreditCard import openCreditCardAccount


class TestOpenCreditCardAccount(unittest.TestCase):
    """
    Unit tests for openCreditCardAccount function.

    This suite verifies:
    - Successful credit card creation for valid customers.
    - Error handling for non-existent or invalid customers.
    - APR assignment based on APRRangeID.
    - Unique account ID generation logic.
    - Behavior under unusual APRRangeID or missing values.
    """

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_valid_customer_credit_card_creation(self, mock_to_csv, mock_read_csv):
        """Test standard account creation for valid customer."""
        mock_read_csv.side_effect = [
            pd.DataFrame([{"CustomerID": 200, "APRRangeID": 2}]),  # customers.csv
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])  # accounts.csv
        ]
        result = openCreditCardAccount(200)
        self.assertEqual(result["status"], "success")
        self.assertIn("Credit card account", result["message"])
        self.assertRegex(result["message"], r"\d{4}.*\d{1,2}\.\d{1,2}% APR")
        mock_to_csv.assert_called()

    @patch("scripts.createCreditCard.pd.read_csv")
    def test_invalid_customer(self, mock_read_csv):
        """Test creation fails for non-existent customer."""
        mock_read_csv.return_value = pd.DataFrame(columns=["CustomerID", "APRRangeID"])
        result = openCreditCardAccount(9999)
        self.assertEqual(result["status"], "error")
        self.assertIn("Customer 9999 not found", result["message"])

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_apr_range_bounds(self, mock_to_csv, mock_read_csv):
        """Test APR assigned within expected bounds for APRRangeID = 4."""
        mock_read_csv.side_effect = [
            pd.DataFrame([{"CustomerID": 333, "APRRangeID": 4}]),
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        ]
        result = openCreditCardAccount(333)
        self.assertEqual(result["status"], "success")
        self.assertRegex(result["message"], r"(27|28|29|30)\.\d+% APR")

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_unrecognized_apr_range_id_defaults(self, mock_to_csv, mock_read_csv):
        """Test fallback to default APR range when APRRangeID is missing or invalid."""
        mock_read_csv.side_effect = [
            pd.DataFrame([{"CustomerID": 404, "APRRangeID": 99}]),  # unexpected APRRangeID
            pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])
        ]
        result = openCreditCardAccount(404)
        self.assertEqual(result["status"], "success")
        self.assertRegex(result["message"], r"(19|20)\.\d+% APR")  # default range

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_account_id_uniqueness_logic(self, mock_to_csv, mock_read_csv):
        """Test account ID is generated uniquely even if many IDs already exist."""
        existing_ids = list(range(5000, 9990))
        mock_read_csv.side_effect = [
            pd.DataFrame([{"CustomerID": 512, "APRRangeID": 1}]),  # customers.csv
            pd.DataFrame({"AccountID": existing_ids, "CustomerID": [512]*len(existing_ids)})  # accounts.csv
        ]
        result = openCreditCardAccount(512)
        self.assertEqual(result["status"], "success")
        used_id = int(result["message"].split()[3])
        self.assertNotIn(used_id, existing_ids)

    @patch("scripts.createCreditCard.pd.read_csv")
    @patch("scripts.createCreditCard.pd.DataFrame.to_csv")
    def test_multiple_credit_card_creations(self, mock_to_csv, mock_read_csv):
        """Test multiple credit card creations for same customer (unique accounts)."""
        customer_df = pd.DataFrame([{"CustomerID": 777, "APRRangeID": 3}])
        accounts_df = pd.DataFrame(columns=["AccountID", "CustomerID", "AccountType", "CurrBal", "DateOpened", "CreditLimit", "APR"])

        # Repeat mock data for both calls
        mock_read_csv.side_effect = [
            customer_df, accounts_df,  # First call
            customer_df, accounts_df   # Second call
        ]

        result1 = openCreditCardAccount(777)
        result2 = openCreditCardAccount(777)

        id1 = int(result1["message"].split()[3])
        id2 = int(result2["message"].split()[3])
        self.assertNotEqual(id1, id2)  # Ensure unique account IDs

if __name__ == "__main__":
    unittest.main()
