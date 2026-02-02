from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Footer, Header, LoadingIndicator

from edupsyadmin.api.fill_form import fill_form
from edupsyadmin.tui.clients_overview import ClientsOverview
from edupsyadmin.tui.edit_client import EditClient
from edupsyadmin.tui.fill_form_widget import FillForm, FillFormScreen

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager

BUSY_MSG = "Beschäftigt. Bitte warten, bis der vorherige Vorgang abgeschlossen ist."


class EdupsyadminTui(App[None]):
    """The main TUI for the application."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        layout: horizontal;
    }
    ClientsOverview {
        width: 50%;
        border: solid $accent;
    }
    EditClient {
        width: 50%;
        border: solid $accent;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Beenden", show=True),
        Binding(
            "ctrl+n", "new_client", description="Neue*n Klient*in anlegen", show=True
        ),
        Binding("ctrl+f", "fill_forms", "Formulare ausfüllen", show=True),
        Binding("n", "sort_by_last_name", "Sortieren nach `last_name_encr`", show=True),
        Binding("s", "sort_by_school", "Sortieren nach `schule`", show=True),
        Binding("i", "sort_by_client_id", "Sortieren nach `client_id`", show=True),
        Binding("c", "sort_by_class_name", "Sortieren nach `class_name`", show=True),
        Binding("ctrl+r", "reload", "Neu laden", show=True),
    ]

    def __init__(
        self,
        manager: ClientsManager,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.manager = manager
        self.is_busy = False
        self.nta_nos = nta_nos
        self.schools = schools
        self.columns = columns

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            yield ClientsOverview(
                self.manager,
                nta_nos=self.nta_nos,
                schools=self.schools,
                columns=self.columns,
            )
            yield EditClient()
        yield Footer()
        yield LoadingIndicator(id="main-loading-indicator")

    def on_mount(self) -> None:
        self.query_one("#main-loading-indicator", LoadingIndicator).display = False

    @work(exclusive=True, thread=True)
    def get_client_data(self, client_id: int) -> None:
        """Get decrypted client data and post a message with the result."""
        try:
            data = self.manager.get_decrypted_client(client_id)
            self.post_message(self._ClientDataResult(client_id, data))
        except Exception as e:
            self.post_message(self._ClientDataResult(client_id, None, error=e))

    @work(exclusive=True, thread=True)
    def save_client_data(self, client_id: int | None, data: dict[str, Any]) -> None:
        """Save client data and post a message with the result."""
        try:
            saved_client_id = client_id
            if client_id is not None:
                self.manager.edit_client(client_ids=[client_id], new_data=data)
            else:
                saved_client_id = self.manager.add_client(**data)

            if saved_client_id is not None:
                full_client_data = self.manager.get_decrypted_client(saved_client_id)
                self.post_message(
                    self._ClientDataSaveResult(
                        client_id=saved_client_id, client_data=full_client_data
                    )
                )
            else:
                self.post_message(self._ClientDataSaveResult())

        except Exception as e:
            self.post_message(self._ClientDataSaveResult(error=e))

    @work(exclusive=True, thread=True)
    def fill_forms_worker(self, client_id: int, form_paths: list[str]) -> None:
        """Worker to fill forms."""
        try:
            from edupsyadmin.api.add_convenience_data import add_convenience_data

            client_data = self.manager.get_decrypted_client(client_id)
            client_data_with_convenience = add_convenience_data(client_data)
            fill_form(client_data_with_convenience, form_paths)
            self.post_message(self._FormsFilledResult())
        except Exception as e:
            self.post_message(self._FormsFilledResult(error=e))

    async def on_clients_overview_client_selected(
        self, message: ClientsOverview.ClientSelected
    ) -> None:
        """Handle the client selection message."""
        if self.is_busy:
            self.notify(
                BUSY_MSG,
                severity="warning",
            )
            return

        self.is_busy = True
        self.query_one(ClientsOverview).disabled = True
        loading_indicator = self.query_one("#main-loading-indicator", LoadingIndicator)
        loading_indicator.display = True

        self.get_client_data(message.client_id)

    def on_edupsyadmin_tui__client_data_result(
        self, message: _ClientDataResult
    ) -> None:
        """Handle the result of getting client data."""
        loading_indicator = self.query_one("#main-loading-indicator", LoadingIndicator)
        loading_indicator.display = False
        self.is_busy = False
        self.query_one(ClientsOverview).disabled = False

        if message.error:
            self.notify(
                f"Fehler beim Laden der Klient*innen-Daten: {message.error}",
                severity="error",
            )
        else:
            edit_client_widget = self.query_one(EditClient)
            edit_client_widget.update_client(
                client_id=message.client_id, data=message.client_data
            )

    async def on_edit_client_save_client(self, message: EditClient.SaveClient) -> None:
        if self.is_busy:
            self.notify(
                BUSY_MSG,
                severity="warning",
            )
            return

        self.is_busy = True
        self.query_one(ClientsOverview).disabled = True
        self.query_one(EditClient).disabled = True
        loading_indicator = self.query_one("#main-loading-indicator", LoadingIndicator)
        loading_indicator.display = True
        self.notify("Speichere Daten...")

        self.save_client_data(message.client_id, message.data)

    def on_edupsyadmin_tui__client_data_save_result(
        self, message: _ClientDataSaveResult
    ) -> None:
        """Handle the result of saving client data."""
        loading_indicator = self.query_one("#main-loading-indicator", LoadingIndicator)
        loading_indicator.display = False
        self.is_busy = False
        self.query_one(ClientsOverview).disabled = False
        self.query_one(EditClient).disabled = False

        if message.error:
            self.notify(
                f"Fehler beim Speichern der Daten: {message.error}", severity="error"
            )
        else:
            overview_widget = self.query_one(ClientsOverview)
            overview_widget.action_reload()

            edit_client_widget = self.query_one(EditClient)
            if message.client_id is not None and message.client_data is not None:
                edit_client_widget.update_client(message.client_id, message.client_data)
            else:
                edit_client_widget.update_client(None, {})
            self.notify("Daten erfolgreich gespeichert.", severity="information")

    async def on_edit_client_cancel_edit(self, message: EditClient.CancelEdit) -> None:
        if self.is_busy:
            return

        edit_client_widget = self.query_one(EditClient)
        edit_client_widget.update_client(None, {})
        self.notify("Bearbeitung abgebrochen.", severity="information")

    async def on_fill_form_start_fill(self, message: FillForm.StartFill) -> None:
        """Handle the start fill message from the FillForm widget."""
        if self.is_busy:
            self.notify(BUSY_MSG, severity="warning")
            return
        self.is_busy = True
        self.query_one("#main-loading-indicator").display = True
        self.notify("Fülle Formulare aus...")
        self.fill_forms_worker(message.client_ids, message.form_paths)

    async def on_fill_form_cancel(self, message: FillForm.Cancel) -> None:
        """Handle the cancel message from the FillForm widget."""
        self.pop_screen()

    def on_edupsyadmin_tui__forms_filled_result(
        self, message: _FormsFilledResult
    ) -> None:
        """Handle the result of filling forms."""
        self.query_one("#main-loading-indicator").display = False
        self.is_busy = False
        self.pop_screen()
        if message.error:
            self.notify(
                f"Fehler beim Ausfüllen der Formulare: {message.error}",
                severity="error",
            )
        else:
            self.notify("Formulare erfolgreich ausgefüllt.", severity="information")

    def action_new_client(self) -> None:
        """Action to create a new client."""
        if self.is_busy:
            self.notify(
                BUSY_MSG,
                severity="warning",
            )
            return

        edit_client_widget = self.query_one(EditClient)
        edit_client_widget.update_client(client_id=None, data=None)

    def action_fill_forms(self) -> None:
        """Action to show the fill forms screen for the selected client."""
        if self.is_busy:
            self.notify(BUSY_MSG, severity="warning")
            return

        client_id = self.query_one(EditClient).client_id
        if client_id is None:
            self.notify("Bitte zuerst eine*n Klient*in auswählen.", severity="warning")
            return

        self.push_screen(FillFormScreen(self.manager, client_id))

    def action_reload(self) -> None:
        """Reloads the data in the table from the database."""
        self.query_one(ClientsOverview).action_reload()

    def action_sort_by_client_id(self) -> None:
        """Sort DataTable by client_id"""
        self.query_one(ClientsOverview).action_sort_by_client_id()

    def action_sort_by_last_name(self) -> None:
        """Sort DataTable by last name"""
        self.query_one(ClientsOverview).action_sort_by_last_name()

    def action_sort_by_school(self) -> None:
        """Sort DataTable by school and last name"""
        self.query_one(ClientsOverview).action_sort_by_school()

    def action_sort_by_class_name(self) -> None:
        """Sort DataTable by class_name and last name"""
        self.query_one(ClientsOverview).action_sort_by_class_name()

    class _ClientDataResult(Message):
        def __init__(
            self,
            client_id: int,
            client_data: dict[str, Any] | None,
            error: Exception | None = None,
        ) -> None:
            self.client_id = client_id
            self.client_data = client_data
            self.error = error
            super().__init__()

    class _ClientDataSaveResult(Message):
        def __init__(
            self,
            client_id: int | None = None,
            client_data: dict[str, Any] | None = None,
            error: Exception | None = None,
        ) -> None:
            self.client_id = client_id
            self.client_data = client_data
            self.error = error
            super().__init__()

    class _FormsFilledResult(Message):
        def __init__(self, error: Exception | None = None) -> None:
            self.error = error
            super().__init__()
