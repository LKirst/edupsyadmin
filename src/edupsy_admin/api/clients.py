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
        sep = " TEXT NOT NULL, "
        client_var_initializers = sep.join(CLIENT_VARIABLES) + sep
        query_string = (
            "CREATE TABLE if not exists clients("
            + client_var_initializers
            + "datetime_created TEXT NOT NULL, "
            + "datetime_lastmodified TEXT NOT NULL, "
            + "id TEXT PRIMARY KEY);"
        )
        self._execute(query_string)

    def _execute(self, query_string, tblinfo=False):
        con = get_sql_con(self.fn)
        cur = con.cursor()
        logger.debug(f"executing: {query_string}")
        cur.execute(query_string)
        tables=cur.fetchall()
        con.commit()
        if tblinfo:
            get_tbl_info("clients", con, cur)
        con.close()
        return tables

    def connect(self, name, add, listc, remove, file):
        raise NotImplementedError()

    def add(self, idcode):
        """Add a client to the clients table."""
        data = dict.fromkeys(CLIENT_VARIABLES)
        for key in data.keys():
            data[key] = input(key + ": ")
        logger.debug('adding client to the database')
        client_key_commaseparated = ", ".join(data.keys())
        client_value_commaseparated = "', '".join(data.values())
        logger.warn("You should use prepared statements here")
        query_string = (
                "INSERT INTO clients ("
                + client_key_commaseparated
                + ", datetime_created, datetime_lastmodified, id) VALUES ('"
                + client_value_commaseparated
                + f"', datetime('now'), datetime('now'), '{idcode}');"
                )
        self._execute(query_string)

    def ls(self):
        """List the clients stored"""
        query_string = "SELECT * FROM clients;"
        print(self._execute(query_string))
        raise NotImplementedError()

    def edit(self, key):
        """Change a value for a client in the clients table."""
        logger.debug('editing client to the database')
        raise NotImplementedError()

    def rm(self):
        raise NotImplementedError()

clients = Clients(DB_PATH)

def manipulate_clients(action, idcode):
    if action=="add":
        clients.add(idcode)
    elif action=="list":
        clients.ls()
    elif action=="edit":
        clients.edit()
    elif action=="remove":
        clients.rm()
    else:
        raise Exception("Please select a valid action!")
