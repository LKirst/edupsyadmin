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


def test_get_subcategories():
    assert get_subcategories("category.sub") == ["category.sub", "category"]
    assert get_subcategories("category") == ["category"]
    assert get_subcategories("category.sub.sub2") == [
        "category.sub.sub2",
        "category.sub",
        "category",
    ]


def test_add_categories_to_df():
    df = pd.DataFrame(
        {
            "category": ["cat1", "cat2.sub", "cat2"],
            "h_sessions": [5.3, 1.0, 2.5],
            "n_sessions": [4, 1, 2],  # Represents >3, 1, and 2-3 sessions respectively
        }
    )

    df, summary = add_categories_to_df(df, "category")

    assert "cat1" in df.columns
    assert "cat2" in df.columns
    assert "cat2.sub" in df.columns

    assert summary.loc["sum", "cat1"] == 5.3
    assert summary.loc["sum", "cat2"] == pytest.approx(3.5)

    # The row 'cat1' had 4 sessions (>3)
    assert summary.loc["count_mt3_sessions", "cat1"] == 1
    assert summary.loc["count_2to3_sessions", "cat1"] == 0
    assert summary.loc["count_1_session", "cat1"] == 0

    # The row 'cat2.sub' had 1 session
    assert summary.loc["count_mt3_sessions", "cat2.sub"] == 0
    assert summary.loc["count_2to3_sessions", "cat2.sub"] == 0
    assert summary.loc["count_1_session", "cat2.sub"] == 1

    # Check the parent category 'cat2', which aggregates counts from itself
    # and its children
    assert summary.loc["count_mt3_sessions", "cat2"] == 0
    assert summary.loc["count_2to3_sessions", "cat2"] == 1  # From the 'cat2' entry
    assert summary.loc["count_1_session", "cat2"] == 1  # From the 'cat2.sub' entry


def test_summary_statistics_h_sessions():
    df = pd.DataFrame(
        {"school": ["school1", "school2", "school1"], "h_sessions": [5.2, 2, 3]}
    )
    result = summary_statistics_h_sessions(df)
    assert result.loc["school1", "sum"] == 8.2
    assert result.loc["school2", "sum"] == 2
    assert result.loc["all", "sum"] == 10.2


def test_wstd_in_zstd():
    result = wstd_in_zstd(5)
    assert result.loc["wstd_spsy", "value"] == 5
    assert result.loc["zstd_spsy_week_target", "value"] > 0


def test_summary_statistics_wstd():
    school_students = {"SchoolA": 100, "SchoolB": 200}
    result = summary_statistics_wstd(5, 23, 1000.0, school_students)

    assert result.loc["nstudents_SchoolA", "value"] == 100
    assert result.loc["nstudents_SchoolB", "value"] == 200
    assert result.loc["nstudents_all", "value"] == 300


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.dfi.export")
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.Report")
def test_create_taetigkeitsbericht_report(mock_report, mock_dfi_export, tmp_path):
    summary_wstd = pd.DataFrame(
        {"value": [5, 251, 50]},
        index=["wstd_spsy", "wd_year", "zstd_week"],
    )

    summary_categories = pd.DataFrame(
        {"cat1": [5, 1, 1, 0], "cat2.sub": [3, 0, 1, 1]},
        index=[
            "sum",
            "count_mt3_sessions",
            "count_2to3_sessions",
            "count_1_session",
        ],
    )

    summary_h_sessions = pd.DataFrame(
        {
            "count": [2, 1, 3],
            "mean": [4.0, 2.0, 3.333],
            "sum": [8, 2, 10],
        },
        index=["school1", "school2", "all"],
    )

    output_file = tmp_path / "test_report"

    create_taetigkeitsbericht_report(
        str(output_file),
        "Test Name",
        summary_wstd,
        summary_categories,
        summary_h_sessions,
    )

    mock_dfi_export.assert_called()
    mock_report_instance = mock_report.return_value
    mock_report_instance.output.assert_called_with(str(output_file) + "_report.pdf")


@patch("edupsyadmin.api.taetigkeitsbericht_from_db.ClientsManager")
@patch("edupsyadmin.api.taetigkeitsbericht_from_db.create_taetigkeitsbericht_report")
def test_taetigkeitsbericht(
    mock_create_report, mock_clients_manager, mock_config, tmp_path
):
    mock_manager_instance = mock_clients_manager.return_value
    mock_manager_instance.get_data_raw.return_value = pd.DataFrame(
        {
            "school": ["FirstSchool", "FirstSchool", "SecondSchool"],
            "keyword_taet_encr": ["cat1", "cat2", "cat2"],
            "min_sessions": [300, 180, 132],
            "n_sessions": [4, 2, 1],
        }
    )

    output_basename = tmp_path / "Taetigkeitsbericht_Out"

    taetigkeitsbericht(
        database_url="url",
        wstd_psy=5,
        out_basename=str(output_basename),
    )

    mock_create_report.assert_called()
