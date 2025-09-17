from pathlib import Path

import keyring
import pytest
import yaml
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


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    form_path = tmp_path / "form.pdf"
    form_path.touch()

    config_data = {
        "core": {"logging": "INFO", "app_uid": "test_uid", "app_username": "test_user"},
        "schoolpsy": {
            "schoolpsy_name": "Test Psy",
            "schoolpsy_street": "Street",
            "schoolpsy_city": "City",
        },
        "school": {
            "TestSchool": {
                "school_head_w_school": "Head",
                "school_name": "Test School Name",
                "school_street": "School Street",
                "school_city": "School City",
                "end": "10",
                "nstudents": "100",
            }
        },
        "form_set": {"anschreiben": ["pfad_anschreiben.pdf"]},
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)

    return config_path


@pytest.mark.asyncio
async def test_app_loads_config(config_file: Path):
    """Test if the app loads the configuration correctly."""
    app = ConfigEditorApp(config_path=config_file)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.inputs["core.logging"].value == "INFO"
        assert app.inputs["schoolpsy.schoolpsy_name"].value == "Test Psy"
        assert app.inputs["school.TestSchool.school_name"].value == "Test School Name"
        assert len(app.query(Input)) > 5


@pytest.mark.asyncio
def test_initial_layout(config_file: Path, snap_compare):
    app = ConfigEditorApp(config_path=config_file)
    assert snap_compare(app, terminal_size=(50, 150))


@pytest.mark.asyncio
def test_add_new_school_container(config_file: Path, snap_compare):
    async def run_before(pilot) -> None:
        add_school_button = pilot.app.query_exactly_one("#addschool")
        app.set_focus(add_school_button, scroll_visible=True)
        await pilot.pause()

        await pilot.click(add_school_button)
        await pilot.pause()

    app = ConfigEditorApp(config_path=config_file)
    assert snap_compare(app, run_before=run_before, terminal_size=(50, 150))


@pytest.mark.asyncio
def test_edit_new_school_container(config_file: Path, snap_compare):
    async def run_before(pilot) -> None:
        add_school_button = pilot.app.query_exactly_one("#addschool")
        app.set_focus(add_school_button, scroll_visible=True)
        await pilot.pause()

        await pilot.click(add_school_button)
        await pilot.pause()

        school_key_inp = pilot.app.query_exactly_one("#schoolkey2")
        app.set_focus(school_key_inp)

        school_key_inp.value = ""
        await pilot.press(*"NewSchool")
        await pilot.pause()
        assert school_key_inp.value == "NewSchool"

    app = ConfigEditorApp(config_path=config_file)
    assert snap_compare(app, run_before=run_before, terminal_size=(50, 150))


# TODO: Test delete school
