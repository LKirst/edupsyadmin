#!/usr/bin/env python3
import os
import argparse
import pandas as pd
from pathlib import Path

from datediff import mydatediff_interactive


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


def get_indeces(fn, client_id, d_birth, d_test, age, version):
    csv = pd.read_csv(fn)
    correct_answ = 0
    incorrect_answ = 0

    year = input("Klasse: ")

    text = [f"# Ergebnisse LGVT ({version})\n\n## Items"]
    text += [
        f"\nName/Code: {client_id}; Geburtsdatum: {d_birth}; Klasse: {year}",
        f"\nTestdatum: {d_test}; Alter: {age}",
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

    text += [
        f"\n## LV",
        f"\n- Summe richtige Lösungen: {correct_answ}",
        f"\n- Summe falsche Lösungen: {incorrect_answ}",
        f"\n- Gesamtzahl bearbeitete Items: {i}",
        f"\n- Rohwert LV: {correct_answ*2 - incorrect_answ}; nach Tzp.-Korrektur:",
        f"\n- **PR= ;\tT-Wert=**",
        f"\n## LGS",
        f"\n- Wörter bis zur letzten Klammer: {words_until_last_item}",
        f"\n- Wörter nach der letzten Klammer: {words_after_last_item}",
        f"\n- Rohwert LGS: {words_until_last_item + words_after_last_item}; nach Tzp.-Korrektur:",
        f"\n- **PR= ;\tT-Wert=**",
        f"\n## LGN",
        f"\n- Rohwert LGN: {round((correct_answ/i)*100)}%",
        f"\n- **PR= ;\tT-Wert=**",
    ]

    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=str, choices=["Rosenkohl", "Toechter"])
    parser.add_argument("client_id", type=str, help="subject client_id / name")
    parser.add_argument("directory", type=str, default=".")
    args = parser.parse_args()

    out_path = Path(args.directory).joinpath(f"{args.client_id}_Auswertung_LGVT.md")

    if args.version == "Rosenkohl":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Rosenkohl_WortzahlRichtigeAntwort.csv"
        )
    elif args.version == "Toechter":
        fn_csv = Path(
            "~/bin/school/psych_lgvt_wortzahl_und_richtige/Toechter_WortzahlRichtigeAntwort.csv"
        )
    else:
        raise IOError
    print(fn_csv)

    b_day, t_day, age = mydatediff_interactive()

    results = get_indeces(fn_csv, args.client_id, b_day, t_day, age, args.version)
    print(results)

    with open(out_path, "w", encoding="utf-8") as f:
        for line in results:
            f.write(line)
            f.write("\n")
