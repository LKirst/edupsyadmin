#!/usr/bin/env python3
import math
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from edupsyadmin.core.convert_measures import percentile_to_t

from .managers import ClientsManager


def askyn(prompt: str) -> int:
    yes = {"yes", "ye", "y"}
    no = {"no", "n"}
    quit = {"quit", "q"}

    answ = input(prompt).lower()
    if answ in yes:
        return 1
    if answ in no:
        return 0
    if answ in quit:
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
    name: str,
    schoolyear: int,
    d_test: str | date,
    version: str,
) -> list[str]:
    csv = pd.read_csv(fn)
    correct_answ = 0
    incorrect_answ = 0

    text = [f"# Ergebnisse LGVT ({version})\n\n## Items"]
    text += [
        f"\nName/Code: {name}; Klasse: {schoolyear}",
        f"\nTestdatum: {d_test}",
    ]

    print("Press quit for the first item, the subject did not respond to.")
    for i, item in enumerate(csv.RichtigeAntwort):
        answ = askyn(f"{item}?(y|n|q): ")
        if answ == 1:
            correct_answ += 1
        elif answ == 0:
            incorrect_answ += 1
        elif answ == -1:
            break
        text += [f"\n- Item {i + 1}:\t{answ}\t{item}"]

    words_until_last_item = csv.Wortzahl.iloc[i - 1]
    words_after_last_item = int(input("Words read after the last item: "))

    lv_rw = correct_answ * 2 - incorrect_answ
    lgs_rw = words_until_last_item + words_after_last_item
    lg_rw = round((correct_answ / i) * 100)
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

    text += [
        "\n## LV",
        f"\n- Summe richtige Lösungen: {correct_answ}",
        f"\n- Summe falsche Lösungen: {incorrect_answ}",
        f"\n- Gesamtzahl bearbeitete Items: {i}",
        f"\n- Rohwert LV: {lv_rw}; nach Tzp.-Korrektur: {lv_rw_korr}",
        f"\n- PR={lv_pr_korr} ;\tT-Wert={lv_t:.2f}",
        "\n## LGS",
        f"\n- Wörter bis zur letzten Klammer: {words_until_last_item}",
        f"\n- Wörter nach der letzten Klammer: {words_after_last_item}",
        f"\n- Rohwert LGS: {lgs_rw}; nach Tzp.-Korrektur: {lgs_rw_korr}",
        f"\n- PR={lgs_pr_korr} ;\tT-Wert={lgs_t:.2f}",
        "\n## LGN",
        f"\n- Rohwert LGN: {lg_rw}%",
        f"\n- PR={lg_pr} ;\tT-Wert={lg_t:.2f}",
    ]

    return text


def get_fn_csv(version: str) -> Path:
    # TODO: allow the user to set the paths and document this feature
    if version == "Rosenkohl":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Rosenkohl_WortzahlRichtigeAntwort.csv"
        )
    elif version == "Toechter":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Toechter_WortzahlRichtigeAntwort.csv"
        )
    elif version == "Laufbursche":
        # TODO: Create that file
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Laufbursche_WortzahlRichtigeAntwort.csv"
        )
    else:
        raise OSError
    return fn_csv


def mk_report(
    app_username: str,
    app_uid: str,
    database_url: str,
    salt_path: str,
    client_id: int,
    test_date: str,
    test_type: str = "lgvt",  # noqa : ARG001
    version: str = "Rosenkohl",
    directory: str = ".",
) -> None:
    out_path = Path(directory).joinpath(f"{client_id}_Auswertung_LGVT.md")
    fn_csv = get_fn_csv(version)
    t_day = datetime.strptime(test_date, "%Y-%m-%d").date()

    clients_manager = ClientsManager(
        database_url=database_url,
        app_uid=app_uid,
        app_username=app_username,
        salt_path=salt_path,
    )
    client_dict = clients_manager.get_decrypted_client(client_id)

    name = client_dict["first_name"] + " " + client_dict["last_name"]
    schoolyear = client_dict["class_int"]

    results = get_indeces(fn_csv, name, schoolyear, t_day, version)

    with open(out_path, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line)
            f.write("\n")
