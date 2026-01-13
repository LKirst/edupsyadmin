from datetime import date
from unittest.mock import MagicMock

import pytest
from textual.widgets import Checkbox, Input, Select

from edupsyadmin.tui.edit_client import EditClient, _get_empty_client_dict
from edupsyadmin.tui.edit_client_app import EditClientApp

TERMINAL_SIZE = (70, 130)


@pytest.fixture
def mock_clients_manager(client_dict_set_by_user, mock_config):
    """A mock clients manager that uses mock_config to ensure config is loaded."""
    manager = MagicMock()
    client_data = client_dict_set_by_user.copy()
    if "birthday_encr" in client_data and isinstance(client_data["birthday_encr"], str):
        try:
            client_data["birthday_encr"] = date.fromisoformat(
                client_data["birthday_encr"]
            )
        except (ValueError, TypeError):
            client_data["birthday_encr"] = None
    manager.get_decrypted_client.return_value = client_data
    return manager


def test_initial_layout_existing_client(
    snap_compare, mock_clients_manager, client_dict_set_by_user, mock_config
):
    """Test the initial layout of the edit client screen for an existing client."""
    client_id = client_dict_set_by_user.get("client_id") or 42
    app = EditClientApp(clients_manager=mock_clients_manager, client_id=client_id)

    async def run_before(pilot):
        await pilot.pause()
        while not pilot.app.query(Input):
            await pilot.pause(0.01)

    assert snap_compare(app, run_before=run_before, terminal_size=TERMINAL_SIZE)


def test_initial_layout_new_client(snap_compare, mock_config):
    """Test the initial layout of the edit client screen for a new client."""
    local_mock_manager = MagicMock()
    local_mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=local_mock_manager, client_id=None)

    async def run_before(pilot):
        await pilot.pause()
        while not pilot.app.query(Input):
            await pilot.pause(0.01)

    assert snap_compare(app, run_before=run_before, terminal_size=TERMINAL_SIZE)


@pytest.mark.asyncio
async def test_type_text(mock_config):
    local_mock_manager = MagicMock()
    local_mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=local_mock_manager, client_id=None)

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        wid = "#first_name_encr"
        input_widget = pilot.app.query_one(wid, Input)
        input_widget.focus()
        await pilot.press(*"TestName")
        assert input_widget.value == "TestName"


@pytest.mark.asyncio
async def test_type_date(mock_config):
    local_mock_manager = MagicMock()
    local_mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=local_mock_manager, client_id=None)

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        wid = "#entry_date"
        input_widget = pilot.app.query_one(wid, Input)
        input_widget.focus()
        await pilot.press(*"2025-01-01")
        assert input_widget.value == "2025-01-01"


@pytest.mark.asyncio
async def test_set_bool(mock_config):
    local_mock_manager = MagicMock()
    local_mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=local_mock_manager, client_id=None)

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        wid = "#nos_rs"
        bool_widget = pilot.app.query_one(wid, Checkbox)
        assert bool_widget.value is False
        await pilot.click(wid)
        assert bool_widget.value is True


@pytest.mark.asyncio
async def test_save_new_client_triggers_add(client_dict_all_str, mock_config):
    """Test that saving a new client triggers the `add_client` method on the manager."""
    mock_manager = MagicMock()
    mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=mock_manager, client_id=None)

    typed_values = client_dict_all_str.copy()
    typed_values.pop("client_id", None)

    widget_types = {}

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        while not pilot.app.query(Input):
            await pilot.pause(0.01)

        edit_client = pilot.app.query_one(EditClient)
        for key, value in typed_values.items():
            if not value:
                continue
            widget = edit_client.query_one(f"#{key}")
            widget_types[key] = type(widget)
            if isinstance(widget, Checkbox):
                widget.value = value == "1"
            elif isinstance(widget, Input | Select):
                widget.value = value

        await edit_client.action_save()
        await pilot.pause()

    mock_manager.add_client.assert_called_once()
    called_kwargs = mock_manager.add_client.call_args.kwargs

    # The data sent to add_client should only be the data that differs
    # from a default new client.
    defaults = _get_empty_client_dict()

    expected_data = {}
    for k, v in typed_values.items():
        if not v:
            continue

        val_to_check = None
        val_to_check = v == "1" if widget_types.get(k) is Checkbox else v

        if val_to_check != defaults.get(k):
            expected_data[k] = val_to_check

    assert called_kwargs == expected_data


@pytest.mark.asyncio
async def test_edit_client_triggers_edit(
    clients_manager, client_dict_all_str, mock_config
):
    """Test that editing an existing client triggers the `edit_client` method."""
    client_id = clients_manager.add_client(**client_dict_all_str)

    app = EditClientApp(clients_manager=clients_manager, client_id=client_id)

    change_values = {
        "first_name_encr": "SomeNewNameßä",
        "lrst_last_test_date_encr": "2026-01-01",
        "nos_rs": True,
    }

    async with app.run_test(size=TERMINAL_SIZE) as pilot:
        await pilot.pause()
        while not pilot.app.query(Input):
            await pilot.pause(0.01)

        edit_client = pilot.app.query_one(EditClient)
        for key, value in change_values.items():
            widget = edit_client.query_one(f"#{key}")
            if isinstance(widget, Input | Select):
                widget.value = str(value)
            elif isinstance(widget, Checkbox):
                widget.value = value

        await edit_client.action_save()
        await pilot.pause()

    edited_client = clients_manager.get_decrypted_client(client_id)
    for key, value in change_values.items():
        retrieved_value = edited_client[key]
        if isinstance(retrieved_value, date):
            assert retrieved_value.isoformat() == value
        elif isinstance(retrieved_value, bool):
            assert retrieved_value == value
        else:
            assert str(retrieved_value) == str(value)


@pytest.mark.asyncio
async def test_cancel_exits(mock_config):
    """Test that cancelling an edit exits the app."""
    local_mock_manager = MagicMock()
    local_mock_manager.get_decrypted_client.return_value = None
    app = EditClientApp(clients_manager=local_mock_manager, client_id=None)
    async with app.run_test() as pilot:
        await pilot.pause()
        while not pilot.app.query(Input):
            await pilot.pause(0.01)

        await pilot.app.query_one(EditClient).action_cancel()
        await pilot.pause()

    assert app._exit is True
