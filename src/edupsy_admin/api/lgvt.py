#!/usr/bin/env python3
import os
import argparse
import pandas as pd
from pathlib import Path

import percentile_to_t from convert_measures

def askyn(prompt):
    yes = {"yes", "ye", "y"}
    no = {"no", "n"}
    quit = {"quit", "q"}

    answ = input(prompt).lower()
    if answ in yes:
        return 1
    elif answ in no:
        return 0
    elif answ in quit:
        return -1
    else:
        raise IOError("Only y, n or q are allowed.")


def get_lv_korrektur(lv_rw):
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


def get_indeces(fn, client_id, d_test, version):
    csv = pd.read_csv(fn)
    correct_answ = 0
    incorrect_answ = 0

    year = input("Klasse: ")

    text = [f"# Ergebnisse LGVT ({version})\n\n## Items"]
    text += [
        f"\nName/Code: {client_id}; Klasse: {year}",
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
        text += [f"\n- Item {i+1}:\t{answ}\t{item}"]

    words_until_last_item = csv.Wortzahl.iloc[i - 1]
    words_after_last_item = int(input("Words read after the last item: "))

    lv_rw = correct_answ*2 - incorrect_answ
    lgs_rw = words_until_last_item + words_after_last_item
    if year < 11:
        lv_rw_korr, lv_pr_korr = get_lv_korrektur(lv_rw)
        lgs_korr_faktor = float(input("Korrekturfaktor LGS:"))
        lgs_rw_korr = round(lgs_rw * lgs_korr_faktor)
    else:
        lv_rw_korr = lv_rw
        lv_pr_korr = int(input("Rohwert LV = {lv_rw_korr}; PR = "))
        lgs_rw_korr = lgs_rw
    lgs_pr_korr = input("Rohwert LGS = {lgs_rw_korr}; PR = "))

    lv_t = percentile_to_t(lv_rw_korr)
    lgs_t = percentile_to_t(lgs_rw_korr)

    text += [
        f"\n## LV",
        f"\n- Summe richtige Lösungen: {correct_answ}",
        f"\n- Summe falsche Lösungen: {incorrect_answ}",
        f"\n- Gesamtzahl bearbeitete Items: {i}",
        f"\n- Rohwert LV: {lv_rw}; nach Tzp.-Korrektur: {lv_rw_korr}",
        f"\n- PR={lv_korr_pr} ;\tT-Wert={lv_t}",
        f"\n## LGS",
        f"\n- Wörter bis zur letzten Klammer: {words_until_last_item}",
        f"\n- Wörter nach der letzten Klammer: {words_after_last_item}",
        f"\n- Rohwert LGS: {lgs_rw}; nach Tzp.-Korrektur: {lgs_rw_korr}",
        f"\n- PR={lgs_pr_korr} ;\tT-Wert={lgs_t}",
        f"\n## LGN",
        f"\n- Rohwert LGN: {round((correct_answ/i)*100)}%",
        f"\n- **PR= ;\tT-Wert=**", # TODO
    ]

    return text

def get_fn_csv(version):
    if version == "Rosenkohl":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Rosenkohl_WortzahlRichtigeAntwort.csv"
        )
    elif version == "Toechter":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Toechter_WortzahlRichtigeAntwort.csv"
        )
    elif version == "Laufburschen":
        # TODO: Create that file
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Toechter_WortzahlRichtigeAntwort.csv"
        )
    else:
        raise IOError
    return fn_csv

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=str, choices=["Rosenkohl", "Toechter", "Laufburschen"])
    parser.add_argument("client_id", type=str, help="subject client_id / name")
    parser.add_argument("test_date", type=str, help="Testdatum (YYYY-mm-dd)")
    parser.add_argument("directory", type=str, default=".")
    args = parser.parse_args()

    out_path = Path(args.directory).joinpath(f"{args.client_id}_Auswertung_LGVT.md")
    fn_csv = get_fn_csv(args.version)

    t_day = datetime.strptime(args.test_date), "%Y-%m-%d").date()
    results = get_indeces(fn_csv, args.client_id, t_day, args.version)
    print(results)

    with open(out_path, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line)
            f.write("\n")
