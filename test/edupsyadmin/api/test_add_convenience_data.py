from datetime import datetime
from unittest.mock import patch

import pytest

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.utils.academic_year import get_this_academic_year_string


def _is_valid_german_date(date_str: str | None) -> bool:
    if date_str is None or date_str == "":
        return date_str == ""
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return True
    except ValueError:
        return False


@patch(
    "edupsyadmin.api.add_convenience_data._get_subjects"
)  # Mock the get_subjects function
def test_add_convenience_data(mock_get_subjects, mock_config, client_dict_internal):
    # Mock the return value of get_subjects
    mock_get_subjects.return_value = "Math, Science, History"

    result = add_convenience_data(client_dict_internal)

    # client data
    assert (
        result["name"]
        == client_dict_internal["first_name_encr"]
        + " "
        + client_dict_internal["last_name_encr"]
    )
    assert (
        result["addr_s_nname"]
        == client_dict_internal["street_encr"]
        + ", "
        + client_dict_internal["city_encr"]
    )
    assert result["addr_m_wname"] == (
        result["name"]
        + "\n"
        + client_dict_internal["street_encr"]
        + "\n"
        + client_dict_internal["city_encr"]
    )

    # school data
    is_1st_school = client_dict_internal["school"] == "FirstSchool"
    assert (
        result["school_name"] == "Berufsfachschule Kinderpflege"
        if is_1st_school
        else "Fachoberschule"
    )
    assert (
        result["school_street"] == "Beispielstr. 1"
        if is_1st_school
        else "Platzhalterweg 2"
    )
    if is_1st_school:
        assert (
            result["school_addr_s_wname"]
            == "Berufsfachschule Kinderpflege, Beispielstr. 1, 87700 Beispielstadt"
        )
        assert (
            result["school_head_w_school"] == "Außenstellenleitung der Berufsfachschule"
        )
    assert result["school_subjects"] == "Math, Science, History"

    diagnosis = result.get("lrst_diagnosis_encr")
    if diagnosis == "lrst":
        assert result["lrst_diagnosis_long"] == "Lese-Rechtschreib-Störung"
    elif diagnosis == "iLst":
        assert result["lrst_diagnosis_long"] == "isolierte Lesestörung"
    elif diagnosis == "iRst":
        assert result["lrst_diagnosis_long"] == "isolierte Rechtschreibstörung"

    assert (
        result["schoolpsy_addr_m_wname"]
        == "Firstname Lastname\nBeispielstr. 1\n87700 Beispielstadt"
    )

    # Check dates
    dates = [
        "birthday_encr",
        "today_date",
        "lrst_last_test_date_encr",
        "document_shredding_date",
    ]
    for d in dates:
        assert _is_valid_german_date(result[d + "_de"])

    # Verify that the school subjects were fetched
    mock_get_subjects.assert_called_once_with(client_dict_internal["school"])

    # Check school_year
    assert result["school_year"] == get_this_academic_year_string()

    # Check nta_nos_end_schoolyear
    if client_dict_internal.get("nta_nos_end"):
        assert result["nta_nos_end_schoolyear"] == get_this_academic_year_string()
    else:
        assert "nta_nos_end_schoolyear" not in result

    # Check lrst_schpsy
    if client_dict_internal.get("lrst_last_test_by_encr") == "schpsy":
        assert result["lrst_schpsy"] == 1
    elif not client_dict_internal.get("lrst_last_test_by_encr"):
        assert "lrst_schpsy" not in result


@patch("edupsyadmin.api.add_convenience_data._get_subjects")
def test_add_convenience_data_invalid_lrst_diagnosis(mock_get_subjects, mock_config):
    mock_get_subjects.return_value = "Math"
    client_data = {"lrst_diagnosis_encr": "invalid_diagnosis", "school": "FirstSchool"}
    with pytest.raises(ValueError, match="lrst_diagnosis can be only one of"):
        add_convenience_data(client_data)


@patch("edupsyadmin.api.add_convenience_data._get_subjects")
def test_add_convenience_data_missing_address_parts(mock_get_subjects, mock_config):
    mock_get_subjects.return_value = "Math"
    client_data = {
        "first_name_encr": "John",
        "last_name_encr": "Doe",
        "school": "FirstSchool",
    }
    result = add_convenience_data(client_data)
    assert "addr_s_nname" not in result
    assert "addr_m_wname" not in result


@patch("edupsyadmin.api.add_convenience_data.logger.error")
@patch("edupsyadmin.api.add_convenience_data._get_subjects")
def test_add_convenience_data_invalid_lrst_test_by(
    mock_get_subjects, mock_logger_error, mock_config
):
    mock_get_subjects.return_value = "Math"
    client_data = {"lrst_last_test_by_encr": "invalid_tester", "school": "FirstSchool"}
    result = add_convenience_data(client_data)
    assert "lrst_schpsy" not in result
    mock_logger_error.assert_called_once()
