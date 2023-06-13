import os
import sqlite3
import pprint

TEST_DB = "tests/testdb.sqlite"


def get_sql_con(fn: str = TEST_DB):
    print(f"Cwd: {os.getcwd()}")
    try:
        con = sqlite3.connect(fn)
        print(f"Connected to the db {fn}")
        return con
    except sqlite.Error as e:
        print(e)


def get_tbl_info(tbl_name: str, con, cur):
    res = con.execute(f"PRAGMA table_info({tbl_name});")
    colnames = [tuple([i[0] for i in res.description])]
    print(f"### cols descr for {tbl_name} ###")
    pprint.pprint(colnames + res.fetchall())

    cur.execute(f"SELECT * FROM {tbl_name}")
    print("### rows descr for {tbl_name} ###")
    print(f"Nrows:{len(cur.fetchall())}")
