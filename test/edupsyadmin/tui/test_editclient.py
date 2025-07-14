import pytest

from edupsyadmin.tui.editclient import StudentEntryApp


@pytest.mark.asyncio
async def test_type_text() -> None:
    app = StudentEntryApp(42, data=None)

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
    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        wid = "#entry_date"
        input_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(input_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        await pilot.click(wid)
        await pilot.press(*"2025-01-01")

        assert input_widget.value == "2025-01-01"


@pytest.mark.asyncio
async def test_set_bool() -> None:
    app = StudentEntryApp(42, data=None)

    async with app.run_test() as pilot:
        wid = "#nos_rs"
        bool_widget = pilot.app.query_exactly_one(wid)
        app.set_focus(bool_widget, scroll_visible=True)
        await pilot.wait_for_scheduled_animations()
        assert bool_widget.value is False

        await pilot.click(wid)
        bool_widget.value = True
        assert bool_widget.value is True


@pytest.mark.asyncio
async def test_get_data() -> None:
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
        for key, value in client_dict.items():
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
    assert data == client_dict
