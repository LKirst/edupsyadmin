from unittest.mock import MagicMock

import pandas as pd
import pytest
from textual.widgets import DataTable, Input

from edupsyadmin.tui.edit_client import EditClient
from edupsyadmin.tui.edupsyadmintui import EdupsyadminTui

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


def test_edupsyadmintui_initial_layout(snap_compare, mock_config):
    """Test the initial layout of the main TUI."""
    mock_manager = MagicMock()
    df = pd.DataFrame(ROWS, columns=COLUMNS)
    mock_manager.get_clients_overview.return_value = df
    mock_manager.get_decrypted_client.return_value = dict(zip(COLUMNS, ROWS[0]))

    app = EdupsyadminTui(manager=mock_manager)

    async def run_before(pilot):
        await pilot.pause()
        # Wait for the table to be populated
        table = pilot.app.query_one(DataTable)
        while table.loading:
            await pilot.pause(0.01)

    assert snap_compare(app, run_before=run_before)


@pytest.mark.asyncio
async def test_select_client_populates_edit_form(snap_compare, mock_config):
    """Test that selecting a client in the overview populates the edit form."""
    mock_manager = MagicMock()
    df = pd.DataFrame(ROWS, columns=COLUMNS)
    mock_manager.get_clients_overview.return_value = df

    client_to_select = dict(zip(COLUMNS, ROWS[1]))
    mock_manager.get_decrypted_client.return_value = client_to_select

    app = EdupsyadminTui(manager=mock_manager)

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
