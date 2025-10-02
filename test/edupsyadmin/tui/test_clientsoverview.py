from edupsyadmin.tui.clientsoverview import ClientsOverview

ROWS = [
    (
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
    ),
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


def test_clients_overview(snap_compare) -> None:
    app = ClientsOverview(data=ROWS)
    assert snap_compare(app, terminal_size=(150, 30))
