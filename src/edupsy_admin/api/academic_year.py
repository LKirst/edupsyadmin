#!/usr/bin/env python
import argparse
from dateutil import relativedelta
from datetime import datetime, date


def get_academic_year_string(end_of_year: date):
    return f"{int(end_of_year.year)-1}/{end_of_year.strftime('%y')}"


def get_this_academic_year_string():
    return get_academic_year_string(get_estimated_end_of_academic_year())


def get_estimated_end_of_academic_year(
    date_current: date = date.now,
    grade_current: int = 0,
    grade_target: int = 0,
    last_month: int = 7,
):
    remaining_years = grade_target - grade_current
    date_target = date_current + relativedelta.relativedelta(years=remaining_years)
    if date_target.month > last_month:
        end_of_year = datetime(year=date_target.year + 1, month=last_month, day=31)
    else:
        end_of_year = datetime(year=date_target.year, month=last_month, day=31)
    return end_of_year


def get_estimated_end_of_this_academic_year(
    grade_current: int, grade_target: int, last_month: int = 7
):
    date_current = date.today()
    date_target = get_estimated_end_of_academic_year(
        date_current, grade_current, grade_target, last_month
    )
    return date_target


def get_date_destroy_records(date_graduation: date):
    """
    Quelle der Regelung:
    Bekanntmachung des Bayerischen Staatsministeriums für Unterricht und Kultus
    über die Schulberatung in Bayern vom 29. Oktober 2001 (KWMBl. I S. 454, StAnz.
    Nr. 47), die zuletzt durch Bekanntmachung vom 17. März 2023 (BayMBl. Nr. 148)
    geändert worden ist

    Ziffer III. 4.4:
    "Aufzeichnungen [von Schüler:innenberatung] sind – soweit möglich im
    Beratungsraum – bis zum Ablauf von drei Jahren nach dem Ende des
    Schulbesuchs der betreffenden Schülerin bzw. des betreffenden Schülers
    unter Verschluss zu halten und anschließend zu vernichten. (Die im Rahmen
    der Beratung von Schule und Lehrkräften erstellten Aufzeichnungen sind bis
    zum Ablauf von zwei Jahren nach Ende der konkreten Maßnahme unter
    Verschluss zu halten und anschließend zu vernichten.))"
    """

    date_destroy = date_graduation + relativedelta.relativedelta(years=3)
    return date_destroy


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("grade_current", type=int)
    parser.add_argument("grade_target", type=int)
    parser.add_argument("--last_month", "-lm", default=7, type=int)
    parser.add_argument(
        "--destroy_files",
        action="store_true",
        help=(
            "if true, 3 years will be added to grade_target and the date returned "
            "is the date when the records should be destroyed"
        ),
    )
    args = parser.parse_args()

    date_target = get_estimated_end_of_this_academic_year(
        args.grade_current, args.grade_target, args.last_month
    )
    if args.destroy_files:
        print("adding three years to the date of graduation")
        date_target = get_date_destroy_records(date_target)
    academic_year = get_academic_year_string(date_target)
    print(f"Geschätztes Ende des akademischen Jahre {academic_year}: {date_target}")
