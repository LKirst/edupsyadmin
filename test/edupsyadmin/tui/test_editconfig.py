import keyring
import pytest
from textual.widgets import Input

from edupsyadmin.tui.editconfig import (
    ConfigEditorApp,
)


# Mock keyring
@pytest.fixture(autouse=True)
def mock_keyring(monkeypatch):
    store = {}

    def get_password(service, username):
        return store.get(f"{service}:{username}")

    def set_password(service, username, password):
        store[f"{service}:{username}"] = password

    def delete_password(service, username):
        key = f"{service}:{username}"
        store.pop(key, None)

    monkeypatch.setattr(keyring, "get_password", get_password)
    monkeypatch.setattr(keyring, "set_password", set_password)
    monkeypatch.setattr(keyring, "delete_password", delete_password)


@pytest.mark.asyncio
async def test_app_loads_config(mock_config):
    """Test if the app loads the configuration correctly."""
    app = ConfigEditorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_exactly_one("#core-logging", Input).value == "DEBUG"
        assert (
            app.query_exactly_one("#schoolpsy-schoolpsy_name", Input).value
            == "Firstname Lastname"
        )
        # TODO: check School(s)


def test_initial_layout(mock_config, snap_compare):
    app = ConfigEditorApp()
    assert snap_compare(app, terminal_size=(50, 150))


def test_add_new_school_container(mock_config, snap_compare):
    async def run_before(pilot) -> None:
        add_school_button = pilot.app.query_exactly_one("#add-school-button")
        app.set_focus(add_school_button, scroll_visible=True)
        await pilot.pause()

        await pilot.click(add_school_button)
        await pilot.pause()

    app = ConfigEditorApp()
    assert snap_compare(app, run_before=run_before, terminal_size=(50, 150))


def test_edit_new_school_container(mock_config, snap_compare):
    async def run_before(pilot) -> None:
        add_school_button = pilot.app.query_exactly_one("#add-school-button")
        app.set_focus(add_school_button, scroll_visible=True)
        await pilot.pause()

        await pilot.click(add_school_button)
        await pilot.pause()

        # Correct query for the item_key input of the newly added school editor
        from edupsyadmin.tui.editconfig import SchoolEditor

        school_editors = pilot.app.query(SchoolEditor)
        new_school_editor = school_editors[-1]
        school_key_inp = new_school_editor.query_one("#item_key", Input)
        app.set_focus(school_key_inp)

        school_key_inp.value = ""
        await pilot.press(*"NewSchool")
        await pilot.pause()
        assert school_key_inp.value == "NewSchool"

    app = ConfigEditorApp()
    assert snap_compare(app, run_before=run_before, terminal_size=(50, 150))


# TODO: Test delete school
