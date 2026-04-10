#!/usr/bin/env python3
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.reports import (
    ResultsItem,
    TestReport,
    TestReportData,
    normal_distribution_plot,
)
from edupsyadmin.core.config import config
from edupsyadmin.utils.convert_measures import percentile_to_t, t_to_z
from edupsyadmin.utils.datediff import mydatediff


def askyn(prompt: str) -> int:
    s_yes = {"yes", "ye", "y"}
    s_no = {"no", "n"}
    s_quit = {"quit", "q"}

    answ = input(prompt).lower()
    if answ in s_yes:
        return 1
    if answ in s_no:
        return 0
    if answ in s_quit:
        return -1
    raise OSError("Only y, n or q are allowed.")


def get_lv_korrektur(lv_rw: float) -> tuple[float, int]:
    lv_korr_faktor = float(input("Korrekturfaktor LV:"))
    lv_rw_korr = lv_rw * lv_korr_faktor
    lv_rw_korr_floor = math.floor(lv_rw_korr)
    lv_rw_korr_ceil = math.ceil(lv_rw_korr)
    lv_rw_korr_nachkomma = lv_rw_korr % 1

    lv_pr_floor = int(input(f"Rohwert abger. LV = {lv_rw_korr_floor}; PR = "))
    lv_pr_ceil = int(input(f"Rohwert aufger. LV = {lv_rw_korr_ceil}; PR = "))
    lv_pr_diff = lv_pr_ceil - lv_pr_floor
    lv_pr_korr = round(lv_pr_floor + lv_pr_diff * lv_rw_korr_nachkomma)
    return lv_rw_korr, lv_pr_korr


def get_indeces(
    fn: str | os.PathLike[str],
    schoolyear: int,
) -> tuple[list[ResultsItem], float, float, float]:
    csv = pd.read_csv(fn)
    correct_answ = 0
    incorrect_answ = 0

    print("Press quit for the first item, the subject did not respond to.")
    num_processed = 0
    for i, item in enumerate(csv.RichtigeAntwort):
        answ = askyn(f"{item}?(y|n|q): ")
        if answ == 1:
            correct_answ += 1
        elif answ == 0:
            incorrect_answ += 1
        elif answ == -1:
            num_processed = i
            break
    else:
        num_processed = len(csv)

    if num_processed == 0:
        raise ValueError("No items were processed.")

    words_until_last_item = csv.Wortzahl.iloc[num_processed - 1]
    words_after_last_item = int(input("Words read after the last item: "))

    lv_rw = correct_answ * 2 - incorrect_answ
    lgs_rw = words_until_last_item + words_after_last_item
    lg_rw = round((correct_answ / num_processed) * 100)
    if schoolyear < 11:
        lv_rw_korr, lv_pr_korr = get_lv_korrektur(lv_rw)
        lgs_korr_faktor = float(input("Korrekturfaktor LGS:"))
        lgs_rw_korr = round(lgs_rw * lgs_korr_faktor)
    else:
        lv_rw_korr = lv_rw
        lv_pr_korr = int(input(f"Rohwert LV = {lv_rw_korr}; PR = "))
        lgs_rw_korr = lgs_rw

    lgs_pr_korr = int(input(f"Rohwert LGS = {lgs_rw_korr}; PR = "))
    lg_pr = int(input(f"Rohwert LG = {lg_rw}; PR = "))

    lv_t = percentile_to_t(lv_pr_korr)
    lgs_t = percentile_to_t(lgs_pr_korr)
    lg_t = percentile_to_t(lg_pr)

    results: list[ResultsItem] = [
        "Items",
        ("Bearbeitete Items", str(num_processed)),
        ("Richtige Lösungen", str(correct_answ)),
        ("Falsche Lösungen", str(incorrect_answ)),
        "LV",
        ("Rohwert LV", str(lv_rw)),
        ("Rohwert LV nach Tzp.-Korrektur", str(lv_rw_korr)),
        ("PR", str(lv_pr_korr)),
        ("T-Wert", f"{lv_t:.2f}"),
        "LGS",
        ("Wörter bis zur letzten Klammer", str(words_until_last_item)),
        ("Wörter nach der letzten Klammer", str(words_after_last_item)),
        ("Rohwert LGS", str(lgs_rw)),
        ("Rohwert LGS nach Tzp.-Korrektur", str(lgs_rw_korr)),
        ("PR", str(lgs_pr_korr)),
        ("T-Wert", f"{lgs_t:.2f}"),
        "LGN",
        ("Rohwert LGN", f"{lg_rw}%"),
        ("PR", str(lg_pr)),
        ("T-Wert", f"{lg_t:.2f}"),
    ]

    return results, lv_t, lgs_t, lg_t


def mk_report(
    database_url: str,
    client_id: int,
    test_date: str,
    version: str = "Rosenkohl",
    directory: str | os.PathLike[str] = ".",
) -> None:
    fn_csv = getattr(config.lgvtcsv, version)
    t_day = datetime.strptime(test_date, "%Y-%m-%d").date()

    client_dict = ClientsManager(
        database_url=database_url,
    ).get_decrypted_client(client_id)

    name = (
        (client_dict.get("first_name_encr", "") or "")
        + " "
        + (client_dict.get("last_name_encr", "") or "")
    ).strip() or str(client_id)
    schoolyear = int(cast(Any, client_dict.get("class_int_encr", 0)))
    birthday = client_dict.get("birthday_encr")

    if birthday is None:
        raise ValueError(f"No birthday found for client {client_id}")

    age_str = mydatediff(birthday, t_day)

    results, lv_t, lgs_t, lg_t = get_indeces(fn_csv, schoolyear)

    # Plot generation
    z_values = [t_to_z(lv_t), t_to_z(lgs_t), t_to_z(lg_t)]
    fn_plot = Path("normal_distribution_plot.png")
    normal_distribution_plot(z_values, fn_plot)

    data = TestReportData(
        heading=f"LGVT ({version}) Auswertung",
        client_name_or_id=name,
        grade=schoolyear,
        test_date=t_day,
        birthday=birthday,
        age_str=age_str,
        results=results,
        plot_path=fn_plot,
    )

    report = TestReport(data)
    output_fn = Path(directory) / f"{client_id}_Auswertung_LGVT.pdf"
    report.build(output_fn)

    # remove the plot png
    if fn_plot.exists():
        fn_plot.unlink()
