from datetime import date
from typing import Any

import pytest

from edupsyadmin.api.managers import (
    ClientNotFoundError,
)

EXPECTED_KEYS = {
    "first_name_encr",
    "last_name_encr",
    "gender_encr",
    "birthday_encr",
    "street_encr",
    "city_encr",
    "parent_encr",
    "telephone1_encr",
    "telephone2_encr",
    "email_encr",
    "notes_encr",
    "client_id",
    "school",
    "entry_date",
    "class_name",
    "class_int",
    "estimated_graduation_date",
    "document_shredding_date",
    "keyword_taet_encr",
    "lrst_diagnosis_encr",
    "lrst_last_test_date_encr",
    "lrst_last_test_by_encr",
    "datetime_created",
    "datetime_lastmodified",
    "notenschutz",
    "nos_rs",
    "nos_rs_ausn",
    "nos_rs_ausn_faecher",
    "nos_les",
    "nos_other",
    "nachteilsausgleich",
    "nta_zeitv",
    "nta_zeitv_vieltext",
    "nta_zeitv_wenigtext",
    "nta_font",
    "nta_aufg",
    "nta_struktur",
    "nta_arbeitsm",
    "nta_ersgew",
    "nta_vorlesen",
    "nta_other",
    "nta_other_details",
    "nta_nos_notes",
    "nta_nos_end",
    "nta_nos_end_grade",
    "min_sessions",
    "n_sessions",
}


class TestManagers:
    def test_add_client(self, mock_keyring, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert EXPECTED_KEYS.issubset(client.keys())
        assert client["first_name_encr"] == client_dict_set_by_user["first_name_encr"]
        assert client["last_name_encr"] == client_dict_set_by_user["last_name_encr"]
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

    def test_add_client_set_id(self, mock_keyring, clients_manager):
        client_dict_with_id = {
            "client_id": 99,
            "school": "FirstSchool",
            "gender_encr": "f",
            "entry_date": date(2021, 6, 30),
            "class_name": "7TKKG",
            "first_name_encr": "Lieschen",
            "last_name_encr": "Müller",
            "birthday_encr": "1990-01-01",
        }
        client_id = clients_manager.add_client(**client_dict_with_id)
        assert client_id == 99

    def test_add_client_set_id_str(self, mock_keyring, clients_manager):
        client_dict_with_id = {
            "client_id": "98",
            "school": "FirstSchool",
            "gender_encr": "f",
            "entry_date": date(2021, 6, 30),
            "class_name": "7TKKG",
            "first_name_encr": "Lieschen",
            "last_name_encr": "Müller",
            "birthday_encr": "1990-01-01",
        }
        client_id = clients_manager.add_client(**client_dict_with_id)
        assert client_id == 98

    def test_edit_client(self, mock_keyring, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)
        client = clients_manager.get_decrypted_client(client_id=client_id)
        updated_data = {
            "first_name_encr": "Jane",
            "last_name_encr": "Smith",
            "nta_zeitv_vieltext": 25,
            "nta_font": True,
            "nta_nos_end_grade": 10,
        }
        clients_manager.edit_client([client_id], updated_data)
        upd_cl = clients_manager.get_decrypted_client(client_id)

        assert EXPECTED_KEYS.issubset(upd_cl.keys())
        assert upd_cl["first_name_encr"] == "Jane"
        assert upd_cl["last_name_encr"] == "Smith"

        assert upd_cl["nta_zeitv_vieltext"] == 25
        assert upd_cl["nta_font"] is True
        assert upd_cl["nta_zeitv"] is True
        assert upd_cl["nachteilsausgleich"] is True
        assert upd_cl["nta_nos_end_grade"] == 10
        assert upd_cl["nta_nos_end"] is True

        assert upd_cl["nta_ersgew"] is False

        assert upd_cl["datetime_lastmodified"] > client["datetime_lastmodified"]

        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

        # add another client
        another_client_dict = {
            "school": "SecondSchool",
            "gender_encr": "m",
            "entry_date": date(2020, 12, 24),
            "class_name": "5a",
            "first_name_encr": "Aam",
            "last_name_encr": "Admi",
            "birthday_encr": "1992-01-01",
            "street_encr": "Platzhalterplatz 1",
            "city_encr": "87534 Oberstaufen",
            "telephone1_encr": "0000 0000",
            "email_encr": "aam.admi@example.com",
        }
        another_client_id = clients_manager.add_client(**another_client_dict)

        # edit multiple clients
        clients_manager.edit_client(
            [client_id, another_client_id],
            {
                "nos_rs": "0",
                "nos_les": "1",
                "nta_font": True,
                "nta_zeitv_vieltext": "",
                "nta_zeitv_wenigtext": "",
                "lrst_diagnosis_encr": "iLst",
            },
        )
        upd_cl1_multiple = clients_manager.get_decrypted_client(client_id)
        upd_cl2_multiple = clients_manager.get_decrypted_client(another_client_id)

        assert (
            upd_cl1_multiple["first_name_encr"] != upd_cl2_multiple["first_name_encr"]
        )
        assert (
            upd_cl1_multiple["notenschutz"] == upd_cl2_multiple["notenschutz"] is True
        )
        assert upd_cl1_multiple["nos_rs"] == upd_cl2_multiple["nos_rs"] is False
        assert upd_cl1_multiple["nos_les"] == upd_cl2_multiple["nos_les"] is True
        assert upd_cl1_multiple["nta_zeitv"] == upd_cl2_multiple["nta_zeitv"] is False
        assert (
            upd_cl1_multiple["nta_zeitv_vieltext"]
            == upd_cl2_multiple["nta_zeitv_vieltext"]
            is None
        )
        assert (
            upd_cl1_multiple["lrst_diagnosis_encr"]
            == upd_cl2_multiple["lrst_diagnosis_encr"]
            == "iLst"
        )

    def test_delete_client(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)
        clients_manager.delete_client(client_id)
        with pytest.raises(ClientNotFoundError) as excinfo:
            clients_manager.get_decrypted_client(client_id)
        assert excinfo.value.client_id == client_id

    def test_edit_client_with_invalid_key(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        invalid_key = "this_key_does_not_exist"
        new_data = {"first_name_encr": "new_name", invalid_key: "some_value"}

        with pytest.raises(ValueError) as excinfo:
            clients_manager.edit_client([client_id], new_data)

        assert invalid_key in str(excinfo.value)

        # Check that the valid data was not updated
        updated_client = clients_manager.get_decrypted_client(client_id)
        assert updated_client["first_name_encr"] != "new_name"


class TestClientValidation:
    def test_validate_lrst_diagnosis(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid value
        clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": "lrst"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_diagnosis_encr"] == "lrst"

        # Invalid value
        with pytest.raises(ValueError, match="Invalid value for lrst_diagnosis"):
            clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": "invalid"})

        # Empty value
        clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_diagnosis_encr"] == ""

        # None value
        clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_diagnosis_encr"] == ""

    def test_validate_nos_rs_ausn_faecher(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # With value
        clients_manager.edit_client([client_id], {"nos_rs_ausn_faecher": "Deutsch"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher"] == "Deutsch"
        assert client["nos_rs_ausn"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nos_rs_ausn_faecher": " "})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher"] == " "
        assert client["nos_rs_ausn"] is False

        # With None
        clients_manager.edit_client([client_id], {"nos_rs_ausn_faecher": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher"] is None
        assert client["nos_rs_ausn"] is False

    def test_validate_nos_bool(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        clients_manager.edit_client(
            [client_id], {"nos_rs": False, "nos_les": False, "nos_other_details": ""}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs"] is False
        assert client["nos_les"] is False
        assert client["nos_other"] is False
        assert client["notenschutz"] is False

        # nos_rs
        clients_manager.edit_client([client_id], {"nos_rs": "1"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs"] is True
        assert client["notenschutz"] is True

        clients_manager.edit_client([client_id], {"nos_rs": False})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs"] is False
        assert client["notenschutz"] is False

        # nos_les
        clients_manager.edit_client([client_id], {"nos_les": True})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_les"] is True
        assert client["notenschutz"] is True

        clients_manager.edit_client([client_id], {"nos_les": 0})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_les"] is False
        assert client["notenschutz"] is False

        # invalid value
        with pytest.raises(ValueError, match="cannot be converted to a boolean"):
            clients_manager.edit_client([client_id], {"nos_rs": "abc"})

    def test_validate_nos_other_details(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        clients_manager.edit_client(
            [client_id], {"nos_rs": False, "nos_les": False, "nos_other_details": ""}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["notenschutz"] is False

        # With value
        clients_manager.edit_client([client_id], {"nos_other_details": "Some details"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_other_details"] == "Some details"
        assert client["nos_other"] is True
        assert client["notenschutz"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nos_other_details": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_other_details"] == ""
        assert client["nos_other"] is False
        assert client["notenschutz"] is False

    def test_validate_nta_zeitv_percentage(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # nta_zeitv_vieltext
        clients_manager.edit_client([client_id], {"nta_zeitv_vieltext": "25"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_zeitv_vieltext"] == 25
        assert client["nta_zeitv"] is True
        assert client["nachteilsausgleich"] is True

        clients_manager.edit_client([client_id], {"nta_zeitv_vieltext": 0})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_zeitv_vieltext"] == 0
        assert client["nta_zeitv"] is False
        assert client["nachteilsausgleich"] is False

        # nta_zeitv_wenigtext
        clients_manager.edit_client([client_id], {"nta_zeitv_wenigtext": 10})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_zeitv_wenigtext"] == 10
        assert client["nta_zeitv"] is True
        assert client["nachteilsausgleich"] is True

        clients_manager.edit_client([client_id], {"nta_zeitv_wenigtext": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_zeitv_wenigtext"] is None
        assert client["nta_zeitv"] is False
        assert client["nachteilsausgleich"] is False

    def test_validate_nta_bool(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        nta_bool_fields = [
            "nta_font",
            "nta_aufg",
            "nta_struktur",
            "nta_arbeitsm",
            "nta_ersgew",
            "nta_vorlesen",
        ]
        reset_data: dict[str, str | Any] = dict.fromkeys(nta_bool_fields, False)
        reset_data["nta_other_details"] = ""  # makes sure nta_other is False
        clients_manager.edit_client([client_id], reset_data)
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nachteilsausgleich"] is False

        for field in nta_bool_fields:
            # Test setting to True
            clients_manager.edit_client([client_id], {field: True})
            client = clients_manager.get_decrypted_client(client_id)
            assert client[field] is True
            assert client["nachteilsausgleich"] is True, (
                f"Setting {field} to True should set nachteilsausgleich to True!"
            )

            # Test setting back to False
            clients_manager.edit_client([client_id], {field: False})
            client = clients_manager.get_decrypted_client(client_id)
            assert client[field] is False
            assert client["nachteilsausgleich"] is False

    def test_validate_nta_other_details(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        nta_bool_fields = [
            "nta_font",
            "nta_aufg",
            "nta_struktur",
            "nta_arbeitsm",
            "nta_ersgew",
            "nta_vorlesen",
        ]
        reset_data: dict[str, str | Any] = dict.fromkeys(nta_bool_fields, False)
        reset_data["nta_other_details"] = ""  # makes sure nta_other is False
        clients_manager.edit_client([client_id], reset_data)
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nachteilsausgleich"] is False

        # With value
        clients_manager.edit_client([client_id], {"nta_other_details": "Some details"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_other_details"] == "Some details"
        assert client["nta_other"] is True
        assert client["nachteilsausgleich"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nta_other_details": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_other_details"] == ""
        assert client["nta_other"] is False
        assert client["nachteilsausgleich"] is False

    def test_validate_nta_nos_end_grade(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # With value
        clients_manager.edit_client([client_id], {"nta_nos_end_grade": "10"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_end_grade"] == 10
        assert client["nta_nos_end"] is True

        # With None
        clients_manager.edit_client([client_id], {"nta_nos_end_grade": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_end_grade"] is None
        assert client["nta_nos_end"] is False

    def test_validate_lrst_last_test_date_encr(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid date string
        clients_manager.edit_client(
            [client_id], {"lrst_last_test_date_encr": "2023-01-01"}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_last_test_date_encr"] == "2023-01-01"

        # date object
        test_date = date(2023, 2, 1)
        clients_manager.edit_client(
            [client_id], {"lrst_last_test_date_encr": test_date}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_last_test_date_encr"] == "2023-02-01"

        # Invalid date string
        with pytest.raises(ValueError, match="Invalid date format"):
            clients_manager.edit_client(
                [client_id], {"lrst_last_test_date_encr": "2023-13-01"}
            )

        # Empty string
        clients_manager.edit_client([client_id], {"lrst_last_test_date_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_last_test_date_encr"] == ""

    def test_validate_lrst_last_test_by_encr(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid value
        clients_manager.edit_client([client_id], {"lrst_last_test_by_encr": "schpsy"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_last_test_by_encr"] == "schpsy"

        # Invalid value
        with pytest.raises(
            ValueError, match="Invalid value for lrst_last_test_by_encr"
        ):
            clients_manager.edit_client(
                [client_id], {"lrst_last_test_by_encr": "invalid"}
            )

        # Required when lrst_diagnosis_encr is set
        clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": "lrst"})
        with pytest.raises(
            ValueError, match="is required when lrst_diagnosis_encr is set"
        ):
            clients_manager.edit_client([client_id], {"lrst_last_test_by_encr": ""})

        # Not required when lrst_diagnosis_encr is not set
        clients_manager.edit_client([client_id], {"lrst_diagnosis_encr": ""})
        clients_manager.edit_client([client_id], {"lrst_last_test_by_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["lrst_last_test_by_encr"] == ""

    def test_validate_birthday(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid date string
        clients_manager.edit_client([client_id], {"birthday_encr": "2000-01-01"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["birthday_encr"] == "2000-01-01"

        # date object
        test_date = date(2001, 2, 3)
        clients_manager.edit_client([client_id], {"birthday_encr": test_date})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["birthday_encr"] == "2001-02-03"

        # Invalid date string
        with pytest.raises(ValueError, match="does not match format"):
            clients_manager.edit_client([client_id], {"birthday_encr": "2000-20-20"})

    def test_validate_unencrypted_dates(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid date string
        clients_manager.edit_client([client_id], {"entry_date": "2022-01-01"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date"] == date(2022, 1, 1)

        # None
        clients_manager.edit_client([client_id], {"entry_date": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date"] is None

        # date object
        test_date = date(2022, 2, 1)
        clients_manager.edit_client([client_id], {"entry_date": test_date})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date"] == test_date

        # Empty string
        clients_manager.edit_client([client_id], {"entry_date": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date"] is None

        # Invalid date string
        with pytest.raises(ValueError):
            clients_manager.edit_client([client_id], {"entry_date": "invalid-date"})

    def test_validate_keyword_taet_encr(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # invalid keyword
        keyword = "some_invalid_keyword"
        with pytest.raises(ValueError, match="Invalid keyword"):
            clients_manager.edit_client([client_id], {"keyword_taet_encr": keyword})

        # valid keyword
        keyword = "lrst.sp.ern"
        clients_manager.edit_client([client_id], {"keyword_taet_encr": keyword})
        client = clients_manager.get_decrypted_client(client_id)
        assert "keyword_taet_encr" in client

        # Test with empty string
        clients_manager.edit_client([client_id], {"keyword_taet_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["keyword_taet_encr"] == ""

    def test_min_sessions(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        clients_manager.edit_client([client_id], {"min_sessions": 45})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["min_sessions"] == 45

        clients_manager.edit_client([client_id], {"min_sessions": "120"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["min_sessions"] == 120

    def test_nta_nos_notes(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        notes = "Some notes about NTA/NOS"
        clients_manager.edit_client([client_id], {"nta_nos_notes": notes})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_notes"] == notes

        clients_manager.edit_client([client_id], {"nta_nos_notes": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_notes"] is None

    def test_gender_conversion(self, clients_manager, client_dict_set_by_user):
        client_w = client_dict_set_by_user.copy()
        del client_w["client_id"]
        client_w["gender_encr"] = "w"
        client_w_id = clients_manager.add_client(**client_w)
        decrypted_w = clients_manager.get_decrypted_client(client_w_id)
        assert decrypted_w["gender_encr"] == "f"

        client_d = client_dict_set_by_user.copy()
        del client_d["client_id"]
        client_d["gender_encr"] = "d"
        client_d_id = clients_manager.add_client(**client_d)
        decrypted_d = clients_manager.get_decrypted_client(client_d_id)
        assert decrypted_d["gender_encr"] == "x"

        client_m = client_dict_set_by_user.copy()
        del client_m["client_id"]
        client_m["gender_encr"] = "m"
        client_m_id = clients_manager.add_client(**client_m)
        decrypted_m = clients_manager.get_decrypted_client(client_m_id)
        assert decrypted_m["gender_encr"] == "m"

    def test_class_name_parsing(self, clients_manager, client_dict_set_by_user):
        client_data = client_dict_set_by_user.copy()
        del client_data["client_id"]
        client_data["class_name"] = "10a"
        client_id = clients_manager.add_client(**client_data)
        client = clients_manager.get_decrypted_client(client_id)
        assert client["class_int"] == 10
        assert client["estimated_graduation_date"] is not None
        assert client["document_shredding_date"] is not None

        # Test with no number in class_name
        # FIXME: Raise an error because it containes no integer
        # TODO: write a validates method for the db model and a validator for the tui
        client_data["class_name"] = "Vorklasse"
        client_id_2 = clients_manager.add_client(**client_data)
        client2 = clients_manager.get_decrypted_client(client_id_2)
        assert client2["class_int"] is None
        assert client2["estimated_graduation_date"] is None
        assert client2["document_shredding_date"] is None


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
