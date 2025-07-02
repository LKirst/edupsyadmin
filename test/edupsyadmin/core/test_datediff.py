import unittest
from datetime import datetime

from edupsyadmin.core.datediff import mydatediff


class TestDatediff(unittest.TestCase):
    def test_mydatediff(self):
        date1 = datetime(2020, 1, 1)
        date2 = datetime(2021, 1, 1)
        result = mydatediff(date1, date2)
        self.assertEqual(result, "1 Jahre, 0 Monate und 0 Tage")

        date1 = datetime(2020, 1, 1)
        date2 = datetime(2020, 6, 1)
        result = mydatediff(date1, date2)
        self.assertEqual(result, "0 Jahre, 5 Monate und 0 Tage")

        date1 = datetime(2020, 1, 1)
        date2 = datetime(2019, 6, 1)
        result = mydatediff(date1, date2)
        self.assertEqual(result, "0 Jahre, -7 Monate und 0 Tage")

        date1 = datetime(2020, 1, 1)
        date2 = datetime(2020, 1, 3)
        result = mydatediff(date1, date2)
        self.assertEqual(result, "0 Jahre, 0 Monate und 2 Tage")


if __name__ == "__main__":
    unittest.main()
