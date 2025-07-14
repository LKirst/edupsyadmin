#!/usr/bin/env python
import argparse
import os
from datetime import datetime

from reports import Report, normal_distribution_plot

from edupsyadmin.core.convert_measures import iq_to_t, iq_to_z
from edupsyadmin.core.datediff import mydatediff


def input_int_or_none(prompt: str) -> int | None:
    inp = input(prompt)
    try:
        return int(inp)
    except ValueError:
        print("Treating the input as None.")
        return None


def safe_iq_to_t(iq_value: int | None) -> float | None:
    """Avoid errors with None values"""
    if iq_value is None:
        return None
    return round(iq_to_t(iq_value), 2)


def create_report(path: str | os.PathLike[str]) -> None:
    client_id = int(input("Client ID: "))
    birthday = datetime.strptime(
        input("Geburtsdatum (YYYY-mm-dd): "), "%Y-%m-%d"
    ).date()
    testdate = datetime.strptime(input("Testdatum (YYYY-mm-dd): "), "%Y-%m-%d").date()

    age_str = f"Alter: {mydatediff(birthday, testdate)}"
    text = []
    text.append(age_str)

    raw_part1_min = input_int_or_none("Teil 1 min: ")
    raw_part1_max = input_int_or_none("Teil 1 max: ")
    raw_part2 = int(input("Teil 2: "))

    raw_total_min = raw_part1_min + raw_part2 if raw_part1_min else None
    raw_total_max = raw_part1_max + raw_part2 if raw_part1_max else None

    print(age_str)
    print("Rohwerte:")
    print(f"\tTeil 1 min\t = {raw_part1_min}")
    print(f"\tTeil 1 max\t = {raw_part1_max}")
    print(f"\tTeil 2\t\t = {raw_part2}")
    print(f"\tGes min\t\t = {raw_total_min}")
    print(f"\tGes max\t\t = {raw_total_max}")

    iq_part1_min = input_int_or_none("IQ Teil 1 min: ")
    iq_part1_max = input_int_or_none("IQ Teil 1 max: ")
    iq_part2 = int(input("IQ Teil 2: "))
    iq_total_min = input_int_or_none("IQ Total min: ")
    iq_total_max = input_int_or_none("IQ Total max: ")

    differenz = None if iq_part1_max is None else iq_part1_max - iq_part2

    results = [
        (
            f"Teil 1 min\t = {raw_part1_min}; \t"
            f"IQ Teil 1 min\t = {iq_part1_min}; "
            f"T = {safe_iq_to_t(iq_part1_min)}"
        ),
        (
            f"Teil 1 max\t = {raw_part1_max}; \t"
            f"IQ Teil 1 max\t = {iq_part1_max}; "
            f"T = {safe_iq_to_t(iq_part1_max)}"
        ),
        (
            f"Teil 2\t\t = {raw_part2}; \t"
            f"IQ Teil 2\t = {iq_part2}; "
            f"T = {safe_iq_to_t(iq_part2)}"
        ),
        (
            f"Ges. min\t\t = {raw_total_min}; \t"
            f"IQ Ges min\t = {iq_total_min}; "
            f"T = {safe_iq_to_t(iq_total_min)}"
        ),
        (
            f"Ges. max\t\t = {raw_total_max}; \t"
            f"IQ Ges max\t = {iq_total_max}; "
            f"T = {safe_iq_to_t(iq_total_max)}"
        ),
        (
            f"Differenz IQ Teil 1 max - Teil 2 "
            f"(sign. ist >= 12): IQ-Wert-Differenz = {differenz}"
        ),
    ]

    text += results

    # create a normal distribution plot and save it as a png
    iq_values = [iq_part1_min, iq_part1_max, iq_part2, iq_total_min, iq_total_max]
    z_values = [iq_to_z(iq) for iq in iq_values if iq is not None]
    fn_plot = "normal_distribution_plot.png"
    normal_distribution_plot(z_values, fn_plot)

    # create the pdf
    heading = f"CFT 20-R (Testdatum: {testdate}; Code: {client_id})"
    report = Report(heading, text, fn_plot)
    report.print_page()
    report.output(os.path.join(path, f"{client_id}_Auswertung.pdf"), "F")

    # remove the plot png
    os.remove(fn_plot)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        default=".",
        help="The directory where the output pdf should be saved",
    )
    args = parser.parse_args()

    create_report(args.path)
