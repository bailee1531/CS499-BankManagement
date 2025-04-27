# Spring 2025 Authors: Sierra Yerges
# In root dir: python -m unittest tests/test_billPayment.py
import unittest
from unittest.mock import patch
from decimal import Decimal
import pandas as pd
from datetime import date
from scripts.billPayment import (
    scheduleBillPayment,
    viewScheduledBills,
    processScheduledBills
)

class TestBillPaymentFunctions(unittest.TestCase):
    """
    Unit tests for the bill payment system functions:
    - scheduleBillPayment
    - viewScheduledBills
    - processScheduledBills
    """

    @patch("scripts.billPayment.pd.read_csv")
    @patch("scripts.billPayment.pd.DataFrame.to_csv")
    def test_schedule_bill_payment_success(self, mock_to_csv, mock_read_csv):
        """
        Test successful scheduling of a bill payment.
        """
        mock_read_csv.return_value = pd.DataFrame(columns=[
            "BillID", "CustomerID", "PayeeName", "PayeeAddress", "Amount", "DueDate", "PaymentAccID"
        ])
        result = scheduleBillPayment(
            101, "UAH Electric", "301 Sparkman Dr", Decimal("120.50"), "2025-03-25", 5001
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("scheduled", result["message"])
        mock_to_csv.assert_called()

    @patch("scripts.billPayment.os.path.exists", return_value=False)
    def test_view_scheduled_bills_file_missing(self, mock_exists):
        """
        Test viewing scheduled bills when file does not exist.
        """
        result = viewScheduledBills(999)
        self.assertEqual(result[0]["status"], "error")
        self.assertIn("No scheduled bills", result[0]["message"])

    @patch("scripts.billPayment.os.path.exists", return_value=True)
    @patch("scripts.billPayment.pd.read_csv")
    def test_view_scheduled_bills_for_customer(self, mock_read_csv, mock_exists):
        """
        Test viewing scheduled bills for a customer with bills.
        """
        mock_read_csv.return_value = pd.DataFrame([
            {"BillID": 1, "CustomerID": 315, "PayeeName": "UAH", "PayeeAddress": "301 Sparkman", "Amount": "100.00", "DueDate": "2025-03-22", "PaymentAccID": 7001}
        ])
        result = viewScheduledBills(315)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["CustomerID"], 315)

    @patch("scripts.billPayment.pd.read_csv")
    @patch("scripts.billPayment.generate_transaction_ID", return_value="TX999")
    @patch("scripts.billPayment.pd.DataFrame.to_csv")
    @patch("scripts.billPayment.os.path.exists", return_value=True)
    def test_process_due_bill_success(self, mock_exists, mock_to_csv, mock_generate_txn, mock_read_csv):
        """
        Test that a due bill is processed successfully (non-credit account).
        """
        today = date.today().isoformat()
        mock_read_csv.side_effect = [
            pd.DataFrame([{
                "AccountID": 7001,
                "CustomerID": 315,
                "AccountType": "Checking",
                "CurrBal": "500.00",
                "CreditLimit": "0.00"
            }]),
            pd.DataFrame([{
                "BillID": 1,
                "CustomerID": 315,
                "PayeeName": "Power Company",
                "PayeeAddress": "123 Electric Way",
                "Amount": "100.00",
                "DueDate": today,
                "PaymentAccID": 7001
            }]),
            pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])
        ]
        result = processScheduledBills()
        self.assertEqual(result[0]["status"], "success")
        self.assertIn("processed successfully", result[0]["message"])
        mock_to_csv.assert_called()

    @patch("scripts.billPayment.pd.read_csv")
    @patch("scripts.billPayment.generate_transaction_ID", return_value="TX999")
    @patch("scripts.billPayment.pd.DataFrame.to_csv")
    @patch("scripts.billPayment.os.path.exists", return_value=True)
    def test_overlimit_fee_applied_on_credit_card(self, mock_exists, mock_to_csv, mock_generate_txn, mock_read_csv):
        """
        Test that over-limit fee is charged and re-billed when credit card limit exceeded.

        Verifies:
        - Original bill is skipped due to credit limit breach.
        - Over-limit fee is re-scheduled successfully.
        """
        today = date.today().isoformat()

        # Initial call to read accounts.csv, bills.csv, logs.csv
        mock_accounts = pd.DataFrame([{
            "AccountID": 8888,
            "CustomerID": 222,
            "AccountType": "Credit Card",
            "CurrBal": "1490.00",
            "CreditLimit": "1500.00"
        }])
        mock_bills = pd.DataFrame([{
            "BillID": 22,
            "CustomerID": 222,
            "PayeeName": "Gym",
            "PayeeAddress": "123 Fitness Ln",
            "Amount": "20.00",
            "DueDate": today,
            "PaymentAccID": 8888
        }])
        mock_logs = pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])

        # Provide mocks for all expected read_csv calls (including nested)
        mock_read_csv.side_effect = [
            mock_accounts,  # accounts.csv
            mock_bills,     # bills.csv
            mock_logs,      # logs.csv
            mock_bills      # read again inside scheduleBillPayment
        ]

        result = processScheduledBills()

        self.assertEqual(result[0]["status"], "error")
        self.assertIn("Over-limit fee", result[0]["message"])
        mock_to_csv.assert_called()

    @patch("scripts.billPayment.pd.read_csv")
    @patch("scripts.billPayment.generate_transaction_ID", return_value="TX999")
    @patch("scripts.billPayment.pd.DataFrame.to_csv")
    @patch("scripts.billPayment.os.path.exists", return_value=True)
    def test_insufficient_funds_standard_account(self, mock_exists, mock_to_csv, mock_generate_txn, mock_read_csv):
        """
        Test insufficient funds scenario for checking/savings account.
        """
        today = date.today().isoformat()
        mock_read_csv.side_effect = [
            pd.DataFrame([{
                "AccountID": 5555,
                "CustomerID": 111,
                "AccountType": "Savings",
                "CurrBal": "50.00",
                "CreditLimit": "0.00"
            }]),
            pd.DataFrame([{
                "BillID": 5,
                "CustomerID": 111,
                "PayeeName": "Insurance Co",
                "PayeeAddress": "789 Secure St",
                "Amount": "100.00",
                "DueDate": today,
                "PaymentAccID": 5555
            }]),
            pd.DataFrame(columns=["AccountID", "CustomerID", "TransactionType", "Amount", "TransactionID"])
        ]
        result = processScheduledBills()
        self.assertEqual(result[0]["status"], "error")
        self.assertIn("Insufficient funds", result[0]["message"])


if __name__ == "__main__":
    unittest.main()
