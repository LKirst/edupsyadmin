from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import Input, SelectionList

from edupsyadmin.tui.fill_form_app import FillFormApp
from edupsyadmin.tui.fill_form_widget import FillForm, MultiSelectDirectoryTree

CLIENT_ID = 42
CLIENT_DATA = {
    "client_id": CLIENT_ID,
    "first_name_encr": "John",
    "last_name_encr": "Doe",
}


@pytest.fixture
def mock_clients_manager(mock_config):
    """A mock clients manager for the fill form TUI."""
    manager = MagicMock()
    manager.get_decrypted_client.return_value = CLIENT_DATA
    return manager


def test_initial_layout(snap_compare, mock_clients_manager, tmp_path):
    """Test the initial layout of the fill form app."""
    # Create a mock directory structure
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "form_a.pdf").touch()
    (docs_dir / "letter.md").touch()

    img_dir = tmp_path / "images"
    img_dir.mkdir()
    (img_dir / "logo.png").touch()

    (tmp_path / "README.md").touch()
    (tmp_path / "form_b.pdf").touch()

    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])

    async def run_before(pilot):
        # Point the DirectoryTree to the mock directory
        dir_tree = pilot.app.query_one(MultiSelectDirectoryTree)
        dir_tree.path = str(tmp_path)

        # Update the path input to match
        path_input = pilot.app.query_one("#path-input", Input)
        path_input.value = "TMP/DIR"

        await pilot.pause()

    assert snap_compare(app, run_before=run_before, terminal_size=(70, 35))


@pytest.mark.asyncio
async def test_path_input_valid(mock_clients_manager, tmp_path):
    """Test entering a valid path in the path input updates the DirectoryTree."""
    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    async with app.run_test() as pilot:
        fill_form_widget = pilot.app.query_one(FillForm)
        path_input = fill_form_widget.query_one("#path-input", Input)
        dir_tree = fill_form_widget.query_one(
            "MultiSelectDirectoryTree", MultiSelectDirectoryTree
        )

        # Initially, the path input should show the current working directory
        assert path_input.value == str(Path().resolve())
        assert dir_tree.path == Path()

        # Simulate selecting a file before changing path
        mock_file_path = tmp_path / "mock_file.pdf"
        mock_file_path.touch()
        dir_tree.selected_paths.add(mock_file_path)
        assert mock_file_path in dir_tree.selected_paths

        # Enter a new valid path
        new_path = tmp_path / "subdir"
        new_path.mkdir()
        path_input.value = str(new_path)
        fill_form_widget.post_message(
            Input.Submitted(input=path_input, value=path_input.value)
        )
        await pilot.pause()

        # Verify the DirectoryTree's path is updated
        assert dir_tree.path == new_path
        # Verify the selection is cleared
        assert not dir_tree.selected_paths

        # Verify no error notification
        with patch.object(FillForm, "notify") as mock_notify:
            await pilot.pause()
            mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_path_input_invalid(mock_clients_manager, tmp_path):
    """Test invalid path input: notification and reset."""
    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    async with app.run_test() as pilot:
        fill_form_widget = pilot.app.query_one(FillForm)
        path_input = fill_form_widget.query_one("#path-input", Input)
        dir_tree = fill_form_widget.query_one(
            "MultiSelectDirectoryTree", MultiSelectDirectoryTree
        )

        original_path_value = path_input.value  # Current working directory
        original_tree_path = dir_tree.path  # Path object

        invalid_path = tmp_path / "non_existent_dir" / "file.txt"  # Not a directory

        with patch.object(FillForm, "notify") as mock_notify:
            path_input.value = str(invalid_path)
            fill_form_widget.post_message(
                Input.Submitted(input=path_input, value=path_input.value)
            )
            await pilot.pause()

            # Verify notification is shown
            mock_notify.assert_called_once_with(
                f"Error: Path '{invalid_path}' is not a valid directory."
            )

            # Verify DirectoryTree's path is NOT updated
            assert dir_tree.path == original_tree_path
            # Verify input value is reset to the last valid path
            assert path_input.value == original_path_value


@pytest.mark.asyncio
async def test_fill_button_no_forms_notification(mock_clients_manager):
    """Test that a notification is shown if no forms are selected."""
    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    with patch.object(FillForm, "notify") as mock_notify:
        async with app.run_test() as pilot:
            await pilot.click("#fill-button")
            await pilot.pause()

    mock_notify.assert_called_once_with(
        "Please select at least one form or form set.", severity="error"
    )


@pytest.mark.asyncio
@patch("edupsyadmin.tui.fill_form_widget.config")
async def test_fill_button_emits_start_fill_message(
    mock_config, mock_clients_manager, tmp_path
):
    """Test that the 'Fill Form(s)' button emits the StartFill message."""
    mock_config.form_set = {"MySet": ["/path/to/set_form.pdf"]}
    form_path = tmp_path / "form1.pdf"
    form_path.touch()

    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    messages = []
    app.post_message = messages.append

    async with app.run_test() as pilot:
        fill_form_widget = pilot.app.query_one(FillForm)

        # 1. Select a form set
        form_sets_widget = fill_form_widget.query_one("#form-sets", SelectionList)
        form_sets_widget.select("MySet")

        # 2. Select a file from DirectoryTree
        dir_tree = fill_form_widget.query_one(
            "MultiSelectDirectoryTree", MultiSelectDirectoryTree
        )
        dir_tree.selected_paths = {form_path}

        # 3. Click the button
        await pilot.click("#fill-button")
        await pilot.pause()

    start_fill_messages = [m for m in messages if isinstance(m, FillForm.StartFill)]
    assert len(start_fill_messages) == 1
    message = start_fill_messages[0]
    assert message.client_ids == [CLIENT_ID]
    assert set(message.form_paths) == {
        "/path/to/set_form.pdf",
        str(form_path),
    }


@pytest.mark.asyncio
async def test_cancel_button_emits_cancel_message(mock_clients_manager):
    """Test that the 'Cancel' button emits the Cancel message."""
    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    messages = []
    app.post_message = messages.append

    async with app.run_test() as pilot:
        await pilot.click("#cancel-button")
        await pilot.pause()

    cancel_messages = [m for m in messages if isinstance(m, FillForm.Cancel)]
    assert len(cancel_messages) == 1


@pytest.mark.asyncio
async def test_select_directory_and_file_nodes(mock_clients_manager, tmp_path):
    """Test that selecting a directory doesn't crash, and selecting a file works."""
    # Arrange
    app = FillFormApp(clients_manager=mock_clients_manager, client_ids=[CLIENT_ID])
    (tmp_path / "my_test_dir").mkdir()
    test_file_path = tmp_path / "my_test_file.pdf"
    test_file_path.touch()

    async with app.run_test() as pilot:
        tree = pilot.app.query_one(MultiSelectDirectoryTree)
        tree.path = str(tmp_path)
        await pilot.pause()  # Let the tree reload

        # Find the nodes for the directory and file
        dir_node = next(
            (n for n in tree.root.children if n.label.plain == "my_test_dir"), None
        )
        file_node = next(
            (n for n in tree.root.children if n.label.plain == "my_test_file.pdf"),
            None,
        )
        assert dir_node is not None
        assert file_node is not None

        # Act 1: Simulate selecting the directory node by posting an event
        tree.post_message(tree.NodeSelected(dir_node))
        await pilot.pause()

        # Assert 1: No crash occurred and the directory was not added to selection
        assert not tree.selected_paths

        # Act 2: Simulate selecting the file node
        tree.post_message(tree.NodeSelected(file_node))
        await pilot.pause()

        # Assert 2: The file was added to the selection
        assert len(tree.selected_paths) == 1
        assert test_file_path in tree.selected_paths
