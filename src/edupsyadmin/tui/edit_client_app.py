from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header

from edupsyadmin.tui.edit_client import EditClient

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager


class EditClientApp(App):
    """A standalone Textual App to display the EditClient widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Quit", show=True)
    ]

    def __init__(
        self,
        clients_manager: "ClientsManager",
        client_id: int | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.clients_manager = clients_manager
        self.client_id = client_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield EditClient()
        yield Footer()

    def on_mount(self) -> None:
        # Update the EditClient with data for a new client or existing one
        # For new client, client_id is None
        self.query_one(EditClient).update_client(self.client_id, None)

    async def on_edit_client_save_client(self, message: EditClient.SaveClient) -> None:
        """Handle the save message from the EditClient widget."""
        try:
            if message.client_id is not None:
                self.clients_manager.edit_client(
                    client_ids=[message.client_id], new_data=message.data
                )
            else:
                self.clients_manager.add_client(**message.data)
            self.notify("Daten erfolgreich gespeichert.")
            self.exit()  # Exit after saving
        except Exception as e:
            self.notify(f"Fehler beim Speichern: {e}", severity="error")
