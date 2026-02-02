import pytest
import yaml
from conftest import TEST_UID, TEST_USERNAME
from textual.widgets import Input

from edupsyadmin.tui.editconfig import (
    ConfigEditorApp,
    SchoolEditor,
)


@pytest.mark.asyncio
async def test_app_loads_config(mock_config_snapshots):
    """Test if the app loads the configuration correctly."""
    app = ConfigEditorApp(mock_config_snapshots, TEST_UID, TEST_USERNAME)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_exactly_one("#core-logging", Input).value == "DEBUG"
        assert (
            app.query_exactly_one("#schoolpsy-schoolpsy_name", Input).value
            == "Firstname Lastname"
        )
        # TODO: check School(s)


def test_initial_layout(mock_config_snapshots, snap_compare):
    app = ConfigEditorApp(mock_config_snapshots, TEST_UID, TEST_USERNAME)
    assert snap_compare(app, terminal_size=(80, 250))


def test_add_new_school_container(mock_config_snapshots, snap_compare):
    app = ConfigEditorApp(mock_config_snapshots, TEST_UID, TEST_USERNAME)

    async def run_before(pilot):
        add_school_button = pilot.app.query_one("#add-school-button")
        add_school_button.focus()
        await pilot.pause()
        await pilot.click(add_school_button)
        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(80, 280))


def test_edit_new_school_container(mock_config_snapshots, snap_compare):
    app = ConfigEditorApp(mock_config_snapshots, TEST_UID, TEST_USERNAME)

    async def run_before(pilot):
        add_school_button = pilot.app.query_one("#add-school-button")
        add_school_button.focus()
        await pilot.pause()
        await pilot.click(add_school_button)
        await pilot.pause()

        # Correct query for the item_key input of the newly added school editor
        school_editors = pilot.app.query(SchoolEditor)
        new_school_editor = school_editors[-1]
        school_key_inp = new_school_editor.query_one("#item_key", Input)
        school_key_inp.focus()

        school_key_inp.value = ""
        await pilot.press(*"NewSchoolEdited")
        await pilot.pause()
        assert school_key_inp.value == "NewSchoolEdited"

    assert snap_compare(app, run_before=run_before, terminal_size=(80, 280))


# TODO: Test delete school


@pytest.mark.asyncio
async def test_app_saves_config_changes(mock_config):
    """Test if the app saves changes to the configuration file."""
    config_path = mock_config
    app = ConfigEditorApp(config_path, TEST_UID, TEST_USERNAME)

    new_logging_level = "INFO"
    new_schoolpsy_name = "Dr. New Name"
    test_password = "test_password_12345"

    async with app.run_test() as pilot:
        # Change values in the input fields
        logging_input = app.query_exactly_one("#core-logging", Input)
        logging_input.value = new_logging_level

        schoolpsy_name_input = app.query_exactly_one("#schoolpsy-schoolpsy_name", Input)
        schoolpsy_name_input.value = new_schoolpsy_name

        # Set password so the save doesn't abort
        password_input = app.query_exactly_one("#password", Input)
        password_input.value = test_password

        password_confirm_input = app.query_exactly_one("#password_confirm", Input)
        password_confirm_input.value = test_password

        await pilot.click("#save")

    # Read the config file after the app has exited
    with config_path.open("w") as f:
        saved_config = yaml.safe_load(f)

    # Assert that the changes were saved
    assert saved_config["core"]["logging"] == new_logging_level
    assert saved_config["schoolpsy"]["schoolpsy_name"] == new_schoolpsy_name
