from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from edupsyadmin.api.lgvt import mk_report
from edupsyadmin.core.config import config


@pytest.fixture
def mock_lgvt_csv(tmp_path):
    """Create a mock CSV for LGVT tests."""
    df = pd.DataFrame(
        {
            "RichtigeAntwort": ["The", "quick", "brown", "fox", "jumps"],
            "Wortzahl": [20, 63, 80, 102, 145],
        },
    )
    csv_path = tmp_path / "mock_lgvt.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_lgvt_report_grade_11_snapshot(
    pdf_snapshot,
    clients_manager,
    tmp_path,
    mock_lgvt_csv,
    monkeypatch,
):
    """Snapshot test for LGVT report (Grade 11+)."""
    # Configure mock CSV path in global config
    monkeypatch.setattr(config.instance.lgvtcsv, "Rosenkohl", str(mock_lgvt_csv))

    # Add a stable client
    client_data = {
        "first_name_encr": "Max",
        "last_name_encr": "Mustermann",
        "birthday_encr": date(2008, 5, 15),
        "class_name_encr": "11",
        "school": "FirstSchool",
        "gender_encr": "m",
    }
    client_id = clients_manager.add_client(**client_data)

    test_date = "2026-04-18"

    inputs = [
        "y",  # item 1
        "n",  # item 2
        "y",  # item 3
        "q",  # item 4 is quit, so 3 items processed
        "5",  # words_after_last_item
        "50",  # lv_pr_korr
        "60",  # lgs_pr_korr
        "70",  # lg_pr
    ]

    with patch("builtins.input", side_effect=inputs):
        mk_report(
            database_url=clients_manager.database_url,
            client_id=client_id,
            test_date=test_date,
            version="Rosenkohl",
            directory=tmp_path,
        )

    report_path = tmp_path / f"{client_id}_Auswertung_LGVT.pdf"
    assert report_path.exists()
    assert pdf_snapshot == report_path


def test_lgvt_report_grade_9_snapshot(
    pdf_snapshot,
    clients_manager,
    tmp_path,
    mock_lgvt_csv,
    monkeypatch,
):
    """Snapshot test for LGVT report (Grade < 11)."""
    # Configure mock CSV path in global config
    monkeypatch.setattr(config.instance.lgvtcsv, "Rosenkohl", str(mock_lgvt_csv))

    # Add a stable client
    client_data = {
        "first_name_encr": "Erika",
        "last_name_encr": "Mustermann",
        "birthday_encr": date(2011, 8, 20),
        "class_name_encr": "9",
        "school": "SecondSchool",
        "gender_encr": "f",
    }
    client_id = clients_manager.add_client(**client_data)

    test_date = "2026-04-18"

    inputs = [
        "y",  # item 1
        "y",  # item 2
        "y",  # item 3
        "n",  # item 4
        "q",  # item 5 is quit, so 4 items processed
        "1",  # words_after_last_item
        "0.9",  # lv_korr_faktor
        "40",  # lv_pr_floor
        "45",  # lv_pr_ceil
        "0.85",  # lgs_korr_faktor
        "55",  # lgs_pr_korr
        "65",  # lg_pr
    ]

    with patch("builtins.input", side_effect=inputs):
        mk_report(
            database_url=clients_manager.database_url,
            client_id=client_id,
            test_date=test_date,
            version="Rosenkohl",
            directory=tmp_path,
        )

    report_path = tmp_path / f"{client_id}_Auswertung_LGVT.pdf"
    assert report_path.exists()
    assert pdf_snapshot == report_path
