from datetime import date

from dateutil import relativedelta


def mydatediff(d1: date, d2: date) -> str:
    """
    Calculate the difference between two dates and return it as a formatted string.

    :param d1: The first date.
    :param d2: The second date.
    :return: A string representing the difference in years, months, and days.
    """
    difference = relativedelta.relativedelta(d2, d1)
    return (
        f"{difference.years} Jahre, {difference.months} Monate "
        f"und {difference.days} Tage"
    )
