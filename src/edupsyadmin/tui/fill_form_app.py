from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header, LoadingIndicator

from edupsyadmin.tui.fill_form_widget import FillForm

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager


class FillFormApp(App[None]):
    """A standalone Textual App to display the FillForm widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Quit", show=True)
    ]

    def __init__(
        self,
        clients_manager: ClientsManager,
        client_id: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.clients_manager = clients_manager
        self.client_id = client_id

    def compose(self) -> ComposeResult:
        yield Header()
        yield FillForm()
        yield Footer()
        yield LoadingIndicator()

    def on_mount(self) -> None:
        self.query_one(LoadingIndicator).display = False
        client_data = self.clients_manager.get_decrypted_client(self.client_id)
        self.query_one(FillForm).update_client(self.client_id, client_data)

    @work(exclusive=True, thread=True)
    def fill_forms_worker(self, client_id: int, form_paths: list[str]) -> None:
        """Worker to fill forms."""
        from edupsyadmin.api.add_convenience_data import add_convenience_data
        from edupsyadmin.api.fill_form import fill_form

        try:
            client_data = self.clients_manager.get_decrypted_client(client_id)
            client_data_with_convenience = add_convenience_data(client_data)
            fill_form(client_data_with_convenience, form_paths)
            self.notify("Forms filled successfully.")
        except Exception as e:
            self.notify(f"Error filling forms: {e}", severity="error")
        finally:
            self.call_from_thread(self.exit)

    async def on_fill_form_start_fill(self, message: FillForm.StartFill) -> None:
        """Handle the start fill message from the FillForm widget."""
        self.query_one(LoadingIndicator).display = True
        self.query_one(FillForm).disabled = True
        self.fill_forms_worker(message.client_id, message.form_paths)

    async def on_fill_form_cancel(self, message: FillForm.Cancel) -> None:
        """Handle the cancel message from the FillForm widget."""
        self.exit()
