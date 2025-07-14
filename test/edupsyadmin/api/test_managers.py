from datetime import date

import pytest

from edupsyadmin.api.managers import (
    ClientNotFoundError,
    enter_client_untiscsv,
)
from edupsyadmin.tui.editclient import StudentEntryApp

EXPECTED_KEYS = {
    "parent_encr",
    "class_name",
    "notenschutz",
    "nta_ersgew",
    "telephone1_encr",
    "class_int",
    "nos_rs_ausn",
    "nos_rs_ausn_faecher",
    "nta_vorlesen",
    "telephone2_encr",
    "estimated_graduation_date",
    "nta_zeitv_vieltext",
    "nta_other",
    "nta_notes",
    "email_encr",
    "document_shredding_date",
    "nos_les",
    "nta_zeitv_wenigtext",
    "nta_other_details",
    "first_name_encr",
    "notes_encr",
    "keyword_taetigkeitsbericht",
    "nachteilsausgleich",
    "nta_font",
    "last_name_encr",
    "client_id",
    "lrst_diagnosis",
    "nta_zeitv",
    "nta_aufg",
    "street_encr",
    "gender_encr",
    "school",
    "datetime_created",
    "nta_struktur",
    "n_sessions",
    "birthday_encr",
    "city_encr",
    "entry_date",
    "datetime_lastmodified",
    "nta_arbeitsm",
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
        clients_manager.edit_client(client_id, updated_data)
        updated_client = clients_manager.get_decrypted_client(client_id)

        print(f"Keys of the updated client: {updated_client.keys()}")

        assert EXPECTED_KEYS.issubset(updated_client.keys())
        assert updated_client["first_name_encr"] == "Jane"
        assert updated_client["last_name_encr"] == "Smith"

        assert updated_client["nta_zeitv_vieltext"] == 25
        assert updated_client["nta_font"] is True
        assert updated_client["nta_zeitv"] is True
        assert updated_client["nachteilsausgleich"] is True

        assert updated_client["nta_ersgew"] is False

        assert updated_client["datetime_lastmodified"] > client["datetime_lastmodified"]

        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

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
                await pilot.click(wid)
                await pilot.press(*value)

            wid = "#Submit"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
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
                await pilot.click(wid)
                if isinstance(value, bool):
                    input_widget.value = value
                    continue
                await pilot.press(*value)

            wid = "#Submit"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.click(wid)

        data = app.get_data()
        assert data == change_values


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
