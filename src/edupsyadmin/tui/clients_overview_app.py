from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.tui.clients_overview import ClientsOverview


class ClientsOverviewApp(App):
    """A standalone Textual App to display the ClientsOverview widget."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Beenden", show=True, priority=True),
    ]

    def __init__(
        self,
        clients_manager: ClientsManager,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | None = None,
        **kwargs,
    ) -> None:
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
