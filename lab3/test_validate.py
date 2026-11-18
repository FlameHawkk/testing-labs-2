import unittest
from graph_config import validate

class TestValidate(unittest.TestCase):
    def test_valid_value(self):
        self.assertEqual(validate("50", 0, 100), 50)

    def test_boundary_min(self):
        self.assertEqual(validate("0", 0, 100), 0)

    def test_boundary_max(self):
        self.assertEqual(validate("100", 0, 100), 100)

    def test_non_numeric(self):
        self.assertIsNone(validate("abc", 0, 100))

    def test_empty_string(self):
        self.assertIsNone(validate("", 0, 100))

    def test_below_min(self):
        self.assertIsNone(validate("-1", 0, 100))

    def test_above_max(self):
        self.assertIsNone(validate("101", 0, 100))

if __name__ == "__main__":
    unittest.main(verbosity=2)