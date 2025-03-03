from withdrawMoney import withdraw
from decimal import Decimal
import unittest

class TestWithdraw(unittest.TestCase):
    def test_param_type(self):
        def params_test(accID, amount):
            self.assertIsInstance(accID, int)
            self.assertIsInstance(amount, Decimal)
        
        params_test(615, 167.89)
        params_test(789, 20)

    def test_withdraw(self):
        self.assertTrue(withdraw(615, 167.89))
        self.assertTrue(withdraw(789, 20))

    def test_invalid_accID(self):
        with self.assertRaises(TypeError) as context:
            withdraw('test', 167.89)
        self.assertEqual('accID must be an integer', str(context.exception))

    def test_invalid_amount(self):
        with self.assertRaises(TypeError) as context:
            withdraw(615, 'test')
        self.assertEqual('amount must be a decimal', str(context.exception))

    def test_invalid_amount_list(self):
        with self.assertRaises(TypeError) as context:
            withdraw(615, [20,30,40])
        self.assertEqual('amount must be a decimal', str(context.exception))

if __name__ == '__main__':
    unittest.main()