from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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


def get_subcategories(category_key: str) -> list[str]:
    """
    Extract all hierarchical subcategories from a dot-separated category key.

    Example: 'a.b.c' -> ['a.b.c', 'a.b', 'a']
    """
    parts = category_key.split(".")
    return [".".join(parts[:i]) for i in range(len(parts), 0, -1)]


def add_categories_to_df(
    df: pd.DataFrame,
    category_colnm: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process hierarchical categories and generate summary statistics.
    """
    # Identify all unique categories and their superordinate parents
    all_categories = set()
    for key in df[category_colnm].unique():
        if pd.notna(key):
            all_categories.update(get_subcategories(str(key)))

    sorted_categories = sorted(all_categories)

    # For each category, create a column containing h_sessions if the row matches
    for cat in sorted_categories:
        # A row matches a category if its specific key starts with that category
        # (and is followed by a dot or is the exact key)
        mask = df[category_colnm].apply(
            lambda k, cat=cat: str(k) == cat or str(k).startswith(f"{cat}."),
        )
        df.loc[mask, cat] = df.loc[mask, "h_sessions"]

    categories_df = df[sorted_categories]

    # Create summary DataFrame
    summary = categories_df.describe()
    summary.loc["sum", :] = categories_df.sum()

    # Add counts for session brackets
    for cat in sorted_categories:
        mask = df[cat].notna()
        cat_sessions = df.loc[mask, "n_sessions"]

        summary.loc["count_mt3_sessions", cat] = (cat_sessions > 3).sum()
        summary.loc["count_2to3_sessions", cat] = cat_sessions.between(2, 3).sum()
        summary.loc["count_1_session", cat] = (cat_sessions == 1).sum()

    return df, summary


def summary_statistics_h_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """Sum up Zeitstunden (h_sessions) per school and in total"""
    h_sessions = df.groupby("school")["h_sessions"].describe()
    h_sessions.loc[:, "sum"] = df.groupby("school")["h_sessions"].agg("sum")
    total = df["h_sessions"].describe()
    total["sum"] = df["h_sessions"].agg("sum")
    h_sessions.loc["all", :] = total
    return h_sessions


@dataclass
class ActivitySummary:
    """Encapsulates all calculations for activity report statistics."""

    wstd_spsy: int
    wstd_total: int = 23
    days_per_week: int = 5
    vacation_days: int = 30
    hours_per_week_std: float = 40.0
    school_students: dict[str, int] = field(default_factory=dict)
    zstd_spsy_year_actual: float | None = None

    @property
    def work_days_per_year(self) -> int:
        """Total work days in a year after deducting vacation."""
        return 251 - self.vacation_days

    @property
    def work_weeks_per_year(self) -> float:
        """Total work weeks in a year."""
        return self.work_days_per_year / self.days_per_week

    @property
    def hours_per_day(self) -> float:
        """Standard working hours per day."""
        return self.hours_per_week_std / self.days_per_week

    @property
    def hours_per_year_total(self) -> float:
        """Total working hours in a year for a full position."""
        return self.hours_per_day * self.work_days_per_year

    @property
    def hours_per_wstd(self) -> float:
        """Hours per year corresponding to one 'Wochenstunde'."""
        return (
            self.hours_per_year_total / self.wstd_total if self.wstd_total > 0 else 0.0
        )

    @property
    def target_hours_year(self) -> float:
        """Target working hours per year based on school psychology hours."""
        return self.hours_per_wstd * self.wstd_spsy

    @property
    def target_hours_week(self) -> float:
        """Target working hours per week."""
        return self.target_hours_year / self.work_weeks_per_year

    @property
    def n_students_all(self) -> int:
        """Total number of students across all schools."""
        return sum(self.school_students.values())

    @property
    def ratio_nstudents_wstd_spsy(self) -> float:
        """Ratio of total students to school psychology hours."""
        return self.n_students_all / self.wstd_spsy if self.wstd_spsy > 0 else 0.0

    @property
    def zstd_spsy_week_actual(self) -> float | None:
        """Actual working hours per week based on recorded sessions."""
        if self.zstd_spsy_year_actual is None:
            return None
        return self.zstd_spsy_year_actual / self.work_weeks_per_year

    @property
    def perc_spsy_year_actual(self) -> float | None:
        """Percentage of target hours actually worked."""
        if self.zstd_spsy_year_actual is None or self.target_hours_year <= 0:
            return None
        return (self.zstd_spsy_year_actual / self.target_hours_year) * 100

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the summary to a DataFrame for report generation."""
        stats_data: dict[str, list[Any]] = {
            "wd_week": [self.days_per_week, "Arbeitstage/Woche"],
            "wd_year": [
                self.work_days_per_year,
                "Arbeitstage/Jahr nach Abzug von 30 Tagen Urlaub",
            ],
            "ww_year": [self.work_weeks_per_year, "Arbeitswochen/Jahr"],
            "zstd_week": [self.hours_per_week_std, "h/Woche"],
            "zstd_day": [self.hours_per_day, "h/Arbeitstag"],
            "zstd_year": [self.hours_per_year_total, "h/Jahr"],
            "wstd_total_target": [
                self.wstd_total,
                "n Wochenstunden insgesamt (Anrechnungsstunden und Unterricht)",
            ],
            "wstd_spsy": [
                self.wstd_spsy,
                "n Wochenstunden Schulpsychologie (Anrechnungsstunden)",
            ],
            "zstd_spsy_1wstd_target": [
                self.hours_per_wstd,
                "h Arbeit / Jahr, die einer Wochenstunde entsprächen",
            ],
            "zstd_spsy_year_target": [
                self.target_hours_year,
                "h Arbeit / Jahr, die den angegebenen Wochenstunden "
                "Schulpsychologie entsprächen",
            ],
            "zstd_spsy_week_target": [
                self.target_hours_week,
                "h Arbeit in der Woche, die den angegebenen Wochenstunden "
                "Schulpsychologie entsprächen",
            ],
            "nstudents_all": [self.n_students_all, ""],
            "ratio_nstudens_wstd_spsy": [self.ratio_nstudents_wstd_spsy, ""],
        }

        for school_name, student_count in self.school_students.items():
            stats_data[f"nstudents_{school_name}"] = [student_count, ""]

        if self.zstd_spsy_year_actual is not None:
            stats_data["zstd_spsy_year_actual"] = [self.zstd_spsy_year_actual, ""]
            stats_data["zstd_spsy_week_actual"] = [self.zstd_spsy_week_actual, ""]
            stats_data["perc_spsy_year_actual"] = [self.perc_spsy_year_actual, ""]

        return pd.DataFrame.from_dict(
            stats_data,
            orient="index",
            columns=["value", "description"],
        )


def wstd_in_zstd(wstd_spsy: int, wstd_total: int = 23) -> pd.DataFrame:
    """
    Create a dataframe of Wochenstunden and Zeitstunden for school psychology.
    """
    return ActivitySummary(wstd_spsy=wstd_spsy, wstd_total=wstd_total).to_dataframe()


def summary_statistics_wstd(
    wstd_spsy: int,
    wstd_total: int,
    zstd_spsy_year_actual: float,
    school_students: dict[str, int],
) -> pd.DataFrame:
    """Calculate Wochenstunden summary statistics."""
    return ActivitySummary(
        wstd_spsy=wstd_spsy,
        wstd_total=wstd_total,
        zstd_spsy_year_actual=zstd_spsy_year_actual,
        school_students=school_students,
    ).to_dataframe()


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
                summary_h_sessions,
                h_sessions_img,
                table_conversion="matplotlib",
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

    # Only fetch required columns
    df = ClientsManager(
        database_url=database_url,
    ).get_clients_overview(
        columns=["keyword_taet_encr", "min_sessions", "n_sessions"],
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
        wstd_psy,
        wstd_total,
        zstd_spsy_year_actual,
        school_students_dict,
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
