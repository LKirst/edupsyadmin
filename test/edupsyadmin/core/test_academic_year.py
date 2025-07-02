import unittest
from datetime import date

from edupsyadmin.core.academic_year import (
    DEFAULT_LAST_DAY,
    DEFAULT_LAST_MONTH,
    get_academic_year_string,
    get_date_destroy_records,
    get_estimated_end_of_academic_year,
    get_estimated_end_of_this_academic_year,
    get_this_academic_year_string,
)

TODAY = date.today()
end_of_year = date(TODAY.year, DEFAULT_LAST_MONTH, DEFAULT_LAST_DAY)
if TODAY.month > DEFAULT_LAST_MONTH:
    end_of_year = end_of_year.replace(year=end_of_year.year + 1)


class TestAcademicYearFunctions(unittest.TestCase):
    def test_get_academic_year_string(self):
        end_of_year = date(2023, 7, 31)
        self.assertEqual(get_academic_year_string(end_of_year), "2022/23")

    def test_get_this_academic_year_string(self):
        self.assertEqual(
            get_this_academic_year_string(), get_academic_year_string(end_of_year)
        )

    def test_get_estimated_end_of_academic_year(self):
        current_date = date(2023, 1, 10)
        self.assertEqual(
            get_estimated_end_of_academic_year(current_date),
            date(2023, DEFAULT_LAST_MONTH, DEFAULT_LAST_DAY),
        )

        self.assertEqual(
            get_estimated_end_of_academic_year(
                date_current=current_date,
                grade_current=10,
                grade_target=11,
                last_month=8,
                last_day=30,
            ),
            date(2024, 8, 30),
        )

    def test_get_estimated_end_of_this_academic_year(self):
        result = get_estimated_end_of_this_academic_year(10, 12)
        self.assertEqual(result.year, end_of_year.year + 2)
        self.assertEqual(result.month, DEFAULT_LAST_MONTH)
        self.assertEqual(result.day, DEFAULT_LAST_DAY)

    def test_get_date_destroy_records(self):
        graduation_date = date(2023, 7, 31)
        self.assertEqual(
            get_date_destroy_records(graduation_date), date(2023 + 3, 7, 31)
        )


if __name__ == "__main__":
    unittest.main()
