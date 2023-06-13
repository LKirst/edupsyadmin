import pandas as pd

from utils_sql import get_sql_con, get_tbl_info


def names_tbl(con, fn):
    """Create a table of client names."""
    cur = con.cursor()
    cur.execute(
        (
            "CREATE TABLE names("
            "first_name TEXT NOT NULL, "
            "last_name TEXT NOT NULL, "
            "birthday TEXT NOT NULL, "
            "gender TEXT NOT NULL, "
            "school TEXT NOT NULL, "
            "street TEXT NOT NULL, "
            "city TEXT NOT NULL, "
            "parent TEXT NOT NULL, "
            "id TEXT PRIMARY KEY);"
        )
    )
    con.commit()

    get_tbl_info("names", con, cur)
