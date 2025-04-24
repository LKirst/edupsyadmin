from datetime import date
from unittest.mock import patch

from edupsyadmin.api.add_convenience_data import add_convenience_data

# Sample input data
input_data = {
    "first_name": "John",
    "last_name": "Doe",
    "street": "456 Example Rd",
    "city": "Example City",
    "school": "FirstSchool",
    "nachteilsausgleich": True,
    "notenschutz": True,
    "birthday": "2000-01-01",
    "nta_zeitv_vieltext": 25,
    "document_shredding_date": date(2025, 12, 24),
    "lrst_diagnosis": "lrst",
}


@patch(
    "edupsyadmin.api.add_convenience_data.get_subjects"
)  # Mock the get_subjects function
def test_add_convenience_data(mock_get_subjects, mock_config):
    # Mock the return value of get_subjects
    mock_get_subjects.return_value = "Math, Science, History"

    # Call the function with input data
    result = add_convenience_data(input_data)

    # Assertions
    assert result["name"] == "John Doe"
    assert result["addr_s_nname"] == "456 Example Rd, Example City"
    assert result["addr_m_wname"] == "John Doe\n456 Example Rd\nExample City"
    assert result["school_name"] == "Berufsfachschule Kinderpflege"
    assert result["school_street"] == "Beispielstr. 1"
    assert (
        result["school_addr_s_wname"]
        == "Berufsfachschule Kinderpflege, Beispielstr. 1, 87700 Beispielstadt"
    )
    assert result["school_head_w_school"] == "Außenstellenleitung der Berufsfachschule"
    assert result["school_subjects"] == "Math, Science, History"
    assert result["lrst_diagnosis_long"] == "Lese-Rechtschreib-Störung"
    assert (
        result["schoolpsy_addr_m_wname"]
        == "Firstname Lastname\nBeispielstr. 1\n87700 Beispielstadt"
    )
    # Check dates
    assert result["date_today_de"] is not None  # Check if date is added
    assert result["birthday_de"] == "01.01.2000"
    assert result["document_shredding_date_de"] == "24.12.2025"
    # Verify that the school subjects were fetched
    mock_get_subjects.assert_called_once_with("FirstSchool")
