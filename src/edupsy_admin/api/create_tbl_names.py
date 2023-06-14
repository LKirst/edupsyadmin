from edupsy_admin.core import logger
from edupsy_admin.core.utils_sql import get_sql_con, get_tbl_info

CLIENT_VARIABLES = [
    "first_name",
    "last_name",
    "birthday",
    "gender",
    "school",
    "street",
    "city",
    "parent",
]


class Clients:
    def __init__(self, fn):
        self.fn = fn
        con = get_sql_con(self.fn)
        cur = con.cursor()
        sep = " TEXT NOT NULL, "
        client_var_initializers = sep.join(CLIENT_VARIABLES) + sep
        query_string = (
            "CREATE TABLE if not exists clients("
            + client_var_initializers
            + "datetime_created TEXT NOT NULL, "
            + "datetime_lastmodified TEXT NOT NULL, "
            + "id TEXT PRIMARY KEY);"
        )
        cur.execute(
            (
                "first_name TEXT NOT NULL, "
                "last_name TEXT NOT NULL, "
                "birthday TEXT NOT NULL, "
                "gender TEXT NOT NULL, "
                "school TEXT NOT NULL, "
                "street TEXT NOT NULL, "
                "city TEXT NOT NULL, "
                "parent TEXT NOT NULL, "
            )
        )
        con.commit()

        get_tbl_info("clients", con, cur)

        con.close()

    def add_client(
        self, first_name, last_name, birthday, gender, school, street, city, parent
    ):
        """Add a client to the client table."""
        raise NotImplementedError()
