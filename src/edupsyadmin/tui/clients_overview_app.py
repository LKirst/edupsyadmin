from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.tui.clients_overview import ClientsOverview


class ClientsOverviewApp(App):
    """A standalone Textual App to display the ClientsOverview widget."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("n", "sort_by_last_name", "Sortieren nach `last_name_encr`", show=True),
        Binding("s", "sort_by_school", "Sortieren nach `schule`", show=True),
        Binding("i", "sort_by_client_id", "Sortieren nach `client_id`", show=True),
        Binding("c", "sort_by_class_name", "Sortieren nach `class_name`", show=True),
        Binding("ctrl+r", "reload", "Neu laden", show=True),
    ]

    def __init__(
        self,
        clients_manager: ClientsManager,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.clients_manager = clients_manager
        self.nta_nos = nta_nos
        self.schools = schools
        self.columns = columns

    def compose(self) -> ComposeResult:
        yield Header()
        yield ClientsOverview(
            self.clients_manager,
            nta_nos=self.nta_nos,
            schools=self.schools,
            columns=self.columns,
        )
        yield Footer()

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
