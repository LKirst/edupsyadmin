from __future__ import annotations

from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DataTable, Static

if TYPE_CHECKING:
    import pandas as pd

    from edupsyadmin.api.managers import ClientsManager


class ClientsOverview(Static):
    """A TUI to show clients in a DataTable."""

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
        self._last_applied_sort: tuple[tuple[str, ...], bool] = ((), False)
        self._reverse_states: dict[str, bool] = {}

    def compose(self) -> ComposeResult:
        yield DataTable(id="clients_overview_table")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.fixed_columns = 1
        table.zebra_stripes = True
        self.action_reload()

    def _get_toggle_reverse_state(self, sort_key: str) -> bool:
        """
        Determine and toggle the reverse state for a given sort key.
        """
        self._reverse_states[sort_key] = not self._reverse_states.get(sort_key, False)
        return self._reverse_states[sort_key]

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

            # Re-apply last applied sort if any
            if self._last_applied_sort[0]:
                table.sort(
                    *self._last_applied_sort[0], reverse=self._last_applied_sort[1]
                )

        table.loading = False
        self.notify("Tabelle neu geladen.")

    def action_reload(self) -> None:
        """Reloads the data in the table from the database."""
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

    def _sort_table_by(self, *column_keys: str) -> None:
        """Sorts the DataTable by the given column keys, toggling direction."""
        table = self.query_one(DataTable)
        # The primary column key is used for toggling state.
        primary_key = column_keys[0]
        reverse_flag = self._get_toggle_reverse_state(primary_key)
        table.sort(*column_keys, reverse=reverse_flag)
        self._last_applied_sort = (column_keys, reverse_flag)

    def action_sort_by_client_id(self) -> None:
        """Sort DataTable by client_id"""
        self._sort_table_by("client_id")

    def action_sort_by_last_name(self) -> None:
        """Sort DataTable by last name"""
        self._sort_table_by("last_name_encr")

    def action_sort_by_school(self) -> None:
        """Sort DataTable by school and last name"""
        self._sort_table_by("school", "last_name_encr")

    def action_sort_by_class_name(self) -> None:
        """Sort DataTable by class_name and last name"""
        self._sort_table_by("class_name", "last_name_encr")
