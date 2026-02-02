from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header, LoadingIndicator

from edupsyadmin.api.managers import ClientNotFoundError
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
        client_ids: list[int],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.clients_manager = clients_manager
        self.client_ids = client_ids

    def compose(self) -> ComposeResult:
        yield Header()
        yield FillForm()
        yield Footer()
        yield LoadingIndicator()

    def on_mount(self) -> None:
        self.query_one(LoadingIndicator).display = False
        fill_form_widget = self.query_one(FillForm)

        # Load all clients with error handling
        clients_data = {}
        failed_ids = []

        for client_id in self.client_ids:
            try:
                clients_data[client_id] = self.clients_manager.get_decrypted_client(
                    client_id
                )
            except ClientNotFoundError:
                failed_ids.append(client_id)

        if failed_ids:
            self.notify(
                f"Warning: Could not find clients with IDs: {', '.join(map(str, failed_ids))}",
                severity="warning",
            )

        if not clients_data:
            self.notify("No valid clients found", severity="error")
            self.exit()
            return

        fill_form_widget.update_clients(clients_data)

    @work(exclusive=True, thread=True)
    def fill_forms_worker(self, client_ids: list[int], form_paths: list[str]) -> None:
        """Worker to fill forms for multiple clients."""
        from edupsyadmin.api.add_convenience_data import add_convenience_data
        from edupsyadmin.api.fill_form import fill_form

        success_count = 0
        failed_clients = []
        error_messages = []

        try:
            for client_id in client_ids:
                try:
                    client_data = self.clients_manager.get_decrypted_client(client_id)
                    client_data_with_convenience = add_convenience_data(client_data)
                    fill_form(client_data_with_convenience, form_paths)
                    success_count += 1
                except ClientNotFoundError:
                    failed_clients.append(client_id)
                    error_messages.append(f"Client {client_id} not found")
                except Exception as e:
                    failed_clients.append(client_id)
                    error_messages.append(f"Client {client_id}: {e!s}")

            # Build final notification message
            if success_count > 0 and not failed_clients:
                msg = f"Forms filled successfully for {success_count} client(s)."
                severity = "information"
            elif success_count > 0 and failed_clients:
                msg = (
                    f"Forms filled for {success_count} client(s). "
                    f"Failed for {len(failed_clients)} client(s): "
                    f"{', '.join(map(str, failed_clients))}"
                )
                severity = "warning"
            else:
                msg = "Failed to fill forms for all clients. Errors:\n" + "\n".join(
                    error_messages
                )
                severity = "error"

            self.call_from_thread(self.notify, msg, severity=severity)

        except Exception as e:
            self.call_from_thread(
                self.notify, f"Critical error filling forms: {e}", severity="error"
            )
        finally:
            self.call_from_thread(self.exit)

    async def on_fill_form_start_fill(self, message: FillForm.StartFill) -> None:
        """Handle the start fill message from the FillForm widget."""
        self.query_one(LoadingIndicator).display = True
        self.query_one(FillForm).disabled = True
        self.fill_forms_worker(message.client_ids, message.form_paths)

    async def on_fill_form_cancel(self, message: FillForm.Cancel) -> None:
        """Handle the cancel message from the FillForm widget."""
        self.exit()
