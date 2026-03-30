from typing import ClassVar

import pandas as pd
from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.message import Message
from textual.widgets import DataTable, Static

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.tui.dialogs import YesNoDialog


def _format_cell(value: str | bool | float | int) -> Text | str | bool | float | int:
    """Format a cell value with colors:
    - NaN → grey
    - True → bold green "True"
    - False → bold red "False"
    """
    if pd.isna(value):
        return Text("—", style="dim")

    if value is True:
        return Text("True", style="bold green")

    if value is False:
        return Text("False", style="bold red")

    return value


class StyledID:
    """A helper to allow numerical sorting and styled rendering of client IDs."""

    def __init__(self, value: int, style: str) -> None:
        self.value = value
        self.style = style

    def __lt__(self, other: object) -> bool:
        if isinstance(other, StyledID):
            return self.value < other.value
        if isinstance(other, int):
            return self.value < other
        return str(self.value) < str(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StyledID):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        return str(self.value) == str(other)

    def __str__(self) -> str:
        return str(self.value)

    def __rich__(self) -> Text:
        return Text(str(self.value), style=self.style)

    def __int__(self) -> int:
        return self.value


class ClientsOverview(Static):
    """A TUI to show clients in a DataTable."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("delete", "request_delete_client", "Löschen"),
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

    class _ClientDeleted(Message):
        """Internal message to signal client was deleted."""

        def __init__(self, error: Exception | None = None) -> None:
            self.error = error
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

    @work(exclusive=True, thread=True)
    def delete_client(self, client_id: int) -> None:
        """Delete client from database."""
        try:
            self.manager.delete_client(client_id)
            self.post_message(self._ClientDeleted())
        except Exception as e:
            self.post_message(self._ClientDeleted(error=e))

    def _setup_table_columns(self, table: DataTable, columns: list[str]) -> None:
        """Sets up the DataTable columns if not already present."""
        if not table.columns:
            for col in columns:
                if col == "case_active":
                    continue
                width = 20 if col in ("first_name_encr", "last_name_encr") else None
                table.add_column(col, key=col, width=width)

    def _add_rows_to_table(self, table: DataTable, df: pd.DataFrame) -> None:
        """Formats and adds rows from the DataFrame to the DataTable."""
        skip_formatting = {"client_id"}
        formatted_rows = []
        for row_tuple in df.itertuples(index=False, name=None):
            row_dict = dict(zip(df.columns, row_tuple, strict=True))
            case_active = row_dict.get("case_active", True)
            client_id_style = "bold green" if case_active else "bold red"

            formatted_row = []
            for col in df.columns:
                if col == "case_active":
                    continue
                val = row_dict[col]
                if col == "client_id":
                    formatted_row.append(StyledID(int(val), style=client_id_style))
                elif col in skip_formatting:
                    formatted_row.append(val)
                else:
                    formatted_row.append(_format_cell(val))
            formatted_rows.append(formatted_row)

        table.add_rows(formatted_rows)

    def on_clients_overview__df_loaded(self, message: _DfLoaded) -> None:
        table = self.query_one(DataTable)
        table.clear()

        df = message.df
        if df.empty:
            table.loading = False
            self.notify("Tabelle neu geladen.")
            return

        self._setup_table_columns(table, list(df.columns))
        self._add_rows_to_table(table, df)

        if self._last_applied_sort[0]:
            table.sort(
                *self._last_applied_sort[0],
                reverse=self._last_applied_sort[1],
            )

        table.loading = False
        self.notify("Tabelle neu geladen.")

    def on_clients_overview__client_deleted(self, message: _ClientDeleted) -> None:
        """Callback for when a client is deleted."""
        if message.error:
            self.notify(f"Fehler beim Löschen: {message.error}", severity="error")
        else:
            self.notify("Klient*in erfolgreich gelöscht.")
            self.action_reload()

    def action_reload(self) -> None:
        """Reloads the data in the table from the database."""
        table = self.query_one(DataTable)
        table.loading = True
        self.get_clients_df()

    def action_request_delete_client(self) -> None:
        """Action to request deleting a client."""
        table = self.query_one(DataTable)
        if table.cursor_row < 0:
            self.notify("No client selected to delete.", severity="warning")
            return

        row_data = table.get_row_at(table.cursor_row)
        client_id_val = row_data[0]
        last_name = row_data[2]
        first_name = row_data[3]

        try:
            client_id = int(client_id_val)
        except ValueError, TypeError:
            self.notify(f"Invalid client_id: {client_id_val}", severity="error")
            return

        def check_delete(delete: bool | None) -> None:
            """Called with the result of the dialog."""
            if delete:
                self.delete_client(client_id)

        self.app.push_screen(
            YesNoDialog(f"Delete client {first_name} {last_name} (ID: {client_id})?"),
            check_delete,
        )

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
            client_id_val = event.data_table.get_row(row_key)[0]
            try:
                client_id = int(client_id_val)
                self.post_message(self.ClientSelected(client_id))
            except ValueError, TypeError:
                self.notify(f"Ungültige client_id: {client_id_val}")

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
        """Sort DataTable by class_name_encr and last name"""
        self._sort_table_by("class_name_encr", "last_name_encr")
