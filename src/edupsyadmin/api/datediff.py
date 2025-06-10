#!/usr/bin/env python3
from datetime import date, datetime

from dateutil import relativedelta


def mydatediff(d1: date, d2: date) -> str:
    """
    Calculate the difference between two dates and return it as a formatted string.

    :param d1: The first date.
    :param d2: The second date.
    :return: A string representing the difference in years, months, and days.
    """
    difference = relativedelta.relativedelta(d2, d1)
    difference_string = "{} Jahre, {} Monate und {} Tage".format(
        difference.years, difference.months, difference.days
    )
    return difference_string


def mydatediff_interactive() -> tuple[date, date, str]:
    """
    Interactively get two dates from the user and calculate their difference.

    :return: A tuple containing the two dates and their difference as a string.
    """
    date1 = datetime.strptime(input("Datum 1 (YYYY-mm-dd): "), "%Y-%m-%d").date()
    date2 = datetime.strptime(input("Datum 2 (YYYY-mm-dd): "), "%Y-%m-%d").date()
    return date1, date2, mydatediff(date1, date2)


if __name__ == "__main__":
    d1, d2, difference_string = mydatediff_interactive()
    print(difference_string)
