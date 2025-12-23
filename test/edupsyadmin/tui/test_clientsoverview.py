from unittest.mock import MagicMock

import pandas as pd
from textual.widgets import DataTable

from edupsyadmin.tui.clients_overview_app import ClientsOverviewApp

# Data that the manager is expected to return.
ROWS = [
    (1, "FirstSchool", "abc123", "xyz789", "10A", False, True, "lrst", 50, "key1.a"),
    (2, "FirstSchool", "def456", "uvw345", "9B", True, False, "iRst", 30, "key1.b"),
    (3, "SecondSchool", "ghi789", "rst678", "Ki11", True, True, "lrst", 40, "key2.b"),
    (4, "FirstSchool", "jkl012", "opq123", "10A", False, False, None, 200, "key3.b"),
    (5, "FirstSchool", "bno345", "amn456", "8E", True, False, "iLst", 60, "key1.a.b"),
    (6, "SecondSchool", "pqr678", "ijk789", "Ki10", False, True, "lrst", 70, "key1.a"),
    (7, "SecondSchool", "stu901", "ghi012", "Ki10", True, True, "iRst", 400, "key7"),
    (8, "SecondSchool", "awx234", "efg345", "EV9", False, False, None, 10, "key8"),
    (9, "FirstSchool", "yzb567", "abc678", "11I", True, True, "iLst", 510, "key9.a"),
]
COLUMNS = [
    "client_id",
    "school",
    "first_name_encr",
    "last_name_encr",
    "class_name",
    "notenschutz",
    "nachteilsausgleich",
    "lrst_diagnosis",
    "min_sessions",
    "keyword_taet_encr",
]


def test_clients_overview(snap_compare) -> None:
    """Test that the clients overview table is correctly populated."""
    mock_manager = MagicMock()
    df = pd.DataFrame(ROWS, columns=COLUMNS)
    # The manager's method is called in a worker thread in on_mount
    mock_manager.get_clients_overview.return_value = df

    app = ClientsOverviewApp(clients_manager=mock_manager)

    async def run_before(pilot):
        # Wait for the table to be populated
        await pilot.pause()
        table = pilot.app.query_one(DataTable)

        # Wait until loading is false
        while table.loading:
            await pilot.pause()

        assert table.row_count == len(ROWS)

    assert snap_compare(app, run_before=run_before, terminal_size=(150, 30))
