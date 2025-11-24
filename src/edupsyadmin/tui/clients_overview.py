from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable, Static

if TYPE_CHECKING:
    import pandas as pd

    from edupsyadmin.api.managers import ClientsManager


class ClientsOverview(Static):
    """A TUI to show clients in a DataTable."""

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("n", "sort_by_last_name", "Sortieren nach `last_name_encr`"),
        Binding("s", "sort_by_school", "Sortieren nach `schule`"),
        Binding("i", "sort_by_client_id", "Sortieren nach `client_id`"),
        Binding("c", "sort_by_class_name", "Sortieren nach `class_name`"),
        Binding("ctrl+r", "reload", "Neu laden", show=True),
    ]

    class ClientSelected(Message):
        """Message to indicate a client has been selected."""

        def __init__(self, client_id: int) -> None:
            self.client_id = client_id
            super().__init__()

    class _DfLoaded(Message):
        """Internal message to signal dataframe is loaded."""

        def __init__(self, df: pd.DataFrame) -> None:
            self.df = df
            super().__init__()

    def __init__(
        self,
        manager: ClientsManager,
        nta_nos: bool = False,
        schools: list[str] | None = None,
        columns: list[str] | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.manager = manager
        self.nta_nos = nta_nos
        self.schools = schools
        self.columns = columns
        self.current_sorts: set[str] = set()

    def compose(self) -> ComposeResult:
        yield DataTable(id="clients_overview_table")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.fixed_columns = 1
        table.zebra_stripes = True
        self.action_reload()

    def sort_reverse(self, sort_type: str) -> bool:
        """
        Determine if `sort_type` is ascending or descending.
        """
        reverse = sort_type in self.current_sorts
        if reverse:
            self.current_sorts.remove(sort_type)
        else:
            self.current_sorts.add(sort_type)
        return reverse

    @work(exclusive=True, thread=True)
    def get_clients_df(self) -> None:
        """Get clients overview as a pandas DataFrame."""
        df = self.manager.get_clients_overview(
            nta_nos=self.nta_nos, schools=self.schools, columns=self.columns
        )
        self.post_message(self._DfLoaded(df))

    def on_clients_overview__df_loaded(self, message: _DfLoaded) -> None:
        """Callback for when the client dataframe is loaded."""
        table = self.query_one(DataTable)
        df = message.df
        if not df.empty:
            if not table.columns:
                for col in df.columns:
                    table.add_column(col, key=col)
            table.add_rows(df.values.tolist())

        table.loading = False
        self.notify("Tabelle neu geladen.")

    def action_reload(self) -> None:
        """Reloads the data in the table from the database."""
        self.notify("Lade Daten neu...")
        table = self.query_one(DataTable)
        table.loading = True
        table.clear()
        self.get_clients_df()

    @on(DataTable.RowSelected, "#clients_overview_table")
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection."""
        if getattr(self.app, "is_busy", False):
            self.notify(
                "Beschäftigt. Bitte warten, bis der vorherige "
                "Vorgang abgeschlossen ist."
            )
            return
        row_key = event.row_key
        if row_key is not None:
            client_id_str = event.data_table.get_row(row_key)[0]
            try:
                client_id = int(client_id_str)
                self.post_message(self.ClientSelected(client_id))
            except (ValueError, TypeError):
                self.notify(f"Ungültige client_id: {client_id_str}")

    def action_sort_by_client_id(self) -> None:
        """Sort DataTable by client_id"""
        table = self.query_one(DataTable)
        table.sort(
            "client_id",
            reverse=self.sort_reverse("client_id"),
        )

    def action_sort_by_last_name(self) -> None:
        """Sort DataTable by last name"""
        table = self.query_one(DataTable)
        table.sort(
            "last_name_encr",
            reverse=self.sort_reverse("last_name_encr"),
        )

    def action_sort_by_school(self) -> None:
        """Sort DataTable by school and last name"""
        table = self.query_one(DataTable)
        table.sort(
            "school",
            "last_name_encr",
            reverse=self.sort_reverse("school"),
        )

    def action_sort_by_class_name(self) -> None:
        """Sort DataTable by class_name and last name"""
        table = self.query_one(DataTable)
        table.sort(
            "class_name",
            "last_name_encr",
            reverse=self.sort_reverse("class_name"),
        )
