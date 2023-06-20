from ..core.logger import logger
from .utils_sql import get_sql_con, get_tbl_info, DB_PATH

CLIENT_VARIABLES = [
    "first_name",
    "last_name",
    "birthday",
    "gender",
    "school",
    "street",
    "city",
    "parent",
    "telephone"
]


class Clients:
    def __init__(self, fn):
        logger.debug(f"create connection to database at {fn}")
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
        cur.execute(query_string)
        con.commit()

        get_tbl_info("clients", con, cur)

        con.close()

    def connect(self, name, add, listc, remove, file):
        raise NotImplementedError()

    def add(self):
        """Add a client to the clients table."""
        data = dict.fromkeys(CLIENT_VARIABLES)
        for key in data.keys():
            data[key] = input(key + ": ")
        logger.debug('adding client to the database')
        client_key_commaseparated = ", ".join(data.keys())
        client_value_commaseparated = ", ".join(data.values())
        query_string = (
                "INSERT INTO clients ("
                + client_key_commaseparated
                + ") VALUES ("
                + client_value_commaseparated
                + ");"
                )

        con = get_sql_con(self.fn)
        cur = con.cursor()
        cur.execute(query_string)
        con.commit()
        con.close()

    def ls(self):
        raise NotImplementedError()

    def edit(self, key):
        """Change a value for a client in the clients table."""
        logger.debug('editing client to the database')
        raise NotImplementedError()

    def rm(self):
        raise NotImplementedError()

clients = Clients(DB_PATH)

def manipulate_clients(action):
    if action=="add":
        clients.add()
    elif action=="list":
        clients.ls()
    elif action=="edit":
        clients.edit()
    elif action=="remove":
        clients.rm()
    else:
        raise Exception("Please select a valid action!")
