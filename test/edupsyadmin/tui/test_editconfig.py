import asyncio
from pathlib import Path

import pytest
import yaml
from conftest import TEST_UID, TEST_USERNAME
from textual.widgets import Input, RichLog

from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.core.config import AppConfig
from edupsyadmin.tui.editconfig import (
    PathIsDirValidator,
    PathIsFileValidator,
    SchoolEditor,
)
from edupsyadmin.tui.editconfig_app import (
    ConfigEditorApp,
)

# TODO: Use fixtures consistently


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    """Create and migrate a fresh SQLite database, returning its URL."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    upgrade_db(url)
    return url


@pytest.mark.asyncio
async def test_app_loads_config(mock_config_snapshots, db_url):
    """Test if the app loads the configuration correctly."""
    app = ConfigEditorApp(
        mock_config_snapshots,
        TEST_UID,
        TEST_USERNAME,
        database_url=db_url,
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_exactly_one("#core-logging", Input).value == "DEBUG"
        assert (
            app.query_exactly_one("#schoolpsy-schoolpsy_name", Input).value
            == "Firstname Lastname"
        )
        # TODO: check School(s)


def test_editconfig_initial_layout(mock_config_snapshots, snap_compare, db_url):
    app = ConfigEditorApp(
        mock_config_snapshots,
        TEST_UID,
        TEST_USERNAME,
        database_url=db_url,
    )
    assert snap_compare(app, terminal_size=(80, 250))


def test_add_new_school_container(mock_config_snapshots, snap_compare, db_url):
    app = ConfigEditorApp(
        mock_config_snapshots,
        TEST_UID,
        TEST_USERNAME,
        database_url=db_url,
    )

    async def run_before(pilot):
        add_school_button = pilot.app.query_one("#add-school-button")
        add_school_button.focus()
        await pilot.pause()
        await pilot.click(add_school_button)
        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(80, 280))


def test_edit_new_school_container(mock_config_snapshots, snap_compare, db_url):
    app = ConfigEditorApp(
        mock_config_snapshots,
        TEST_UID,
        TEST_USERNAME,
        database_url=db_url,
    )

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
async def test_app_saves_config_changes(mock_config, tmp_path):
    """Test if the app saves changes to the configuration file."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    config_path = mock_config
    app = ConfigEditorApp(config_path, TEST_UID, TEST_USERNAME, database_url=db_url)

    new_logging_level = "INFO"
    new_schoolpsy_name = "Dr. New Name"
    new_template_directory = "/home/test/templates"
    new_output_directory = "/home/test/output"
    test_password = "test_password_12345"

    async with app.run_test() as pilot:
        # Change values in the input fields
        logging_input = app.query_exactly_one("#core-logging", Input)
        logging_input.value = new_logging_level

        template_dir_input = app.query_exactly_one("#core-template_directory", Input)
        template_dir_input.value = new_template_directory

        output_dir_input = app.query_exactly_one("#core-output_directory", Input)
        output_dir_input.value = new_output_directory

        schoolpsy_name_input = app.query_exactly_one("#schoolpsy-schoolpsy_name", Input)
        schoolpsy_name_input.value = new_schoolpsy_name

        # Set kdf_iterations to 1 to speed up the test
        kdf_iterations_input = app.query_exactly_one("#core-kdf_iterations", Input)
        kdf_iterations_input.value = "1"

        # Set password so the save doesn't abort
        password_input = app.query_exactly_one("#password", Input)
        password_input.value = test_password

        password_confirm_input = app.query_exactly_one("#password_confirm", Input)
        password_confirm_input.value = test_password

        await pilot.click("#save")

        # Wait for the app to exit (it exits after saving)
        for _ in range(100):
            if not app._running:
                break
            await asyncio.sleep(0.05)

    # Read the config file after the app has exited
    with config_path.open("r") as f:
        saved_config = yaml.safe_load(f)

    # Assert that the changes were saved
    assert saved_config["core"]["logging"] == new_logging_level
    assert saved_config["core"]["template_directory"] == new_template_directory
    assert saved_config["core"]["output_directory"] == new_output_directory
    assert saved_config["schoolpsy"]["schoolpsy_name"] == new_schoolpsy_name


def test_path_validators_empty_string(tmp_path: Path) -> None:
    """Test path validators handling of empty string."""
    assert not PathIsFileValidator.validate("").is_valid
    assert not PathIsDirValidator.validate("").is_valid
    assert PathIsDirValidator.validate(str(tmp_path)).is_valid


@pytest.mark.asyncio
async def test_log_widget_hidden_initially(mock_config, tmp_path):
    """Test that #edit-config-log is hidden by default."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)
    async with app.run_test():
        log = app.query_one("#edit-config-log", expect_type=RichLog)
        assert not log.has_class("-visible")


@pytest.mark.asyncio
async def test_add_new_school_and_save_success(mock_config, tmp_path):
    """Test adding a new school, filling all required fields, and saving."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    config_path = mock_config
    app = ConfigEditorApp(config_path, TEST_UID, TEST_USERNAME, database_url=db_url)
    test_password = "test_password_12345"

    expected_end = 12
    expected_nstudents = 850

    async with app.run_test(size=(80, 250)) as pilot:
        add_btn = app.query_one("#add-school-button")
        add_btn.focus()
        await pilot.pause()
        await pilot.click(add_btn)
        await pilot.pause()

        school_editors = list(app.query(SchoolEditor).results(SchoolEditor))
        new_editor = school_editors[-1]

        new_editor.query_one("#item_key", expect_type=Input).value = "Gymnasium"
        new_editor.query_one(
            "#school_name",
            expect_type=Input,
        ).value = "Goethe Gymnasium"
        new_editor.query_one("#school_street", expect_type=Input).value = "Schulstr. 5"
        new_editor.query_one(
            "#school_city",
            expect_type=Input,
        ).value = "80331 Muenchen"
        new_editor.query_one(
            "#school_head_w_school",
            expect_type=Input,
        ).value = "OStD Mueller"
        new_editor.query_one("#end", expect_type=Input).value = str(expected_end)
        new_editor.query_one(
            "#nstudents",
            expect_type=Input,
        ).value = str(expected_nstudents)

        kdf_iterations_input = app.query_exactly_one("#core-kdf_iterations", Input)
        kdf_iterations_input.value = "1"

        password_input = app.query_exactly_one("#password", Input)
        password_input.value = test_password
        password_confirm_input = app.query_exactly_one("#password_confirm", Input)
        password_confirm_input.value = test_password

        save_btn = app.query_one("#save")
        save_btn.focus()
        await pilot.pause()
        await pilot.click(save_btn)

        for _ in range(100):
            if not app._running:
                break
            await asyncio.sleep(0.05)

    assert not app._running

    with config_path.open("r", encoding="utf-8") as f:
        saved_config = yaml.safe_load(f)

    assert "Gymnasium" in saved_config["school"]
    gym = saved_config["school"]["Gymnasium"]
    assert gym["school_name"] == "Goethe Gymnasium"
    assert gym["school_street"] == "Schulstr. 5"
    assert gym["school_city"] == "80331 Muenchen"
    assert gym["school_head_w_school"] == "OStD Mueller"
    assert gym["end"] == expected_end
    assert gym["nstudents"] == expected_nstudents

    # Ensure the saved YAML passes Pydantic validation
    app_config = AppConfig(**saved_config)
    assert app_config.school["Gymnasium"].end == expected_end


@pytest.mark.asyncio
async def test_add_new_school_empty_required_fields_blocks_save(mock_config, tmp_path):
    """Test that adding a school with empty fields blocks save and highlights inputs."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)

    async with app.run_test(size=(80, 250)) as pilot:
        add_btn = app.query_one("#add-school-button")
        add_btn.focus()
        await pilot.pause()
        await pilot.click(add_btn)
        await pilot.pause()

        school_editors = list(app.query(SchoolEditor).results(SchoolEditor))
        new_editor = school_editors[-1]

        save_btn = app.query_one("#save")
        save_btn.focus()
        await pilot.pause()
        await pilot.click(save_btn)
        await pilot.pause()

        # App must remain running
        assert app._running

        # Log must become visible
        log = app.query_one("#edit-config-log", expect_type=RichLog)
        assert log.has_class("-visible")

        # Empty fields on the new editor must have -invalid class
        assert new_editor.query_one(
            "#school_name",
            expect_type=Input,
        ).has_class("-invalid")
        assert new_editor.query_one("#end", expect_type=Input).has_class("-invalid")
        assert new_editor.query_one(
            "#nstudents",
            expect_type=Input,
        ).has_class("-invalid")


@pytest.mark.asyncio
async def test_save_without_keys_or_password_blocks_save(mock_config, tmp_path):
    """Test that attempting to save without keys or password displays log error."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)

    async with app.run_test(size=(80, 250)) as pilot:
        save_btn = app.query_one("#save")
        save_btn.focus()
        await pilot.pause()
        await pilot.click(save_btn)

        # Wait a moment for worker to complete
        for _ in range(20):
            await pilot.pause()
            log = app.query_one("#edit-config-log", expect_type=RichLog)
            if log.has_class("-visible"):
                break
            await asyncio.sleep(0.05)

        assert app._running
        log = app.query_one("#edit-config-log", expect_type=RichLog)
        assert log.has_class("-visible")


@pytest.mark.asyncio
async def test_duplicate_school_key_blocks_save(mock_config, tmp_path):
    """Test that duplicate school keys are caught by validation and block save."""
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    app = ConfigEditorApp(mock_config, TEST_UID, TEST_USERNAME, database_url=db_url)

    async with app.run_test(size=(80, 250)) as pilot:
        add_btn = app.query_one("#add-school-button")
        add_btn.focus()
        await pilot.pause()
        await pilot.click(add_btn)
        await pilot.pause()

        school_editors = list(app.query(SchoolEditor).results(SchoolEditor))
        new_editor = school_editors[-1]

        # Use duplicate key "FirstSchool" which already exists in sampleconfig
        new_editor.query_one("#item_key", expect_type=Input).value = "FirstSchool"
        new_editor.query_one(
            "#school_name",
            expect_type=Input,
        ).value = "Dup Name"
        new_editor.query_one("#school_street", expect_type=Input).value = "Dup Str"
        new_editor.query_one("#school_city", expect_type=Input).value = "Dup City"
        new_editor.query_one(
            "#school_head_w_school",
            expect_type=Input,
        ).value = "Dup Head"
        new_editor.query_one("#end", expect_type=Input).value = "10"
        new_editor.query_one("#nstudents", expect_type=Input).value = "100"

        save_btn = app.query_one("#save")
        save_btn.focus()
        await pilot.pause()
        await pilot.click(save_btn)
        await pilot.pause()

        assert app._running
        log = app.query_one("#edit-config-log", expect_type=RichLog)
        assert log.has_class("-visible")
