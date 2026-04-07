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
    "entry_date_encr",
    "class_name_encr",
    "class_int_encr",
    "estimated_graduation_date_encr",
    "document_shredding_date_encr",
    "keyword_taet_encr",
    "lrst_diagnosis_encr",
    "lrst_last_test_date_encr",
    "lrst_last_test_by_encr",
    "datetime_created",
    "datetime_lastmodified",
    "notenschutz",
    "nos_rs",
    "nos_rs_ausn",
    "nos_rs_ausn_faecher_encr",
    "nos_les",
    "nos_other",
    "nos_other_details_encr",
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
    "nta_other_details_encr",
    "nta_nos_notes_encr",
    "nta_nos_end",
    "nta_nos_end_grade",
    "min_sessions",
    "n_sessions",
}


class TestManagers:
    def test_add_client(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert EXPECTED_KEYS.issubset(client.keys())
        assert client["first_name_encr"] == client_dict_set_by_user["first_name_encr"]
        assert client["last_name_encr"] == client_dict_set_by_user["last_name_encr"]

    def test_add_client_set_id(self, clients_manager):
        client_dict_with_id = {
            "client_id": 99,
            "school": "FirstSchool",
            "gender_encr": "f",
            "entry_date_encr": date(2021, 6, 30),
            "class_name_encr": "7TKKG",
            "first_name_encr": "Lieschen",
            "last_name_encr": "Müller",
            "birthday_encr": date(1990, 1, 1),
        }
        client_id = clients_manager.add_client(**client_dict_with_id)
        assert client_id == 99

    def test_add_client_set_id_str(self, clients_manager):
        client_dict_with_id = {
            "client_id": "98",
            "school": "FirstSchool",
            "gender_encr": "f",
            "entry_date_encr": date(2021, 6, 30),
            "class_name_encr": "7TKKG",
            "first_name_encr": "Lieschen",
            "last_name_encr": "Müller",
            "birthday_encr": date(1990, 1, 1),
        }
        client_id = clients_manager.add_client(**client_dict_with_id)
        assert client_id == 98

    def test_edit_client(self, clients_manager, client_dict_set_by_user):
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

        # add another client
        another_client_dict = {
            "school": "SecondSchool",
            "gender_encr": "m",
            "entry_date_encr": date(2020, 12, 24),
            "class_name_encr": "5a",
            "first_name_encr": "Aam",
            "last_name_encr": "Admi",
            "birthday_encr": date(1992, 1, 1),
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

    def test_get_total_count(self, clients_manager, client_dict_set_by_user):
        initial_count = clients_manager.get_total_count()
        clients_manager.add_client(**client_dict_set_by_user)
        assert clients_manager.get_total_count() == initial_count + 1

    def test_get_decrypted_client_not_found(self, clients_manager):
        with pytest.raises(ClientNotFoundError):
            clients_manager.get_decrypted_client(999)

    def test_get_clients_overview(self, clients_manager):
        # Add a few clients
        c1_id = clients_manager.add_client(
            school="FirstSchool",
            gender_encr="m",
            first_name_encr="A",
            last_name_encr="Alpha",
            birthday_encr="2010-01-01",
            class_name_encr="1a",
            nos_rs=True,
        )
        c2_id = clients_manager.add_client(
            school="SecondSchool",
            gender_encr="f",
            first_name_encr="B",
            last_name_encr="Beta",
            birthday_encr="2011-01-01",
            class_name_encr="2b",
            nta_zeitv_vieltext=25,
        )
        clients_manager.add_client(
            school="FirstSchool",
            gender_encr="x",
            first_name_encr="C",
            last_name_encr="Gamma",
            birthday_encr="2012-01-01",
            class_name_encr="3c",
        )

        # 1. Default overview
        df = clients_manager.get_clients_overview()
        assert len(df) == 3
        expected_base = {
            "client_id",
            "case_active",
            "school",
            "last_name_encr",
            "first_name_encr",
            "class_name_encr",
        }
        assert expected_base.issubset(df.columns)

        # 2. Filter by school
        df_school = clients_manager.get_clients_overview(schools=["FirstSchool"])
        assert len(df_school) == 2
        assert all(df_school["school"] == "FirstSchool")

        # 3. Filter by nta_nos
        df_nta_nos = clients_manager.get_clients_overview(nta_nos=True)
        assert len(df_nta_nos) == 2  # A (nos_rs) and B (nta_zeitv)
        assert set(df_nta_nos["client_id"]) == {c1_id, c2_id}

        # 4. Custom columns
        df_cols = clients_manager.get_clients_overview(
            columns=["birthday_encr", "city_encr"]
        )
        assert "birthday_encr" in df_cols.columns
        assert "city_encr" in df_cols.columns
        assert (
            "first_name_encr" in df_cols.columns
        )  # should still be there as it's required

        # 5. columns="all"
        df_all = clients_manager.get_clients_overview(columns="all")
        assert len(df_all.columns) >= len(EXPECTED_KEYS)

        # 6. Invalid columns
        with pytest.raises(ValueError, match="Invalid column names"):
            clients_manager.get_clients_overview(columns=["non_existent_column"])

        # 7. Single column as string
        df_single = clients_manager.get_clients_overview(columns="birthday_encr")
        assert "birthday_encr" in df_single.columns
        assert "first_name_encr" in df_single.columns

    def test_edit_client_partial_not_found(
        self, clients_manager, client_dict_set_by_user
    ):
        c1_id = clients_manager.add_client(**client_dict_set_by_user)

        from unittest.mock import patch

        from edupsyadmin.core.logger import logger as app_logger

        with patch.object(app_logger, "warning") as mock_warning:
            # Edit one existing and one non-existing ID
            clients_manager.edit_client(
                [c1_id, 999], {"first_name_encr": "UpdatedName"}
            )

            # Check if warning was called with expected message
            called_with_999 = any(
                "{999}" in str(call.args[0]) for call in mock_warning.call_args_list
            )
            assert called_with_999

        # Verify c1 was updated
        updated_c1 = clients_manager.get_decrypted_client(c1_id)
        assert updated_c1["first_name_encr"] == "UpdatedName"


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

    def test_validate_nos_rs_ausn_faecher_encr(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # With value
        clients_manager.edit_client(
            [client_id], {"nos_rs_ausn_faecher_encr": "Deutsch"}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher_encr"] == "Deutsch"
        assert client["nos_rs_ausn"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nos_rs_ausn_faecher_encr": " "})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher_encr"] == " "
        assert client["nos_rs_ausn"] is False

        # With None
        clients_manager.edit_client([client_id], {"nos_rs_ausn_faecher_encr": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_rs_ausn_faecher_encr"] == ""
        assert client["nos_rs_ausn"] is False

    def test_validate_nos_bool(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        clients_manager.edit_client(
            [client_id],
            {"nos_rs": False, "nos_les": False, "nos_other_details_encr": ""},
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

    def test_validate_nos_other_details_encr(
        self, clients_manager, client_dict_set_by_user
    ):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Ensure all are false initially
        clients_manager.edit_client(
            [client_id],
            {"nos_rs": False, "nos_les": False, "nos_other_details_encr": ""},
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["notenschutz"] is False

        # With value
        clients_manager.edit_client(
            [client_id], {"nos_other_details_encr": "Some details"}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_other_details_encr"] == "Some details"
        assert client["nos_other"] is True
        assert client["notenschutz"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nos_other_details_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nos_other_details_encr"] == ""
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
        reset_data["nta_other_details_encr"] = ""  # makes sure nta_other is False
        reset_data["nta_zeitv_vieltext"] = None
        reset_data["nta_zeitv_wenigtext"] = None
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

    def test_validate_nta_other_details_encr(
        self, clients_manager, client_dict_set_by_user
    ):
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
        reset_data["nta_other_details_encr"] = ""  # makes sure nta_other is False
        reset_data["nta_zeitv_vieltext"] = None
        reset_data["nta_zeitv_wenigtext"] = None
        clients_manager.edit_client([client_id], reset_data)
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nachteilsausgleich"] is False

        # With value
        clients_manager.edit_client(
            [client_id], {"nta_other_details_encr": "Some details"}
        )
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_other_details_encr"] == "Some details"
        assert client["nta_other"] is True
        assert client["nachteilsausgleich"] is True

        # With empty value
        clients_manager.edit_client([client_id], {"nta_other_details_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_other_details_encr"] == ""
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

    def test_validate_birthday(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid date string
        clients_manager.edit_client([client_id], {"birthday_encr": "2000-01-01"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["birthday_encr"] == date(2000, 1, 1)

        # date object
        test_date = date(2001, 2, 3)
        clients_manager.edit_client([client_id], {"birthday_encr": test_date})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["birthday_encr"] == test_date

        # Invalid date string
        with pytest.raises(
            ValueError, match=r"Invalid date format for '2000-20-20'. Use YYYY-MM-DD."
        ):
            clients_manager.edit_client([client_id], {"birthday_encr": "2000-20-20"})

    def test_validate_unencrypted_dates(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        # Valid date string
        clients_manager.edit_client([client_id], {"entry_date_encr": "2022-01-01"})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date_encr"] == date(2022, 1, 1)

        # None
        clients_manager.edit_client([client_id], {"entry_date_encr": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date_encr"] is None

        # date object
        test_date = date(2022, 2, 1)
        clients_manager.edit_client([client_id], {"entry_date_encr": test_date})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date_encr"] == test_date

        # Empty string
        clients_manager.edit_client([client_id], {"entry_date_encr": ""})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["entry_date_encr"] is None

        # Invalid date string
        with pytest.raises(ValueError):
            clients_manager.edit_client(
                [client_id], {"entry_date_encr": "invalid-date"}
            )

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

    def test_nta_nos_notes_encr(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)

        notes = "Some notes about NTA/NOS"
        clients_manager.edit_client([client_id], {"nta_nos_notes_encr": notes})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_notes_encr"] == notes

        clients_manager.edit_client([client_id], {"nta_nos_notes_encr": None})
        client = clients_manager.get_decrypted_client(client_id)
        assert client["nta_nos_notes_encr"] == ""

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
        client_data["class_name_encr"] = "10a"
        client_id = clients_manager.add_client(**client_data)
        client = clients_manager.get_decrypted_client(client_id)
        assert client["class_int_encr"] == 10
        assert client["estimated_graduation_date_encr"] is not None
        assert client["document_shredding_date_encr"] is not None

        # Test with no number in class_name_encr
        # FIXME: Raise an error because it containes no integer
        # TODO: write a validates method for the db model and a validator for the tui
        client_data["class_name_encr"] = "Vorklasse"
        client_id_2 = clients_manager.add_client(**client_data)
        client2 = clients_manager.get_decrypted_client(client_id_2)
        assert client2["class_int_encr"] is None
        assert client2["estimated_graduation_date_encr"] is None
        assert client2["document_shredding_date_encr"] is None


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
