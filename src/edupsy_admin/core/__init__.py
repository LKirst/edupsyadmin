"""Core implementation package.

"""

import os

os.chdir("projects3/edupsy_admin")

from utils_sql import get_sql_con, TEST_DB
from create_tbl_names import names_tbl
from create_tbl_task import tasks_tbl


if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

con = get_sql_con()
names_tbl(con, "tests/testcsv.csv")
tasks_tbl(con, "tests/testcsv.csv")
con.close()
