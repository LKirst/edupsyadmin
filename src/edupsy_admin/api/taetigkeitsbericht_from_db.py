import os
import re
import argparse
import logging
from datetime import date

import pandas as pd
import numpy as np

import dataframe_image as dfi
from fpdf import FPDF

from .clients import get_data_raw

pd.set_option("display.precision", 1)


class Report(FPDF):
    def __init__(self, name):
        super().__init__()
        self.WIDTH = 210
        self.HEIGHT = 297
        self.header_text = f"Tätigkeitsbericht {date.today()} ({name})"

    def header(self):
        self.set_font("Arial", "B", 11)
        self.cell(w=0, h=10, txt=self.header_text, border=0, ln=0, align="C")
        self.ln(20)

    def footer(self):
        # page numbers
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, "Page " + str(self.page_no()), border=0, ln=0, align="C")


def get_subcategories(categorykey: str, extrcategories: list[str] = None) -> list[str]:
    if extrcategories is None:
        extrcategories = []
    extrcategories.append(categorykey)
    root, subcategory_suffix = os.path.splitext(categorykey)
    if not subcategory_suffix:
        return extrcategories
    else:
        return get_subcategories(root, extrcategories)


def add_categories_to_df(df: pd.DataFrame, category_colnm: str) -> pd.DataFrame:
    category_keys = sorted(set(df.loc[:, category_colnm].unique()))
    categories_all = []
    for key in category_keys:
        subcategories = get_subcategories(key)
        df.loc[df[category_colnm] == key, subcategories] = df.loc[
            df[category_colnm] == key, "n_sessions"
        ]
        categories_all.extend(subcategories)

    categories_all_set = list(sorted(set(categories_all)))
    categories_df = df[categories_all_set]
    summary_categories = categories_df.describe()
    summary_categories.loc["sum", :] = categories_df.agg("sum", axis=0)
    summary_categories.loc["count_mt3_sessions", :] = categories_df[
        categories_df > 3
    ].agg("count", axis=0)
    summary_categories.loc["count_1to3_sessions", :] = categories_df[
        (categories_df <= 3) & (categories_df >= 1)
    ].agg("count", axis=0)
    summary_categories.loc["count_einm_kurzkont", :] = categories_df[
        categories_df < 1
    ].agg("count", axis=0)

    return df, summary_categories


def summary_statistics_n_sessions(df: pd.DataFrame, min_per_ses=45) -> pd.DataFrame:
    n_sessions = df.groupby("school")["n_sessions"].describe()
    n_sessions.loc[:, "sum"] = df.groupby("school")["n_sessions"].agg("sum")
    total = df["n_sessions"].describe()
    total["sum"] = df["n_sessions"].agg("sum")
    n_sessions.loc["all", :] = total
    n_sessions["zeitstunden"] = n_sessions["sum"] * min_per_ses / 60
    return n_sessions


def wstd_in_zstd(wstd_spsy: int, wstd_total: int = 23) -> pd.DataFrame:
    """Create a dataframe of Wochenstunden and Zeitstunden for school
    psychology.

    Parameters
    ----------
    wstd_spsy: int
        n Wochenstunden insgesamt (Anrechnungsstunden und Unterricht)
    wstd_total: int
        n Wochenstunden Schulpsychologie (Anrechnungsstunden)

    Returns
    -------
    pd.DataFrame
        A dataframe with values for the conversion of Wochenstunden to
        Zeitstunden.
    """
    wstds = pd.DataFrame(columns=["value", "description"])

    wstds.loc["wd_week", :] = [5, "Arbeitstage/Woche"]
    wstds.loc["wd_year", :] = [
        251 - 30,
        "Arbeitstage/Jahr nach Abzug von 30 Tagen Urlaub",
    ]
    wstds.loc["ww_year", :] = [
        wstds.loc["wd_year", "value"] / wstds.loc["wd_week", "value"],
        "Arbeitswochen/Jahr",
    ]
    wstds.loc["zstd_week", :] = [40, "h/Woche"]
    wstds.loc["zstd_day", :] = [
        wstds.loc["zstd_week", "value"] / wstds.loc["wd_week", "value"],
        "h/Arbeitstag",
    ]
    wstds.loc["zstd_year", :] = [
        wstds.loc["zstd_day", "value"] * wstds.loc["wd_year", "value"],
        "h/Jahr",
    ]
    wstds.loc["wstd_total_target", :] = [
        wstd_total,
        ("n Wochenstunden insgesamt (Anrechnungsstunden und Unterricht)"),
    ]
    wstds.loc["wstd_spsy", :] = [
        wstd_spsy,
        "n Wochenstunden Schulpsychologie (Anrechnungsstunden)",
    ]
    wstds.loc["zstd_spsy_1wstd_target", :] = [
        wstds.loc["zstd_year", "value"] / wstd_total,
        ("h Arbeit / Jahr, die einer Wochenstunde entsprächen"),
    ]
    wstds.loc["zstd_spsy_year_target", :] = [
        wstds.loc["zstd_spsy_1wstd_target", "value"] * wstd_spsy,
        (
            "h Arbeit / Jahr, die den angegebenen Wochenstunden "
            "Schulpsychologie entsprächen"
        ),
    ]
    wstds.loc["zstd_spsy_week_target", :] = [
        wstds.loc["zstd_spsy_year_target", "value"] / wstds.loc["ww_year", "value"],
        (
            "h Arbeit in der Woche, die den angegebenen Wochenstunden "
            "Schulpsychologie entsprächen"
        ),
    ]
    return wstds


def summary_statistics_wstd(
    wstd_spsy: int, wstd_total: int, zstd_spsy_year_actual: float, *schools: str
) -> pd.DataFrame:
    """Calculate Wochenstunden summary statistics

    Parameters
    ----------
    wstd_spsy : int
        n Wochenstunden school psychology
    wstd_total : int, optional
        total n Wochenstunden (not just school psychology), by default 23
    zst_spsy_year_actual: float, optional
        actual Zeitstunden school psychology
    *schools : str
        strings with name of the school and n students for the respective school,
        e.g. 'Schulname625'

    Returns
    -------
    pd.DataFrame
        Wochenstunden summary statistics
    """
    summarystats_wstd = wstd_in_zstd(wstd_spsy, wstd_total)

    pattern = re.compile("([^\d]+)(\d+)")
    nstudents = {
        pattern.match(school).groups()[0]: int(pattern.match(school).groups()[1])
        for school in schools
    }

    for schoolnm, schoolnstudents in nstudents.items():
        summarystats_wstd.loc["nstudents_" + schoolnm, "value"] = schoolnstudents
    summarystats_wstd.loc["nstudents_all", "value"] = sum(nstudents.values())
    summarystats_wstd.loc["ratio_nstudens_wstd_spsy", "value"] = (
        sum(nstudents.values()) / wstd_spsy
    )

    if zstd_spsy_year_actual is not None:
        summarystats_wstd.loc["zstd_spsy_year_actual", "value"] = zstd_spsy_year_actual
        summarystats_wstd.loc["zstd_spsy_week_actual", "value"] = (
            zstd_spsy_year_actual / summarystats_wstd.loc["ww_year", "value"]
        )
        summarystats_wstd.loc["perc_spsy_year_actual", "value"] = (
            zstd_spsy_year_actual
            / summarystats_wstd.loc["zstd_spsy_year_target", "value"]
        ) * 100
    return summarystats_wstd


def create_taetigkeitsbericht_report(
    basename_out: str,
    name: str,
    summary_wstd: pd.Series,
    summary_categories: pd.DataFrame = None,
    summary_n_sessions: pd.DataFrame = None,
) -> None:
    if not os.path.exists("resources"):
        os.makedirs("resources")
    wstd_img = "resources/summary_wstd.png"
    dfi.export(summary_wstd, wstd_img, table_conversion="matplotlib")
    if summary_n_sessions is not None:
        n_sessions_img = "resources/summary_n_sessions.png"
        dfi.export(summary_n_sessions, n_sessions_img, table_conversion="matplotlib")

    report = Report(name)
    if summary_categories is not None:
        report.add_page()
        for nm, val in summary_categories.items():
            report.cell(w=15, h=9, border=0, txt=f"{nm}:")
            report.ln(6)
            for text in [
                "einmaliger Kurzkontakt",
                "1-3 Sitzungen",
                "mehr als 3 Sitzungen",
            ]:
                report.cell(w=50, h=9, border=0, txt=text)
            report.ln(6)  # linebreak
            for colnm in [
                "count_einm_kurzkont",
                "count_1to3_sessions",
                "count_mt3_sessions",
            ]:
                report.cell(w=50, h=9, border=0, txt=f"{val[colnm]:.0f}")
            report.ln(18)  # linebreak
    if summary_n_sessions is not None:
        report.add_page()
        report.image(n_sessions_img, x=15, y=report.HEIGHT * 1 / 4, w=180)
    report.add_page()
    report.image(wstd_img, x=15, y=20, w=report.WIDTH - 20)
    report.output(basename_out + "_report.pdf")


def taetigkeitsbericht(
    app_username,
    app_uid,
    database_url,
    config_path,
    wstd_psy: int,
    nstudents: list,
    out_basename: str = "Taetigkeitsbericht_Out",
    min_per_ses: int = 45,
    wstd_total: int = 23,
    name: str = "Schulpsychologie",
) -> None:
    """
    Create a PDF for the Taetigkeitsbericht. This function assumes your db has the columns 'keyword_taetigkeitsbericht' and 'n_sessions'

    param wstd_psy [int]: Anrechnungsstunden in Wochenstunden
    param nstudents [list]: list of strings with item containing the name of
        the school and the number of students at that school, e.g. Schulname625
    param out_basename [str]: base name for the output files.
        Defaults to "Taetigkeitsbericht_Out".
    param min_per_ses [int]: duration of one session in minutes.
        Defaults to 45.
    param wstd_total [int]: total Wochstunden (depends on your school).
        Defaults to 23.
    )
    param name [str]: name for the header of the pdf report.
        Defaults to "Schulpsychologie".
    )
    """

    # Query the data
    df = get_data_raw(app_username, app_uid, database_url, config_path)
    df, summary_categories = add_categories_to_df(df, "keyword_taetigkeitsbericht")
    df.to_csv(out_basename + "_df.csv")
    print(df)
    summary_categories.to_csv(out_basename + "_categories.csv")
    print(summary_categories)

    # Summary statistics for n_sessions
    summarystats_n_sessions = summary_statistics_n_sessions(df, min_per_ses=min_per_ses)
    summarystats_n_sessions.to_csv(out_basename + "_n_sessions.csv")
    print(summarystats_n_sessions)

    zstd_spsy_year_actual = summarystats_n_sessions.loc["all", "zeitstunden"]

    # Summary statistics for Wochenstunden
    summarystats_wstd = summary_statistics_wstd(
        wstd_psy, wstd_total, zstd_spsy_year_actual, *nstudents
    )
    summarystats_wstd.to_csv(out_basename + "_wstd.csv")
    print(summarystats_wstd)

    create_taetigkeitsbericht_report(
        out_basename,
        name,
        summarystats_wstd,
        summary_categories,
        summarystats_n_sessions,
    )
