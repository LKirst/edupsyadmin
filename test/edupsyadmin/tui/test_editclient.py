import pytest

from edupsyadmin.api.managers import _find_changed_values, _get_empty_client_dict
from edupsyadmin.tui.editclient import StudentEntryApp


@pytest.mark.asyncio
async def test_type_text() -> None:
    app = StudentEntryApp(42)

    async with app.run_test() as pilot:
        wid = "#first_name_encr"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.click(wid)
        await pilot.press(*"TestName")

        assert input_widget.value == "TestName"


@pytest.mark.asyncio
async def test_type_date() -> None:
    app = StudentEntryApp(42)

    async with app.run_test() as pilot:
        wid = "#entry_date"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.click(wid)
        await pilot.press(*"2025-01-01")

        assert input_widget.value == "2025-01-01"


@pytest.mark.asyncio
async def test_get_data() -> None:
    empty_client_dict = _get_empty_client_dict()
    client_dict_minimal = {
        "first_name_encr": "Lieschen",
        "last_name_encr": "Müller",
        "school": "FirstSchool",
        "gender_encr": "f",
        "class_name": "7TKKG",
        "birthday_encr": "1990-01-01",
    }

    app = StudentEntryApp(42)

    async with app.run_test() as pilot:
        for key, value in client_dict_minimal.items():
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
    changed_data = _find_changed_values(empty_client_dict, data)
    assert changed_data == client_dict_minimal
