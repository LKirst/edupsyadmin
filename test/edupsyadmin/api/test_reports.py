from datetime import date

import pandas as pd

from edupsyadmin.api.reports import (
    TaetigkeitsberichtReport,
    TestReport,
    TestReportData,
    normal_distribution_plot,
)


def test_normal_distribution_plot_creates_file(tmp_path):
    plot_path = tmp_path / "test_plot.png"
    normal_distribution_plot([0.0, 1.0, -1.0], plot_path)
    assert plot_path.exists()
    assert plot_path.stat().st_size > 0


def test_test_report_build_creates_pdf(tmp_path):
    """TestReport.build() should produce a non-empty PDF file."""
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


def test_taetigkeitsbericht_report_snapshot(pdf_snapshot, tmp_path):
    """Snapshot test for TaetigkeitsberichtReport.build()."""
    summary_wstd = pd.DataFrame(
        {"value": [5, 251, 50], "description": ["desc1", "desc2", "desc3"]},
        index=["wstd_spsy", "wd_year", "zstd_week"],
    )
    summary_h_sessions = pd.DataFrame(
        {
            "count": [2, 1, 3],
            "mean": [4.0, 2.0, 3.333],
            "sum": [8.0, 2.0, 10.0],
        },
        index=["school1", "school2", "all"],
    )
    summary_categories = pd.DataFrame(
        {"cat1": [5, 1, 1, 0]},
        index=[
            "sum",
            "count_mt3_sessions",
            "count_2to3_sessions",
            "count_1_session",
        ],
    )

    output_path = tmp_path / "taetigkeitsbericht_report.pdf"
    report = TaetigkeitsberichtReport(
        name="Test Psychologist", report_date=date(2025, 10, 16)
    )
    report.build(
        output_path,
        summary_wstd=summary_wstd,
        summary_h_sessions=summary_h_sessions,
        summary_categories=summary_categories,
    )

    assert output_path.exists()
    assert pdf_snapshot == output_path
