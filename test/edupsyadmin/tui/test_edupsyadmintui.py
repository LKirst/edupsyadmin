from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from textual.widgets import DataTable, Input

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.tui.edit_client import EditClient
from edupsyadmin.tui.edupsyadmintui import EdupsyadminTui
from edupsyadmin.tui.fill_form_widget import FillForm

ROWS = [
    (1, "FirstSchool", "abc123", "xyz789", "10A", False, True, "lrst", 50, "key1.a"),
    (2, "FirstSchool", "def456", "uvw345", "9B", True, False, "iRst", 30, "key1.b"),
]
COLUMNS = [
    "client_id",
    "school",
    "first_name_encr",
    "last_name_encr",
    "class_name",
    "notenschutz",
    "nachteilsausgleich",
    "lrst_diagnosis",
    "min_sessions",
    "keyword_taet_encr",
]


@pytest.fixture
def mock_clients_manager():
    """Provides a mock ClientsManager."""
    manager = MagicMock()
    df = pd.DataFrame(ROWS, columns=COLUMNS)
    manager.get_clients_overview.return_value = df
    manager.get_decrypted_client.return_value = dict(
        zip(COLUMNS, ROWS[0], strict=False)
    )
    return manager


def test_edupsyadmintui_initial_layout(snap_compare, mock_config, mock_clients_manager):
    """Test the initial layout of the main TUI."""
    app = EdupsyadminTui(manager=mock_clients_manager)

    async def run_before(pilot):
        await pilot.pause()
        # Wait for the table to be populated
        table = pilot.app.query_one(DataTable)
        while table.loading:
            await pilot.pause(0.01)

    assert snap_compare(app, run_before=run_before)


@pytest.mark.asyncio
async def test_select_client_populates_edit_form(mock_config, mock_clients_manager):
    """Test that selecting a client in the overview populates the edit form."""
    client_to_select = dict(zip(COLUMNS, ROWS[1], strict=False))
    mock_clients_manager.get_decrypted_client.return_value = client_to_select

    app = EdupsyadminTui(manager=mock_clients_manager)

    async with app.run_test() as pilot:
        await pilot.pause()
        table = pilot.app.query_one(DataTable)
        while table.loading:
            await pilot.pause(0.01)

        # Select the second row (index 1)
        table.action_cursor_down()
        await pilot.press("enter")
        await pilot.pause()

        # Wait for edit form to populate
        edit_client_widget = pilot.app.query_one(EditClient)
        while edit_client_widget.client_id != client_to_select["client_id"]:
            await pilot.pause(0.01)

        first_name_input = edit_client_widget.query_one("#first_name_encr", Input)
        assert first_name_input.value == client_to_select["first_name_encr"]


@pytest.mark.asyncio
@patch("edupsyadmin.tui.edupsyadmintui.fill_form")
@patch("edupsyadmin.tui.edupsyadmintui.EdupsyadminTui.pop_screen")
async def test_fill_form_worker_uses_convenience_data(
    mock_pop_screen, mock_fill_form, mock_clients_manager, mock_config
):
    """Test that the TUI calls add_convenience_data before filling forms."""
    # Arrange
    raw_client_data = {
        "first_name_encr": "Test",
        "last_name_encr": "User",
        "birthday_encr": "2010-05-12",
    }
    mock_clients_manager.get_decrypted_client.return_value = raw_client_data

    # Calculate the expected data after it has been processed
    expected_data = add_convenience_data(raw_client_data.copy())

    app = EdupsyadminTui(manager=mock_clients_manager)

    # Act
    client_id = 123
    form_paths = ["/fake/form.pdf"]
    async with app.run_test() as pilot:
        # Post the message that the FillForm widget would send to start the worker
        app.post_message(FillForm.StartFill([client_id], form_paths))
        await pilot.pause()  # Allow worker to run

    # Assert
    mock_fill_form.assert_called_once()
    call_args, _ = mock_fill_form.call_args
    actual_data_passed = call_args[0]

    # Verify that the data passed to fill_form was the processed data
    assert actual_data_passed == expected_data
    assert (
        "birthday_encr_de" in actual_data_passed
    )  # Check for a field added by convenience func
