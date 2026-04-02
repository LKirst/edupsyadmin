from datetime import datetime
from os import PathLike
from pathlib import Path

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.reports import (
    ResultsItem,
    TestReport,
    TestReportData,
    normal_distribution_plot,
)
from edupsyadmin.api.types import ClientData
from edupsyadmin.utils.convert_measures import iq_to_t, iq_to_z
from edupsyadmin.utils.datediff import mydatediff


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


def create_report(
    database_url: str,
    client_id: int,
    test_date: str,
    directory: str | PathLike[str] = ".",
) -> None:
    clients_manager = ClientsManager(
        database_url=database_url,
    )
    client_dict: ClientData = clients_manager.get_decrypted_client(client_id)

    testdate = datetime.strptime(test_date, "%Y-%m-%d").date()
    birthday = client_dict.get("birthday_encr")

    if birthday is None:
        raise ValueError(f"No birthday found for client {client_id}")

    age_str = mydatediff(birthday, testdate)
    grade = client_dict.get("class_int_encr")

    raw_part1_min = input_int_or_none("Teil 1 min: ")
    raw_part1_max = input_int_or_none("Teil 1 max: ")
    raw_part2 = int(input("Teil 2: "))

    raw_total_min = raw_part1_min + raw_part2 if raw_part1_min is not None else None
    raw_total_max = raw_part1_max + raw_part2 if raw_part1_max is not None else None

    iq_part1_min = input_int_or_none("IQ Teil 1 min: ")
    iq_part1_max = input_int_or_none("IQ Teil 1 max: ")
    iq_part2 = int(input("IQ Teil 2: "))
    iq_total_min = input_int_or_none("IQ Total min: ")
    iq_total_max = input_int_or_none("IQ Total max: ")

    differenz = None if iq_part1_max is None else iq_part1_max - iq_part2

    results: list[ResultsItem] = [
        "Teil 1",
        ("Teil 1 min — Rohwert", str(raw_part1_min)),
        ("Teil 1 min — IQ", str(iq_part1_min)),
        ("Teil 1 min — T", str(safe_iq_to_t(iq_part1_min))),
        ("Teil 1 max — Rohwert", str(raw_part1_max)),
        ("Teil 1 max — IQ", str(iq_part1_max)),
        ("Teil 1 max — T", str(safe_iq_to_t(iq_part1_max))),
        "Teil 2",
        ("Teil 2 — Rohwert", str(raw_part2)),
        ("Teil 2 — IQ", str(iq_part2)),
        ("Teil 2 — T", str(safe_iq_to_t(iq_part2))),
        "Gesamt",
        ("Ges. min — Rohwert", str(raw_total_min)),
        ("Ges. min — IQ", str(iq_total_min)),
        ("Ges. min — T", str(safe_iq_to_t(iq_total_min))),
        ("Ges. max — Rohwert", str(raw_total_max)),
        ("Ges. max — IQ", str(iq_total_max)),
        ("Ges. max — T", str(safe_iq_to_t(iq_total_max))),
        "Differenz",
        ("IQ Teil 1 max - Teil 2 (sign. ab 12)", str(differenz)),
    ]

    # create a normal distribution plot and save it as a png
    iq_values = [iq_part1_min, iq_part1_max, iq_part2, iq_total_min, iq_total_max]
    z_values = [iq_to_z(iq) for iq in iq_values if iq is not None]
    fn_plot = Path("normal_distribution_plot.png")
    normal_distribution_plot(z_values, fn_plot)

    # create the pdf
    name = (
        client_dict.get("first_name_encr", "")
        + " "
        + client_dict.get("last_name_encr", "")
    ).strip() or str(client_id)

    data = TestReportData(
        heading="CFT 20-R Auswertung",
        client_name_or_id=name,
        grade=grade,
        test_date=testdate,
        birthday=birthday,
        age_str=age_str,
        results=results,
        plot_path=fn_plot,
    )

    report = TestReport(data)
    output_fn = Path(directory) / f"{client_id}_Auswertung.pdf"
    report.build(output_fn)

    # remove the plot png
    if fn_plot.exists():
        fn_plot.unlink()
