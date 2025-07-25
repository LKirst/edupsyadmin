from datetime import date

import pytest

from edupsyadmin.api.managers import (
    ClientNotFoundError,
    enter_client_untiscsv,
)
from edupsyadmin.tui.editclient import StudentEntryApp

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
    "keyword_taetigkeitsbericht",
    "lrst_diagnosis",
    "lrst_last_test_date",
    "lrst_last_test_by",
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
    "h_sessions",
}


class ManagersTest:
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

    def test_edit_client(self, mock_keyring, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)
        client = clients_manager.get_decrypted_client(client_id=client_id)
        updated_data = {
            "first_name_encr": "Jane",
            "last_name_encr": "Smith",
            "nta_zeitv_vieltext": 25,
            "nta_font": True,
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
                "lrst_diagnosis": "iLst",
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
            upd_cl1_multiple["lrst_diagnosis"]
            == upd_cl2_multiple["lrst_diagnosis"]
            == "iLst"
        )

    def test_delete_client(self, clients_manager, client_dict_set_by_user):
        client_id = clients_manager.add_client(**client_dict_set_by_user)
        clients_manager.delete_client(client_id)
        try:
            clients_manager.get_decrypted_client(client_id)
            assert (
                False
            ), "Expected ClientNotFoundError exception when retrieving a deleted client"
        except ClientNotFoundError as e:
            assert e.client_id == client_id

    def test_enter_client_untiscsv(self, mock_keyring, clients_manager, mock_webuntis):
        client_id = enter_client_untiscsv(
            clients_manager, mock_webuntis, school=None, name="MustermMax1"
        )
        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert EXPECTED_KEYS.issubset(client.keys())
        assert client["first_name_encr"] == "Max"
        assert client["last_name_encr"] == "Mustermann"
        assert client["school"] == "FirstSchool"
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

    @pytest.mark.asyncio
    async def test_enter_client_tui(
        self, mock_keyring, clients_manager, client_dict_all_str
    ):
        app = StudentEntryApp(data=None)

        async with app.run_test() as pilot:
            for key, value in client_dict_all_str.items():
                wid = f"#{key}"
                input_widget = pilot.app.query_exactly_one(wid)
                app.set_focus(input_widget, scroll_visible=True)
                await pilot.wait_for_scheduled_animations()
                await pilot.pause()
                await pilot.click(wid)
                await pilot.press(*value)

            wid = "#Submit"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.pause()
            await pilot.click(wid)

        data = app.get_data()
        clients_manager.add_client(**data)

    @pytest.mark.asyncio
    async def test_edit_client_tui(
        self, mock_keyring, clients_manager, client_dict_all_str
    ):
        client_id = clients_manager.add_client(**client_dict_all_str)
        current_data = clients_manager.get_decrypted_client(client_id=client_id)

        app = StudentEntryApp(client_id, data=current_data.copy())

        change_values = {
            "first_name_encr": "SomeNewNameßä",
            "lrst_last_test_date": "2026-01-01",
            "nos_rs": True,
        }

        async with app.run_test() as pilot:
            for key, value in change_values.items():
                wid = f"#{key}"
                input_widget = pilot.app.query_exactly_one(wid)
                input_widget.value = ""
                app.set_focus(input_widget, scroll_visible=True)
                await pilot.wait_for_scheduled_animations()
                await pilot.pause()
                await pilot.click(wid)
                if isinstance(value, bool):
                    input_widget.value = value
                    continue
                await pilot.press(*value)

            wid = "#Submit"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.pause()
            await pilot.click(wid)

        data = app.get_data()
        assert data == change_values


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
