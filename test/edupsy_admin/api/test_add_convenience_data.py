from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from edupsy_admin.api.add_convenience_data import add_convenience_data
from edupsy_admin.core.config import config

# Sample input data
input_data = {
    "first_name": "John",
    "last_name": "Doe",
    "street": "456 Example Rd",
    "city": "Example City",
    "school": "test_school",
    "nachteilsausgleich": True,
    "notenschutz": True,
    "birthday": "2000-01-01",
    "document_shredding_date": datetime.now(),
    "nta_sprachen": 50,
}


@pytest.fixture
def mock_config():
    # TODO: replace with tmp_path
    cfg_paths = [Path(__file__).parent.parent.parent / "data" / "sampleconfig.yml"]
    config.load(cfg_paths)


@patch(
    "edupsy_admin.api.add_convenience_data.get_subjects"
)  # Mock the get_subjects function
def test_add_convenience_data(mock_get_subjects, mock_config):
    # Mock the return value of get_subjects
    mock_get_subjects.return_value = "Math, Science, History"

    # Call the function with input data
    result = add_convenience_data(input_data)

    # Assertions
    # TODO: Handle Umlaute in the config.yaml!
    assert result["name"] == "John Doe"
    assert result["address"] == "456 Example Rd, Example City"
    assert result["address_multiline"] == "John Doe\n456 Example Rd\nExample City"
    assert result["school_name"] == "Test School"
    assert result["school_street"] == "123 Test St"
    assert result["school_head_w_school"] == "Principal of Test School"
    assert result["ns_subjects"] == "Math, Science, History"
    assert (
        result["ns_zeugnisbemerkung"]
        == "Auf die Bewertung der Rechtschreibleistung wurde verzichtet."
    )
    assert (
        result["ns_measures"] == "Verzicht auf die Bewertung der Rechtschreibleistung"
    )
    assert result["na_subjects"] == "Math, Science, History"
    assert result["na_measures"] == (
        "Verlängerung der Arbeitszeit um 50% bei schriftlichen "
        "Leistungsnachweisen und der Vorbereitungszeit bei "
        "mündlichen Leistungsnachweisen"
    )
    assert result["date_today_de"] is not None  # Check if date is added
    assert (
        result["birthday_de"] == "01.01.2000"
    )  # Check if birthday is parsed correctly
    # Verify that the school subjects were fetched
    mock_get_subjects.assert_called_once_with("test_school")
