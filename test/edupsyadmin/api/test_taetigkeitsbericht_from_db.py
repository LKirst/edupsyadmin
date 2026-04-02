from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from edupsyadmin.api.taetigkeitsbericht_from_db import (
    add_categories_to_df,
    create_taetigkeitsbericht_report,
    get_subcategories,
    summary_statistics_h_sessions,
    summary_statistics_wstd,
    taetigkeitsbericht,
    wstd_in_zstd,
)


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "category": ["cat1", "cat2.sub", "cat2"],
            "h_sessions": [5.3, 1.0, 2.5],
            # 4 is >3 sessions; 1 is single session; 2 is 2-3 sessions
            "n_sessions": [4, 1, 2],
        }
    )


@pytest.fixture()
def summary_wstd_df() -> pd.DataFrame:
    return pd.DataFrame(
        {"value": [5, 251, 50]},
        index=["wstd_spsy", "wd_year", "zstd_week"],
    )


@pytest.fixture()
def summary_categories_df() -> pd.DataFrame:
    return pd.DataFrame(
        {"cat1": [5, 1, 1, 0], "cat2.sub": [3, 0, 1, 1]},
        index=[
            "sum",
            "count_mt3_sessions",
            "count_2to3_sessions",
            "count_1_session",
        ],
    )


@pytest.fixture()
def summary_h_sessions_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "count": [2, 1, 3],
            "mean": [4.0, 2.0, 3.333],
            "sum": [8, 2, 10],
        },
        index=["school1", "school2", "all"],
    )


def test_get_subcategories_single():
    assert get_subcategories("category") == ["category"]


def test_get_subcategories_two_levels():
    assert get_subcategories("category.sub") == ["category.sub", "category"]


def test_get_subcategories_three_levels():
    assert get_subcategories("category.sub.sub2") == [
        "category.sub.sub2",
        "category.sub",
        "category",
    ]


def test_add_categories_to_df_columns(sample_df):
    df, _ = add_categories_to_df(sample_df, "category")
    assert "cat1" in df.columns
    assert "cat2" in df.columns
    assert "cat2.sub" in df.columns


def test_add_categories_to_df_sums(sample_df):
    _, summary = add_categories_to_df(sample_df, "category")
    assert summary.loc["sum", "cat1"] == pytest.approx(5.3)
    # cat2 column covers both the direct cat2 row (2.5) and cat2.sub row (1.0)
    assert summary.loc["sum", "cat2"] == pytest.approx(3.5)


def test_add_categories_to_df_session_counts_cat1(sample_df):
    """cat1 row has n_sessions=4, which is >3."""
    _, summary = add_categories_to_df(sample_df, "category")
    assert summary.loc["count_mt3_sessions", "cat1"] == 1
    assert summary.loc["count_2to3_sessions", "cat1"] == 0
    assert summary.loc["count_1_session", "cat1"] == 0


def test_add_categories_to_df_session_counts_cat2sub(sample_df):
    """cat2.sub row has n_sessions=1."""
    _, summary = add_categories_to_df(sample_df, "category")
    assert summary.loc["count_mt3_sessions", "cat2.sub"] == 0
    assert summary.loc["count_2to3_sessions", "cat2.sub"] == 0
    assert summary.loc["count_1_session", "cat2.sub"] == 1


def test_add_categories_to_df_session_counts_cat2_parent(sample_df):
    """cat2 parent column covers its own row (n_sessions=2) and
    the cat2.sub row (n_sessions=1), so both contribute to cat2 counts."""
    _, summary = add_categories_to_df(sample_df, "category")
    assert summary.loc["count_mt3_sessions", "cat2"] == 0
    assert summary.loc["count_2to3_sessions", "cat2"] == 1  # direct cat2 row
    assert summary.loc["count_1_session", "cat2"] == 1  # cat2.sub row


def test_summary_statistics_h_sessions_per_school():
    df = pd.DataFrame(
        {"school": ["school1", "school2", "school1"], "h_sessions": [5.2, 2.0, 3.0]}
    )
    result = summary_statistics_h_sessions(df)
    assert result.loc["school1", "sum"] == pytest.approx(8.2)
    assert result.loc["school2", "sum"] == pytest.approx(2.0)


def test_summary_statistics_h_sessions_total():
    df = pd.DataFrame(
        {"school": ["school1", "school2", "school1"], "h_sessions": [5.2, 2.0, 3.0]}
    )
    result = summary_statistics_h_sessions(df)
    assert result.loc["all", "sum"] == pytest.approx(10.2)


def test_wstd_in_zstd_input_stored():
    result = wstd_in_zstd(5)
    assert pd.to_numeric(result.loc["wstd_spsy", "value"]) == 5


def test_wstd_in_zstd_weekly_target_positive():
    result = wstd_in_zstd(5)
    assert pd.to_numeric(result.loc["zstd_spsy_week_target", "value"]) > 0


def test_wstd_in_zstd_yearly_target_proportional():
    """Doubling wstd_spsy should double the yearly target hours."""
    result_5 = wstd_in_zstd(5)
    result_10 = wstd_in_zstd(10)
    target_5 = pd.to_numeric(result_5.loc["zstd_spsy_year_target", "value"])
    target_10 = pd.to_numeric(result_10.loc["zstd_spsy_year_target", "value"])
    assert target_10 == pytest.approx(target_5 * 2)


def test_summary_statistics_wstd_student_counts():
    school_students = {"SchoolA": 100, "SchoolB": 200}
    result = summary_statistics_wstd(5, 23, 1000.0, school_students)
    assert pd.to_numeric(result.loc["nstudents_SchoolA", "value"]) == 100
    assert pd.to_numeric(result.loc["nstudents_SchoolB", "value"]) == 200
    assert pd.to_numeric(result.loc["nstudents_all", "value"]) == 300


def test_summary_statistics_wstd_actual_hours_stored():
    result = summary_statistics_wstd(5, 23, 1000.0, {"SchoolA": 100})
    assert pd.to_numeric(result.loc["zstd_spsy_year_actual", "value"]) == pytest.approx(
        1000.0
    )


def test_summary_statistics_wstd_zero_wstd():
    """ratio_nstudents_wstd_spsy should be 0 when wstd_spsy=0 (no division by zero)."""
    result = summary_statistics_wstd(0, 23, 0.0, {"SchoolA": 100})
    assert pd.to_numeric(result.loc["ratio_nstudens_wstd_spsy", "value"]) == 0


def test_normal_distribution_plot_creates_file(tmp_path):
    from edupsyadmin.api.reports import normal_distribution_plot

    plot_path = tmp_path / "test_plot.png"
    normal_distribution_plot([0.0, 1.0, -1.0], plot_path)
    assert plot_path.exists()
    assert plot_path.stat().st_size > 0


def test_test_report_build_creates_pdf(tmp_path):
    """TestReport.build() should produce a non-empty PDF file."""
    from datetime import date

    from edupsyadmin.api.reports import (
        TestReport,
        TestReportData,
        normal_distribution_plot,
    )

    plot_path = tmp_path / "plot.png"
    normal_distribution_plot([0.0, 1.0], plot_path)

    data = TestReportData(
        heading="Test Heading",
        client_name_or_id="Test Client",
        grade=10,
        test_date=date(2024, 3, 1),
        birthday=date(2000, 5, 15),
        age_str="23 Jahre, 9 Monate",
        results=[
            "Section A",
            ("Label 1", "Value 1"),
            ("Label 2", "Value 2"),
            "Section B",
            ("Label 3", "Value 3"),
        ],
        plot_path=plot_path,
    )

    output_path = tmp_path / "test_report.pdf"
    TestReport(data).build(output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.dfi_imported", True)
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.dfi")
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.TaetigkeitsberichtReport")
def test_create_taetigkeitsbericht_report_calls_build(
    mock_report_cls,
    mock_dfi,
    tmp_path,
    summary_wstd_df,
    summary_categories_df,
    summary_h_sessions_df,
):
    output_file = str(tmp_path / "test_report")

    create_taetigkeitsbericht_report(
        output_file,
        "Test Name",
        summary_wstd_df,
        summary_categories_df,
        summary_h_sessions_df,
    )

    mock_dfi.export.assert_called()
    mock_report_instance = mock_report_cls.return_value
    mock_report_instance.build.assert_called_once_with(
        output_file + "_report.pdf",
        summary_wstd_img="resources/summary_wstd.png",
        summary_h_sessions_img="resources/summary_h_sessions.png",
        summary_categories=summary_categories_df,
    )


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.dfi_imported", False)
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.logger")
def test_create_taetigkeitsbericht_report_warns_without_dfi(
    mock_logger,
    summary_wstd_df,
):
    create_taetigkeitsbericht_report("out", "Name", summary_wstd_df)
    mock_logger.warning.assert_called_once()
    warning_message = mock_logger.warning.call_args[0][0]
    assert "dataframe_image" in warning_message


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.ClientsManager")
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.create_taetigkeitsbericht_report")
def test_taetigkeitsbericht_calls_create_report(
    mock_create_report,
    mock_clients_manager,
    mock_config,
    tmp_path,
):
    mock_manager_instance = mock_clients_manager.return_value
    mock_manager_instance.get_clients_overview.return_value = pd.DataFrame(
        {
            "school": ["FirstSchool", "FirstSchool", "SecondSchool"],
            "keyword_taet_encr": ["cat1", "cat2", "cat2"],
            "min_sessions": [300, 180, 132],
            "n_sessions": [4, 2, 1],
        }
    )

    output_basename = str(tmp_path / "Taetigkeitsbericht_Out")
    taetigkeitsbericht(
        database_url="url",
        wstd_psy=5,
        out_basename=output_basename,
    )

    mock_create_report.assert_called_once()
    # Verify the correct basename and name are passed through
    assert mock_create_report.call_args[0][0] == output_basename
    assert mock_create_report.call_args[0][1] == "Schulpsychologie"


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.ClientsManager")
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.create_taetigkeitsbericht_report")
def test_taetigkeitsbericht_writes_csv_files(
    mock_create_report,
    mock_clients_manager,
    mock_config,
    tmp_path,
):
    """taetigkeitsbericht() should write three CSV files regardless of PDF output."""
    mock_manager_instance = mock_clients_manager.return_value
    mock_manager_instance.get_clients_overview.return_value = pd.DataFrame(
        {
            "school": ["FirstSchool", "SecondSchool"],
            "keyword_taet_encr": ["cat1", "cat2"],
            "min_sessions": [300, 180],
            "n_sessions": [4, 2],
        }
    )

    output_basename = str(tmp_path / "Taetigkeitsbericht_Out")
    taetigkeitsbericht(database_url="url", wstd_psy=5, out_basename=output_basename)

    assert Path(output_basename + "_df.csv").exists()
    assert Path(output_basename + "_categories.csv").exists()
    assert Path(output_basename + "_h_sessions.csv").exists()
    assert Path(output_basename + "_wstd.csv").exists()
