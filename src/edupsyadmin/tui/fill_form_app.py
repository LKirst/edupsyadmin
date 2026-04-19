from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header, LoadingIndicator

from edupsyadmin.api.fill_form import batch_fill_forms
from edupsyadmin.api.managers import ClientNotFoundError
from edupsyadmin.tui.fill_form_widget import FillForm

if TYPE_CHECKING:
    from edupsyadmin.api.managers import ClientsManager


class FillFormApp(App[None]):
    """A standalone Textual App to display the FillForm widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Beenden", show=True, priority=True),
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
                    client_id,
                )
            except ClientNotFoundError:
                failed_ids.append(client_id)

        if failed_ids:
            self.notify(
                f"Warning: Could not find clients with IDs: "
                f"{', '.join(map(str, failed_ids))}",
                severity="warning",
            )

        if not clients_data:
            self.notify("No valid clients found", severity="error")
            self.exit()
            return

        fill_form_widget.display_client_info(clients_data)

    @work(exclusive=True, thread=True)
    def fill_forms_worker(
        self,
        client_ids: list[int],
        form_paths: list[str],
        out_dir: str | None = None,
    ) -> None:
        """Worker to fill forms for multiple clients."""
        try:
            results = batch_fill_forms(
                self.clients_manager,
                client_ids,
                form_paths,
                out_dir=Path(out_dir) if out_dir else None,
            )

            success_count = sum(1 for res in results if res["success"])
            failed_clients = [res["client_id"] for res in results if not res["success"]]

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
                error_messages = [
                    str(res["error"]) for res in results if not res["success"]
                ]
                msg = "Failed to fill forms for all clients. Errors:\n" + "\n".join(
                    error_messages,
                )
                severity = "error"

            self.call_from_thread(self.notify, msg, severity=severity)

        except Exception as e:
            self.call_from_thread(
                self.notify,
                f"Critical error filling forms: {e}",
                severity="error",
            )
        finally:
            self.call_from_thread(self.exit)

    async def on_fill_form_start_fill(self, message: FillForm.StartFill) -> None:
        """Handle the start fill message from the FillForm widget."""
        self.query_one(LoadingIndicator).display = True
        self.query_one(FillForm).disabled = True
        self.fill_forms_worker(
            message.client_ids,
            message.form_paths,
            out_dir=message.out_dir,
        )

    async def on_fill_form_cancel(self, message: FillForm.Cancel) -> None:
        """Handle the cancel message from the FillForm widget."""
        self.exit()
