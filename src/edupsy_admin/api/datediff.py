#!/usr/bin/env python3
from dateutil import relativedelta
from datetime import datetime


def mydatediff(d1, d2):
    difference = relativedelta.relativedelta(d2, d1)
    difference_string = "{} Jahre, {} Monate und {} Tage".format(
        difference.years, difference.months, difference.days
    )
    return difference_string


def mydatediff_interactive():
    date1 = datetime.strptime(input("Datum 1 (YYYY-mm-dd): "), "%Y-%m-%d").date()
    date2 = datetime.strptime(input("Datum 2 (YYYY-mm-dd): "), "%Y-%m-%d").date()
    return date1, date2, mydatediff(date1, date2)


if __name__ == "__main__":
    d1, d2, difference_string = mydatediff_interactive()
    print(difference_string)
