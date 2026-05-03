from datetime import date
from unittest.mock import patch

from edupsyadmin.api.cft_report import create_report


def test_cft_report_snapshot(pdf_snapshot, clients_manager, tmp_path):
    """Standard report with all values provided."""
    client_data = {
        "first_name_encr": "Max",
        "last_name_encr": "Mustermann",
        "birthday_encr": date(2010, 5, 15),
        "class_name_encr": "8",
        "school": "FirstSchool",
        "gender_encr": "m",
    }
    client_id = clients_manager.add_client(**client_data)

    test_date = "2026-04-18"

    inputs = [
        "15",  # raw_part1_min
        "18",  # raw_part1_max
        "25",  # raw_part2
        "100",  # iq_part1_min
        "110",  # iq_part1_max
        "105",  # iq_part2
        "102",  # iq_total_min
        "108",  # iq_total_max
    ]

    with patch("builtins.input", side_effect=inputs):
        create_report(
            database_url=clients_manager.database_url,
            client_id=client_id,
            test_date=test_date,
            directory=tmp_path,
        )

    report_path = tmp_path / f"{client_id}_Auswertung.pdf"
    assert report_path.exists()
    assert pdf_snapshot == report_path


def test_cft_report_min_none_snapshot(pdf_snapshot, clients_manager, tmp_path):
    """Report where minimum values are None."""
    client_data = {
        "first_name_encr": "Erika",
        "last_name_encr": "Mustermann",
        "birthday_encr": date(2012, 8, 20),
        "class_name_encr": "6",
        "school": "SecondSchool",
        "gender_encr": "f",
    }
    client_id = clients_manager.add_client(**client_data)

    test_date = "2026-04-18"

    inputs = [
        "",  # raw_part1_min -> None
        "18",  # raw_part1_max
        "25",  # raw_part2
        "",  # iq_part1_min -> None
        "110",  # iq_part1_max
        "105",  # iq_part2
        "",  # iq_total_min -> None
        "108",  # iq_total_max
    ]

    with patch("builtins.input", side_effect=inputs):
        create_report(
            database_url=clients_manager.database_url,
            client_id=client_id,
            test_date=test_date,
            directory=tmp_path,
        )

    report_path = tmp_path / f"{client_id}_Auswertung.pdf"
    assert report_path.exists()
    assert pdf_snapshot == report_path


def test_cft_report_max_none_snapshot(pdf_snapshot, clients_manager, tmp_path):
    """Report where maximum values are None."""
    client_data = {
        "first_name_encr": "Hans",
        "last_name_encr": "Beispiel",
        "birthday_encr": date(2011, 3, 10),
        "class_name_encr": "7",
        "school": "FirstSchool",
        "gender_encr": "m",
    }
    client_id = clients_manager.add_client(**client_data)

    test_date = "2026-04-18"

    inputs = [
        "15",  # raw_part1_min
        "",  # raw_part1_max -> None
        "25",  # raw_part2
        "100",  # iq_part1_min
        "",  # iq_part1_max -> None
        "105",  # iq_part2
        "102",  # iq_total_min
        "",  # iq_total_max -> None
    ]

    with patch("builtins.input", side_effect=inputs):
        create_report(
            database_url=clients_manager.database_url,
            client_id=client_id,
            test_date=test_date,
            directory=tmp_path,
        )

    report_path = tmp_path / f"{client_id}_Auswertung.pdf"
    assert report_path.exists()
    assert pdf_snapshot == report_path
