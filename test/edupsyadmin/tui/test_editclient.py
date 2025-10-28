import pytest
from textual.widgets import Checkbox, Input

from edupsyadmin.tui.editclient import StudentEntryApp, _get_empty_client_dict


def convert_boolean_strings_to_bool(data: dict) -> dict:
    converted_data = data.copy()
    for key in [
        "nos_rs",
        "nos_les",
        "nos_other",
        "nta_font",
        "nta_aufg",
        "nta_struktur",
        "nta_arbeitsm",
        "nta_ersgew",
        "nta_vorlesen",
        "nta_other",
        "nta_nos_end",
    ]:
        if key in converted_data and isinstance(converted_data[key], str):
            converted_data[key] = bool(int(converted_data[key]))
    return converted_data


def test_initial_layout(snap_compare):
    app = StudentEntryApp(42, data=None)
    assert snap_compare(app, terminal_size=(50, 80))


@pytest.mark.asyncio
async def test_type_text() -> None:
    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        wid = "#first_name_encr"
        input_widget = pilot.app.query_exactly_one(wid)
        assert isinstance(input_widget, Input)

        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)
        await pilot.press(*"TestName")

        assert input_widget.value == "TestName"


@pytest.mark.asyncio
async def test_type_date() -> None:
    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        wid = "#entry_date"
        input_widget = pilot.app.query_exactly_one(wid)
        assert isinstance(input_widget, Input)

        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)
        await pilot.press(*"2025-01-01")

        assert input_widget.value == "2025-01-01"


@pytest.mark.asyncio
async def test_set_bool() -> None:
    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        wid = "#nos_rs"
        bool_widget = pilot.app.query_exactly_one(wid)
        assert isinstance(bool_widget, Checkbox)

        app.set_focus(bool_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        assert bool_widget.value is False

        await pilot.click(wid)
        bool_widget.value = True
        assert bool_widget.value is True


@pytest.mark.asyncio
async def test_save_returns_data(mock_config) -> None:
    client_dict = {
        "first_name_encr": "Lieschen",
        "last_name_encr": "Müller",
        "school": "FirstSchool",
        "gender_encr": "f",
        "class_name": "7TKKG",
        "birthday_encr": "1990-01-01",
    }

    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        for key, value in client_dict.items():
            wid = f"#{key}"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.pause()
            await pilot.click(wid)
            await pilot.press(*value)

        wid = "#save"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)

    assert app.return_value == client_dict


@pytest.mark.asyncio
async def test_enter_client_tui(mock_config, client_dict_all_str):
    app = StudentEntryApp(data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        for key, value in client_dict_all_str.items():
            if key == "client_id":  # client_id is not an input field
                continue
            wid = f"#{key}"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.pause()
            await pilot.click(wid)
            if isinstance(input_widget, Checkbox):
                input_widget.value = bool(
                    int(value)
                )  # Convert string "0" or "1" to boolean
            else:
                await pilot.press(*value)

        wid = "#save"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)

    data = app.return_value
    expected_data = _get_empty_client_dict()
    # Update with values from client_dict_all_str, excluding client_id
    for k, v in client_dict_all_str.items():
        if k != "client_id":
            expected_data[k] = v
    expected_data = convert_boolean_strings_to_bool(expected_data)

    # Filter expected_data to only include keys present in data
    # This is because app.get_data() only returns changed fields
    filtered_expected_data = {k: expected_data[k] for k in data if k in expected_data}

    assert data == filtered_expected_data


@pytest.mark.asyncio
async def test_edit_client_tui(clients_manager, client_dict_all_str):
    client_id = clients_manager.add_client(**client_dict_all_str)
    current_data = clients_manager.get_decrypted_client(client_id=client_id)

    app = StudentEntryApp(client_id, data=current_data.copy())

    change_values = {
        "first_name_encr": "SomeNewNameßä",
        "lrst_last_test_date_encr": "2026-01-01",
        "nos_rs": True,
    }

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        for key, value in change_values.items():
            wid = f"#{key}"
            input_widget = pilot.app.query_exactly_one(wid)
            app.set_focus(input_widget, scroll_visible=True)
            await pilot.wait_for_scheduled_animations()
            await pilot.pause()
            await pilot.click(wid)
            if isinstance(input_widget, Checkbox):
                input_widget.value = value
            else:
                input_widget.value = ""  # Clear the input field
                await pilot.press(*value)

        wid = "#save"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)

    data = app.return_value
    assert data == change_values


@pytest.mark.asyncio
async def test_cancel_returns_none() -> None:
    app = StudentEntryApp(data=None)

    async with app.run_test() as pilot:
        await pilot.resize_terminal(1000, 1000)
        # Simulate clicking the cancel button
        wid = "#cancel"
        cancel_button = pilot.app.query_exactly_one(wid)
        app.set_focus(cancel_button, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.pause()
        await pilot.click(wid)

    assert app.return_value is None
