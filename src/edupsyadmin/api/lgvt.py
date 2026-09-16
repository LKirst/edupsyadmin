#!/usr/bin/env python3
import csv
import math
import os
from datetime import datetime
from pathlib import Path
from statistics import StatisticsError
from typing import Final

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.reports import (
    ResultsItem,
    TestReport,
    TestReportData,
    normal_distribution_plot,
)
from edupsyadmin.api.types import ClientRecord
from edupsyadmin.core.config import config
from edupsyadmin.utils.convert_measures import percentile_to_t, t_to_z
from edupsyadmin.utils.datediff import mydatediff
from edupsyadmin.utils.path_utils import normalize_path
from edupsyadmin.utils.rounding import round_half_up

MAX_KORREKTUR_SCHOOLYEAR: Final[int] = 11
_BOUNDARY_LABEL = "n/a (da PR < 1 oder PR > 99)"
_Z_EXTREME = 3.0


def _safe_percentile_to_t(percentile: int) -> tuple[float | None, str]:
    """Attempt to convert a percentile to a T-value, handling boundary cases.

    :param percentile: A percentile rank.
    :return: A tuple of ``(t_value, display_string)``. If the percentile is
        at the boundary, ``t_value`` is ``None`` and ``display_string`` is
        the boundary label. For PR ≤ 1, returns ``(None, label)``. For PR ≥ 99,
        returns ``(None, label)``.
    """
    try:
        t = percentile_to_t(percentile)
    except StatisticsError:
        return None, _BOUNDARY_LABEL
    else:
        return t, f"{t:.2f}"


def _t_to_z_clamped(t: float | None, percentile: int | None = None) -> float:
    """Convert a T-value to a Z-score, clamping to ``±3.0`` if ``None``.

    :param t: A T-value, or ``None`` for a boundary case.
    :param percentile: The original percentile (required if ``t`` is ``None``
        to determine the sign of the clamp).
    :return: The corresponding Z-score, or ``±3.0`` for boundary cases.
    """
    if t is None:
        # Clamp to -3.0 for low percentiles, +3.0 for high percentiles
        if percentile is not None and percentile < 50:  # noqa: PLR2004
            return -_Z_EXTREME
        return _Z_EXTREME
    return t_to_z(t)


def askyn(prompt: str) -> int:
    """Ask a yes/no/quit question and return an integer response.

    :param prompt: The question to display to the user.
    :return: ``1`` for yes, ``0`` for no, ``-1`` for quit.
    :raises ValueError: If the input is not a recognised yes/no/quit token.
    """
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
    raise ValueError(f"Invalid input {answ!r}. Only y, n, or q are allowed.")


def calculate_lv_korrektur(
    lv_rw: float,
    lv_korr_faktor: float,
    lv_pr_floor: int,
    lv_pr_ceil: int,
) -> tuple[float, int]:
    """Calculate the corrected LV raw score and percentile rank.

    Interpolates the corrected percentile rank (PR) between the floor and
    ceiling PR values, weighted by the fractional part of the corrected
    raw score.

    :param lv_rw: Uncorrected LV raw score.
    :param lv_korr_faktor: Correction factor to apply to the raw score.
    :param lv_pr_floor: PR corresponding to the floored corrected raw score.
    :param lv_pr_ceil: PR corresponding to the ceiled corrected raw score.
    :return: A tuple of ``(lv_rw_korr, lv_pr_korr)`` — the corrected raw
        score and the interpolated corrected percentile rank.
    :raises ValueError: If ``lv_korr_faktor`` is not positive, or if
        ``lv_pr_floor`` > ``lv_pr_ceil``.
    """
    if lv_korr_faktor <= 0:
        raise ValueError(f"lv_korr_faktor must be positive, got {lv_korr_faktor!r}.")
    if lv_pr_floor > lv_pr_ceil:
        raise ValueError(
            f"lv_pr_floor ({lv_pr_floor}) must not exceed lv_pr_ceil ({lv_pr_ceil})."
        )

    lv_rw_korr = lv_rw * lv_korr_faktor
    lv_rw_korr_nachkomma = lv_rw_korr % 1

    lv_pr_diff = lv_pr_ceil - lv_pr_floor
    lv_pr_korr = round_half_up(lv_pr_floor + lv_pr_diff * lv_rw_korr_nachkomma)

    return lv_rw_korr, lv_pr_korr


def get_indices(
    fn_csv: str | os.PathLike[str],
    correct_answ: int,
    incorrect_answ: int,
    num_processed: int,
    words_after_last_item: int,
    lv_pr_korr: int,
    lgs_pr_korr: int,
    lg_pr: int,
    lv_rw_korr: float,
    lgs_rw_korr: int,
) -> tuple[list[ResultsItem], float, float, float]:
    """Calculate LGVT indices and build the results list for the report.

    Reads item word-counts from a CSV file, computes raw scores, converts
    percentile ranks to T-values, and assembles the structured results list.

    :param fn_csv: Path to the LGVT CSV file containing item data.
    :param correct_answ: Number of correctly answered items.
    :param incorrect_answ: Number of incorrectly answered items.
    :param num_processed: Number of items the subject worked through.
    :param words_after_last_item: Words read after the last bracket item.
    :param lv_pr_korr: Corrected percentile rank for LV.
    :param lgs_pr_korr: Corrected percentile rank for LGS.
    :param lg_pr: Percentile rank for LGN.
    :param lv_rw_korr: Corrected LV raw score.
    :param lgs_rw_korr: Corrected LGS raw score.
    :return: A tuple of ``(results, lv_z, lgs_z, lg_z)`` — the structured
        results list and the three Z-scores for the plot. Z-scores are
        clamped to ±3.0 for boundary percentiles (0 or 100).
    :raises ValueError: If ``num_processed`` is zero or exceeds the number
        of rows in the CSV, or if the CSV is empty.
    :raises FileNotFoundError: If ``fn_csv`` does not exist.
    """
    csv_path = normalize_path(fn_csv)

    with csv_path.open(encoding="utf-8") as f:
        csv_data = list(csv.DictReader(f))

    if not csv_data:
        raise ValueError(f"CSV file {csv_path} is empty.")
    if num_processed == 0:
        raise ValueError("num_processed is zero — no items were processed.")
    if num_processed > len(csv_data):
        raise ValueError(
            f"num_processed ({num_processed}) exceeds number of "
            f"CSV rows ({len(csv_data)})."
        )

    words_until_last_item = int(csv_data[num_processed - 1]["Wortzahl"])
    lv_rw = correct_answ * 2 - incorrect_answ
    lgs_rw = words_until_last_item + words_after_last_item
    lg_rw = round_half_up((correct_answ / num_processed) * 100)

    lv_t, lv_t_str = _safe_percentile_to_t(lv_pr_korr)
    lgs_t, lgs_t_str = _safe_percentile_to_t(lgs_pr_korr)
    lg_t, lg_t_str = _safe_percentile_to_t(lg_pr)

    lv_z = _t_to_z_clamped(lv_t, lv_pr_korr)
    lgs_z = _t_to_z_clamped(lgs_t, lgs_pr_korr)
    lg_z = _t_to_z_clamped(lg_t, lg_pr)

    results: list[ResultsItem] = [
        "Items",
        ("Bearbeitete Items", str(num_processed)),
        ("Richtige Lösungen", str(correct_answ)),
        ("Falsche Lösungen", str(incorrect_answ)),
        "LV",
        ("Rohwert LV", str(lv_rw)),
        ("Rohwert LV nach Tzp.-Korrektur", str(lv_rw_korr)),
        ("PR", str(lv_pr_korr)),
        ("T-Wert", lv_t_str),
        "LGS",
        ("Wörter bis zur letzten Klammer", str(words_until_last_item)),
        ("Wörter nach der letzten Klammer", str(words_after_last_item)),
        ("Rohwert LGS", str(lgs_rw)),
        ("Rohwert LGS nach Tzp.-Korrektur", str(lgs_rw_korr)),
        ("PR", str(lgs_pr_korr)),
        ("T-Wert", lgs_t_str),
        "LGN",
        ("Rohwert LGN", f"{lg_rw}%"),
        ("PR", str(lg_pr)),
        ("T-Wert", lg_t_str),
    ]

    return results, lv_z, lgs_z, lg_z


def generate_lgvt_report(
    client_dict: ClientRecord,
    client_id: int,
    test_date: str,
    results: list[ResultsItem],
    lv_z: float,
    lgs_z: float,
    lg_z: float,
    version: str = "Rosenkohl",
    directory: str | os.PathLike[str] = ".",
) -> Path:
    """Generate the LGVT report PDF for a client.

    Builds a normal-distribution plot from the three Z-scores, assembles
    a :class:`~edupsyadmin.api.reports.TestReport`, writes it to disk, and
    cleans up the temporary plot file.

    :param client_dict: Decrypted client record containing name, grade, and
        birthday.
    :param client_id: Numeric client identifier, used as a fallback name and
        in the output filename.
    :param test_date: ISO-formatted test date string (``YYYY-MM-DD``).
    :param results: Structured results list as returned by
        :func:`get_indices`.
    :param lv_z: Z-score for Leseverständnis (LV).
    :param lgs_z: Z-score for Lesegeschwindigkeit (LGS).
    :param lg_z: Z-score for Lesegenauigkeit (LGN).
    :param version: LGVT version label, e.g. ``"Rosenkohl"``.
    :param directory: Directory in which to write the output PDF.
    :return: :class:`~pathlib.Path` to the generated PDF file.
    :raises ValueError: If the client record contains no birthday.
    :raises ValueError: If ``test_date`` is not a valid ``YYYY-MM-DD`` string.
    """
    try:
        t_day = datetime.strptime(test_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"test_date {test_date!r} is not a valid YYYY-MM-DD date."
        ) from e

    name = (
        (client_dict.first_name_encr or "") + " " + (client_dict.last_name_encr or "")
    ).strip() or str(client_id)
    schoolyear = int(client_dict.class_int_encr or 0)
    birthday = client_dict.birthday_encr

    if birthday is None:
        raise ValueError(f"No birthday found for client {client_id}")

    age_str = mydatediff(birthday, t_day)

    # Plot generation
    z_values = [lv_z, lgs_z, lg_z]
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

    directory_path = normalize_path(directory)
    output_fn = directory_path / f"{client_id}_Auswertung_LGVT.pdf"

    try:
        report = TestReport(data)
        report.build(output_fn)
    finally:
        # remove plot png
        if fn_plot.exists():
            fn_plot.unlink()

    return output_fn


def _prompt_float(prompt: str) -> float:
    """Prompt the user for a float value, retrying on invalid input.

    :param prompt: The prompt string to display.
    :return: A valid float entered by the user.
    """
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print(f"Invalid input {raw!r} — please enter a number.")


def _prompt_int(prompt: str) -> int:
    """Prompt the user for an integer value, retrying on invalid input.

    :param prompt: The prompt string to display.
    :return: A valid integer entered by the user.
    """
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print(f"Invalid input {raw!r} — please enter a whole number.")


def mk_report(
    database_url: str,
    client_id: int,
    test_date: str,
    version: str = "Rosenkohl",
    directory: str | os.PathLike[str] = ".",
) -> None:
    """Interactive CLI wrapper for generating an LGVT report.

    Guides the user through entering item responses and norm-table lookups,
    then delegates computation and PDF generation to :func:`get_indices` and
    :func:`generate_lgvt_report`.

    :param database_url: SQLAlchemy-compatible database URL for client data.
    :param client_id: Numeric identifier of the client to report on.
    :param test_date: ISO-formatted test date string (``YYYY-MM-DD``).
    :param version: LGVT version label used to look up the CSV path in
        config, e.g. ``"Rosenkohl"``.
    :param directory: Directory in which to write the output PDF.
    :raises ValueError: If the LGVT CSV path for ``version`` is not
        configured, or if no items were processed.
    """
    fn_csv = getattr(config.lgvtcsv, version, None)
    if fn_csv is None:
        raise ValueError(f"LGVT CSV path for version '{version}' is not configured.")

    client_dict = ClientsManager(database_url=database_url).get_decrypted_client(
        client_id
    )
    schoolyear = int(client_dict.class_int_encr or 0)

    with normalize_path(fn_csv).open(encoding="utf-8") as f:
        csv_data = list(csv.DictReader(f))

    # Item loop
    correct_answ = 0
    incorrect_answ = 0
    num_processed = 0

    print("Press quit for the first item the subject did not respond to.")
    for i, item in enumerate(csv_data):
        answ = askyn(f"{item['RichtigeAntwort']}? (y|n|q): ")
        if answ == 1:
            correct_answ += 1
        elif answ == 0:
            incorrect_answ += 1
        elif answ == -1:
            num_processed = i
            break
    else:
        num_processed = len(csv_data)

    if num_processed == 0:
        raise ValueError("No items were processed.")

    # Additional input
    words_after_last_item = _prompt_int("Words read after the last item: ")

    # Norm-table lookups (grade-dependent)
    if schoolyear < MAX_KORREKTUR_SCHOOLYEAR:
        lv_korr_faktor = _prompt_float("Korrekturfaktor LV: ")
        lv_rw_korr_floor = math.floor(
            (correct_answ * 2 - incorrect_answ) * lv_korr_faktor
        )
        lv_rw_korr_ceil = math.ceil(
            (correct_answ * 2 - incorrect_answ) * lv_korr_faktor
        )
        lv_pr_floor = _prompt_int(f"Rohwert abger. LV = {lv_rw_korr_floor}; PR = ")
        lv_pr_ceil = _prompt_int(f"Rohwert aufger. LV = {lv_rw_korr_ceil}; PR = ")
        lv_rw_korr, lv_pr_korr = calculate_lv_korrektur(
            lv_rw=correct_answ * 2 - incorrect_answ,
            lv_korr_faktor=lv_korr_faktor,
            lv_pr_floor=lv_pr_floor,
            lv_pr_ceil=lv_pr_ceil,
        )

        lgs_korr_faktor = _prompt_float("Korrekturfaktor LGS: ")
        words_until_last_item = int(csv_data[num_processed - 1]["Wortzahl"])
        lgs_rw = words_until_last_item + words_after_last_item
        lgs_rw_korr = round_half_up(lgs_rw * lgs_korr_faktor)
    else:
        lv_rw_korr = float(correct_answ * 2 - incorrect_answ)
        lv_pr_korr = _prompt_int(f"Rohwert LV = {int(lv_rw_korr)}; PR = ")
        words_until_last_item = int(csv_data[num_processed - 1]["Wortzahl"])
        lgs_rw_korr = words_until_last_item + words_after_last_item

    lgs_pr_korr = _prompt_int(f"Rohwert LGS = {lgs_rw_korr}; PR = ")
    lg_rw = round_half_up((correct_answ / num_processed) * 100)
    lg_pr = _prompt_int(f"Rohwert LG = {lg_rw}; PR = ")

    results, lv_z, lgs_z, lg_z = get_indices(
        fn_csv=fn_csv,
        correct_answ=correct_answ,
        incorrect_answ=incorrect_answ,
        num_processed=num_processed,
        words_after_last_item=words_after_last_item,
        lv_pr_korr=lv_pr_korr,
        lgs_pr_korr=lgs_pr_korr,
        lg_pr=lg_pr,
        lv_rw_korr=lv_rw_korr,
        lgs_rw_korr=lgs_rw_korr,
    )

    generate_lgvt_report(
        client_dict=client_dict,
        client_id=client_id,
        test_date=test_date,
        results=results,
        lv_z=lv_z,
        lgs_z=lgs_z,
        lg_z=lg_z,
        version=version,
        directory=directory,
    )
