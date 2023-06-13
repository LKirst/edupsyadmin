import os
import sqlite3
import pprint

DB_PATH = "temporary_db_for_testing.sqlite"


def get_sql_con(fn: str = DB_PATH):
    print(f"Cwd: {os.getcwd()}")
    try:
        con = sqlite3.connect(fn)
        print(f"Connected to the db {fn}")
        return con
    except sqlite3.Error as e:
        print(e)


def get_tbl_info(tbl_name: str, con, cur):
    res = con.execute(f"PRAGMA table_info({tbl_name});")
    colnames = [tuple([i[0] for i in res.description])]
    print(f"\n### Columns description for the table '{tbl_name}' ###")
    pprint.pprint(colnames + res.fetchall())

    cur.execute(f"SELECT * FROM {tbl_name}")
    print(f"\n### Rows description for the table '{tbl_name}' ###")
    print(f"Nrows:{len(cur.fetchall())}")
