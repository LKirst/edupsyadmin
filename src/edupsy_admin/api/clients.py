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

    def add(
        self, first_name, last_name, birthday, gender, school, street, city, parent
    ):
        """Add a client to the clients table."""
        logger.debug('adding client to the database')
        raise NotImplementedError()

    def edit(
        self, first_name, last_name, birthday, gender, school, street, city, parent
    ):
        """Change a value for a client in the clients table."""
        logger.debug('editing client to the database')
        raise NotImplementedError()

clients = Clients(DB_PATH)
