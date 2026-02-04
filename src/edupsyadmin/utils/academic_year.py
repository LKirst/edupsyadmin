from datetime import date

from dateutil.relativedelta import relativedelta

DEFAULT_LAST_MONTH = 7
DEFAULT_LAST_DAY = 31


def get_academic_year_string(end_of_year: date) -> str:
    """
    Returns the academic year as a string.

    :param end_of_year: the date of the end of the school year
    :return: a string in the format '%Y/%y' for a given end-of-year date
    """
    return f"{int(end_of_year.year) - 1}/{end_of_year.strftime('%y')}"


def get_this_academic_year_string() -> str:
    """
    Returns the current academic year.

    :return: a string in the format '%Y/%y'
    """

    return get_academic_year_string(get_estimated_end_of_academic_year())


def get_estimated_end_of_academic_year(
    date_current: date | None = None,
    grade_current: int = 0,
    grade_target: int = 0,
    last_month: int = DEFAULT_LAST_MONTH,
    last_day: int = DEFAULT_LAST_DAY,
) -> date:
    """
    Estimates the end date of the academic year given the current and target grades.

    :param date_current: The current date, defaults to None
    :param grade_current: The current grade of the student, defaults to 0
    :param grade_target: The target grade of the student, defaults to 0
    :param last_month: The month the academic year ends, defaults to 7 (July)
    :param last_day: The day in the last month when the academic year ends,
        defaults to 31.
    :return: The estimated end of the academic year.
    """
    if date_current is None:
        date_current = date.today()

    remaining_years = grade_target - grade_current
    date_target = date_current + relativedelta(years=remaining_years)
    year_adjustment = 1 if date_target.month > last_month else 0
    return date(year=date_target.year + year_adjustment, month=last_month, day=last_day)


def get_estimated_end_of_this_academic_year(
    grade_current: int, grade_target: int, last_month: int = DEFAULT_LAST_MONTH
) -> date:
    """
    Estimates the end date of the current academic year.

    :param grade_current: The current grade of the student.
    :param grade_target: The target grade of the student.
    :param last_month: The month the academic year ends. Defaults to July (7).
    :return: The estimated end of this academic year.
    """
    date_current = date.today()
    return get_estimated_end_of_academic_year(
        date_current, grade_current, grade_target, last_month
    )


def get_date_destroy_records(date_graduation: date) -> date:
    """
    Calculates the date when student records should be destroyed,
    three years after graduation.

    :param date_graduation: The graduation date of the student.
    :return: The date when records should be destroyed.

    .. note::
        Quelle der Regelung: Bekanntmachung des Bayerischen Staatsministeriums
        für Unterricht und Kultus über die Schulberatung in Bayern vom 29.
        Oktober 2001 (KWMBl. I S. 454, StAnz.  Nr. 47), die zuletzt durch
        Bekanntmachung vom 17. März 2023 (BayMBl. Nr. 148) geändert worden ist

        Ziffer III. 4.4:
        "Aufzeichnungen [von Schüler:innenberatung] sind — soweit möglich im
        Beratungsraum — bis zum Ablauf von drei Jahren nach dem Ende des
        Schulbesuchs der betreffenden Schülerin bzw. des betreffenden Schülers
        unter Verschluss zu halten und anschließend zu vernichten. (Die im
        Rahmen der Beratung von Schule und Lehrkräften erstellten
        Aufzeichnungen sind bis zum Ablauf von zwei Jahren nach Ende der
        konkreten Maßnahme unter Verschluss zu halten und anschließend zu
        vernichten.))"
    """

    return date_graduation + relativedelta(years=3)
