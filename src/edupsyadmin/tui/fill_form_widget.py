from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    SelectionList,
    Static,
)

from edupsyadmin.core.config import config

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager


class MultiSelectDirectoryTree(DirectoryTree):
    """A DirectoryTree that allows for custom multi-selection logic."""

    def __init__(
        self, path: Path | str, *, id: str | None = None, classes: str | None = None
    ) -> None:
        super().__init__(path, id=id, classes=classes)
        self.selected_paths: set[Path] = set()

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        """Called when a node is selected in the tree."""
        event.stop()
        # To distinguish between files and directories, we check the `allow_expand`
        # property of the node. Directories can be expanded, files cannot.
        if event.node and not event.node.allow_expand:
            # The data payload is an os.DirEntry, which has a .path attribute (str).
            # Convert it to a pathlib.Path object for consistent handling.
            selected_path = Path(event.node.data.path)
            if selected_path in self.selected_paths:
                self.selected_paths.remove(selected_path)
                event.node.set_label(selected_path.name)  # Reset label
            else:
                self.selected_paths.add(selected_path)
                new_label = Text.from_markup(f"[b green]{selected_path.name}[/b green]")
                event.node.set_label(new_label)
            self.app.log(f"Currently selected: {self.selected_paths}")


class FillForm(Widget):
    """A widget to select forms to fill for a given client."""

    DEFAULT_CSS = """
    FillForm {
        padding: 1;
        height: 100%;
    }
    #client-info {
        height: auto;
        border: round $accent;
        padding: 1;
        margin-bottom: 1;
    }
    #path-input-container {
        height: auto;
        margin-bottom: 1;
    }
    #path-input-container Label {
        width: auto;
        height: 3;
        content-align: center middle;
        margin-right: 1;
    }
    #path-input-container Input {
        width: 1fr;
    }
    #form-selection-container {
        width: 1fr;
        padding-left: 1;
        padding-right: 1;
    }
    #lists-container {
        height: 1fr;
    }
    DirectoryTree {
        height: 100%;
        border: solid $accent;
    }
    .button-bar {
        height: 3;
        align-horizontal: center;
        width: 100%;
    }
    .button-bar Button {
        margin: 0 1;
    }
    """

    class StartFill(Message):
        """Message to start filling forms."""

        def __init__(self, client_id: int, form_paths: list[str]) -> None:
            self.client_id = client_id
            self.form_paths = form_paths
            super().__init__()

    class Cancel(Message):
        """Message to cancel the operation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.client_id: int | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(id="client-info")
            with Horizontal(id="path-input-container"):
                yield Label("Path:")
                yield Input(id="path-input", placeholder="Enter path...")
            with Vertical():
                with Horizontal(id="lists-container"):
                    with Vertical(id="form-selection-container"):
                        yield Label("Select Form Set:")
                        yield SelectionList[str](id="form-sets")
                    with Vertical(id="form-files-container"):
                        yield MultiSelectDirectoryTree(".", id="form-files")
                with Horizontal(classes="button-bar"):
                    yield Button("Fill Form(s)", variant="primary", id="fill-button")
                    yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        """Populate the form sets and path input."""
        form_sets_widget = self.query_one("#form-sets", SelectionList)
        form_sets = list(config.form_set.keys())
        for form_set in form_sets:
            form_sets_widget.add_option((form_set, form_set))

        path_input = self.query_one("#path-input", Input)
        tree = self.query_one(MultiSelectDirectoryTree)
        path_input.value = str(Path(tree.path).resolve())

    @on(Input.Submitted, "#path-input")
    def on_path_submitted(self, event: Input.Submitted) -> None:
        """Handle path submission."""
        new_path = Path(event.value).expanduser()
        if new_path.is_dir():
            tree = self.query_one(MultiSelectDirectoryTree)
            tree.path = str(new_path)
            # Clear selection when path changes
            tree.selected_paths.clear()
        else:
            self.notify(f"Error: Path '{new_path}' is not a valid directory.")
            # Reset input to current tree path
            tree = self.query_one(MultiSelectDirectoryTree)
            current_path = Path(tree.path).resolve()
            event.input.value = str(current_path)

    def update_client(self, client_id: int, client_data: dict[str, Any]) -> None:
        """Update the widget with data for a specific client."""
        self.client_id = client_id
        info = self.query_one("#client-info", Static)
        first_name = client_data.get("first_name_encr", "")
        last_name = client_data.get("last_name_encr", "")
        info.update(
            f"Fülle Formulare für Klient*in: {first_name} {last_name} "
            f"(ID: {self.client_id})"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "fill-button":
            if self.client_id is None:
                self.notify("No client selected.", severity="error")
                return

            form_paths: list[str] = []
            form_sets_widget = self.query_one("#form-sets", SelectionList)
            if form_sets_widget.selected:
                for selected_set in form_sets_widget.selected:
                    form_paths.extend(config.form_set.get(selected_set, []))

            dir_tree = self.query_one(MultiSelectDirectoryTree)
            selected_file_paths = dir_tree.selected_paths

            for p in selected_file_paths:
                if p.suffix in (".pdf", ".md"):
                    form_paths.append(str(p))

            if not form_paths:
                self.notify(
                    "Please select at least one form or form set.", severity="error"
                )
                return

            # Deduplicate paths
            form_paths = sorted(dict.fromkeys(form_paths))

            self.post_message(self.StartFill(self.client_id, form_paths))

        elif event.button.id == "cancel-button":
            self.post_message(self.Cancel())


class FillFormScreen(Screen):
    """A screen for filling forms."""

    def __init__(
        self,
        clients_manager: ClientsManager,
        client_id: int,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.clients_manager = clients_manager
        self.client_id = client_id

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield FillForm()
        yield Footer()

    def on_mount(self) -> None:
        """Load the client data and update the FillForm widget."""
        client_data = self.clients_manager.get_decrypted_client(self.client_id)
        self.query_one(FillForm).update_client(self.client_id, client_data)
