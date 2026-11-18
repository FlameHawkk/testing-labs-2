import unittest
from graph_config import validate

class TestValidate(unittest.TestCase):
    """Тестирование функции validate() с отображением покрытых путей."""

    def _report(self, test_name, path, input_data, expected, actual):
        print(f"  {test_name}: вход={input_data} → {actual} | путь={path}")
        self.assertEqual(actual, expected)

    def test_valid_value(self):
        result = validate("50", 0, 100)
        self._report("Корректное значение", [1, 2, 4, 6, 8], '"50", 0, 100', 50, result)

    def test_boundary_min(self):
        result = validate("0", 0, 100)
        self._report("Нижняя граница", [1, 2, 4, 6, 8], '"0", 0, 100', 0, result)

    def test_boundary_max(self):
        result = validate("100", 0, 100)
        self._report("Верхняя граница", [1, 2, 4, 6, 8], '"100", 0, 100', 100, result)

    def test_non_numeric(self):
        result = validate("abc", 0, 100)
        self._report("Нечисловая строка", [1, 2, 3], '"abc", 0, 100', None, result)

    def test_empty_string(self):
        result = validate("", 0, 100)
        self._report("Пустая строка", [1, 2, 3], '"", 0, 100', None, result)

    def test_below_min(self):
        result = validate("-1", 0, 100)
        self._report("Меньше минимума", [1, 2, 4, 5], '"-1", 0, 100', None, result)

    def test_above_max(self):
        result = validate("101", 0, 100)
        self._report("Больше максимума", [1, 2, 4, 6, 7], '"101", 0, 100', None, result)

if __name__ == "__main__":
    unittest.main(verbosity=0)