from ..core.logger import logger
from ..core.encrypt import Encryption
from .utils_sql import get_sql_con, get_tbl_info, DB_PATH

CLIENT_VARIABLES_ENCRYPTED = [
        "first_name",
        "last_name",
        "birthday",
        "street",
        "city",
        "parent",
        "telephone",
        "email",
        "gender",
        "notes"
        ]
CLIENT_VARIABLES_UNENCRYPTED = [
        "school",
        "date_ofgraduation"
        ]
CLIENT_VARIABLES_AUTOMATIC = [
        "datetime_created",
        "datetime_lastmodified",
        ]
CLIENT_VARIABLES_ALL = (
        CLIENT_VARIABLES_ENCRYPTED +
        CLIENT_VARIABLES_UNENCRYPTED +
        CLIENT_VARIABLES_AUTOMATIC)

class Clients:

    def __init__(self, fn):
        logger.debug(f"create connection to database at {fn}")
        self.fn = fn
        self.encryption=Encryption()
        sep = " TEXT NOT NULL, "
        client_var_initializers = sep.join(CLIENT_VARIABLES_ALL) + sep
        query_string = (
            "CREATE TABLE if not exists clients("
            + client_var_initializers
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
        data = dict.fromkeys(CLIENT_VARIABLES_ALL)
        for key in data.keys():
            inp = input(key + ": ")
            if key in CLIENT_VARIABLES_ENCRYPTED:
                data[key]=self.encryption.encrypt(inp)
            elif key in CLIENT_VARIABLES_AUTOMATIC:
                data[key]=inp

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
