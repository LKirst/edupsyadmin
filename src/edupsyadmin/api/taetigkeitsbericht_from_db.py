from pathlib import Path

import pandas as pd

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.reports import TaetigkeitsberichtReport
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger

try:
    import dataframe_image as dfi

    dfi_imported = True
except ImportError:
    dfi_imported = False

pd.set_option("display.precision", 1)


def get_subcategories(
    categorykey: str, extrcategories: list[str] | None = None
) -> list[str]:
    """
    Extract all hierarchical subcategories from a dot-separated category key.

    :param categorykey: Dot-separated category string
    :param extrcategories: Accumulated list of categories (used in recursion)
    :return: List of categories
    """
    if extrcategories is None:
        extrcategories = []
    extrcategories.append(categorykey)

    if "." not in categorykey:
        return extrcategories

    parent_category = categorykey.rsplit(".", 1)[0]
    return get_subcategories(parent_category, extrcategories)


def add_categories_to_df(
    df: pd.DataFrame,
    category_colnm: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Take a df with columns keyword_taet_encr, h_sessions, n_sessions
    and create a table with an estimated count of sessions

    :param df: DataFrame with keyword_taet_encr, h_sessions, n_sessions
    :param category_colnm: name of the category column (e.g. keyword_taet_encr)
    :return: A tuple containing the modified DataFrame and a summary DataFrame
    """

    # get a set of unique keys from the category column
    # (keyword_taet_encr; not yet accounting for the hierarchy of
    # categories)
    category_keys = sorted(set(df.loc[:, category_colnm].unique()))

    # for every category (keys and their superordinate categories) add a column;
    # if the row belongs to that category, set the value of the category column to
    # the value of h_sessions
    categories_all = []
    for key in category_keys:
        subcategories = get_subcategories(key)
        df.loc[df[category_colnm] == key, subcategories] = df.loc[
            df[category_colnm] == key, "h_sessions"
        ]
        categories_all.extend(subcategories)

    # create a df  with only the category columns
    categories_all_set = sorted(set(categories_all))
    categories_df = df[categories_all_set]

    # create a temporary DataFrame for counting based on n_sessions
    # This aligns the n_sessions with the categories for accurate counting
    count_df = df[["n_sessions", *categories_all_set]].copy()
    # Fill non-relevant category cells with 0 so we can group by them
    count_df[categories_all_set] = count_df[categories_all_set].notna().astype(int)

    summary_categories = categories_df.describe()
    summary_categories.loc["sum", :] = categories_df.agg("sum", axis=0)

    for cat in categories_all_set:
        # Filter for rows belonging to the current category
        cat_specific_counts = count_df[count_df[cat] == 1]["n_sessions"]

        summary_categories.loc["count_mt3_sessions", cat] = (
            cat_specific_counts > 3
        ).sum()
        summary_categories.loc["count_2to3_sessions", cat] = (
            cat_specific_counts.between(2, 3).sum()
        )
        summary_categories.loc["count_1_session", cat] = (
            cat_specific_counts == 1
        ).sum()

    return df, summary_categories


def summary_statistics_h_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Sum up Zeitstunden (h_sessions) per school and in total"""
    h_sessions = df.groupby("school")["h_sessions"].describe()
    h_sessions.loc[:, "sum"] = df.groupby("school")["h_sessions"].agg("sum")
    total = df["h_sessions"].describe()
    total["sum"] = df["h_sessions"].agg("sum")
    h_sessions.loc["all", :] = total
    return h_sessions


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
        pd.to_numeric(wstds.at["wd_year", "value"])
        / pd.to_numeric(wstds.at["wd_week", "value"]),
        "Arbeitswochen/Jahr",
    ]
    wstds.loc["zstd_week", :] = [40, "h/Woche"]
    wstds.loc["zstd_day", :] = [
        pd.to_numeric(wstds.at["zstd_week", "value"])
        / pd.to_numeric(wstds.at["wd_week", "value"]),
        "h/Arbeitstag",
    ]
    wstds.loc["zstd_year", :] = [
        pd.to_numeric(wstds.at["zstd_day", "value"])
        * pd.to_numeric(wstds.at["wd_year", "value"]),
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
        pd.to_numeric(wstds.at["zstd_year", "value"]) / wstd_total
        if wstd_total > 0
        else 0,
        ("h Arbeit / Jahr, die einer Wochenstunde entsprächen"),
    ]
    wstds.loc["zstd_spsy_year_target", :] = [
        pd.to_numeric(wstds.at["zstd_spsy_1wstd_target", "value"]) * wstd_spsy,
        (
            "h Arbeit / Jahr, die den angegebenen Wochenstunden "
            "Schulpsychologie entsprächen"
        ),
    ]
    wstds.loc["zstd_spsy_week_target", :] = [
        pd.to_numeric(wstds.at["zstd_spsy_year_target", "value"])
        / pd.to_numeric(wstds.at["ww_year", "value"]),
        (
            "h Arbeit in der Woche, die den angegebenen Wochenstunden "
            "Schulpsychologie entsprächen"
        ),
    ]
    return wstds


def summary_statistics_wstd(
    wstd_spsy: int,
    wstd_total: int,
    zstd_spsy_year_actual: float,
    school_students: dict[str, int],
) -> pd.DataFrame:
    """Calculate Wochenstunden summary statistics

    Parameters
    ----------
    wstd_spsy : int
        n Wochenstunden school psychology
    wstd_total : int, optional
        total n Wochenstunden (not just school psychology), by default 23
    zst_spsy_year_actual: float
        actual Zeitstunden school psychology
    school_students:
        a dictionary mapping school names to their number of students
        e.g. {'Schulname': 100, 'SchulnameB': 200}

    Returns
    -------
    pd.DataFrame
        Wochenstunden summary statistics
    """
    summarystats_wstd = wstd_in_zstd(wstd_spsy, wstd_total)

    for school_name, student_count in school_students.items():
        summarystats_wstd.loc["nstudents_" + school_name, "value"] = student_count

    nstudents_total = sum(school_students.values())
    summarystats_wstd.loc["nstudents_all", "value"] = nstudents_total
    summarystats_wstd.loc["ratio_nstudens_wstd_spsy", "value"] = (
        nstudents_total / wstd_spsy if wstd_spsy > 0 else 0
    )

    if zstd_spsy_year_actual is not None:
        summarystats_wstd.loc["zstd_spsy_year_actual", "value"] = zstd_spsy_year_actual
        summarystats_wstd.loc["zstd_spsy_week_actual", "value"] = (
            zstd_spsy_year_actual
            / pd.to_numeric(summarystats_wstd.at["ww_year", "value"])
        )
        target = pd.to_numeric(summarystats_wstd.at["zstd_spsy_year_target", "value"])
        summarystats_wstd.loc["perc_spsy_year_actual", "value"] = (
            zstd_spsy_year_actual / target if target > 0 else 0
        ) * 100
    return summarystats_wstd


def create_taetigkeitsbericht_report(
    basename_out: str,
    name: str,
    summary_wstd: pd.DataFrame,
    summary_categories: pd.DataFrame | None = None,
    summary_h_sessions: pd.DataFrame | None = None,
) -> None:
    if dfi_imported:
        Path("resources").mkdir(parents=True, exist_ok=True)
        wstd_img = "resources/summary_wstd.png"
        dfi.export(summary_wstd, wstd_img, table_conversion="matplotlib")
        h_sessions_img = None
        if summary_h_sessions is not None:
            h_sessions_img = "resources/summary_h_sessions.png"
            dfi.export(
                summary_h_sessions, h_sessions_img, table_conversion="matplotlib"
            )

        report = TaetigkeitsberichtReport(name)
        report.build(
            basename_out + "_report.pdf",
            summary_wstd_img=wstd_img,
            summary_h_sessions_img=h_sessions_img,
            summary_categories=summary_categories,
        )
    else:
        logger.warning("dataframe_image is not installed to generate a pdf output.")


def taetigkeitsbericht(
    database_url: str,
    wstd_psy: int,
    out_basename: str = "Taetigkeitsbericht_Out",
    wstd_total: int = 23,
    name: str = "Schulpsychologie",
) -> None:
    """
    Create a PDF for the Taetigkeitsbericht. This function assumes your db
    has the columns 'keyword_taet_encr', 'min_sessions' and 'n_sessions'
    and reads nstudents from the config.

    param wstd_psy [int]: Anrechnungsstunden in Wochenstunden
    param out_basename [str]: base name for the output files.
        Defaults to "Taetigkeitsbericht_Out".
    param wstd_total [int]: total Wochstunden (depends on your school).
        Defaults to 23.
    )
    param name [str]: name for the header of the pdf report.
        Defaults to "Schulpsychologie".
    )
    """

    # Query the data
    clients_manager = ClientsManager(
        database_url=database_url,
    )
    # Only fetch required columns
    df = clients_manager.get_clients_overview(
        columns=["keyword_taet_encr", "min_sessions", "n_sessions"]
    )
    df["h_sessions"] = df["min_sessions"] / 60.0

    df, summary_categories = add_categories_to_df(df, "keyword_taet_encr")
    df.to_csv(out_basename + "_df.csv")
    print(df)
    summary_categories.to_csv(out_basename + "_categories.csv")
    print(summary_categories)

    # Summary statistics for h_sessions
    summarystats_h_sessions = summary_statistics_h_sessions(df)
    summarystats_h_sessions.to_csv(out_basename + "_h_sessions.csv")
    print(summarystats_h_sessions)

    zstd_spsy_year_actual = pd.to_numeric(summarystats_h_sessions.loc["all", "sum"])

    # Get student data from the config
    school_students_dict = {
        school.school_name: school.nstudents for school in config.school.values()
    }

    # Summary statistics for Wochenstunden
    summarystats_wstd = summary_statistics_wstd(
        wstd_psy, wstd_total, zstd_spsy_year_actual, school_students_dict
    )
    summarystats_wstd.to_csv(out_basename + "_wstd.csv")
    print(summarystats_wstd)

    create_taetigkeitsbericht_report(
        out_basename,
        name,
        summarystats_wstd,
        summary_categories,
        summarystats_h_sessions,
    )
