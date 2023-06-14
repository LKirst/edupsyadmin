import datetime
from edupsy_admin.core.utils_sql import get_sql_con, get_tbl_info


def lrst_tbl(con, fn):
    """Create a table for tests and questionnaires.

    Parameters
    ----------
    con : _type_
        _description_
    fn : function
        _description_
    """
    query_string = (
        "CREATE TABLE lrst("
        "diagnose text NOT NULL, "
        "na_zeitzuschlag int NOT NULL, "
        "na_aufgabevorlesen bool NOT NULL, "
        "ns_rs bool NOT NULL, "
        "ns_gewichtungmdl bool NOT NULL, "
        "ns_nichtvorlesen bool NOT NULL, "
        "datetime_created text NOT NULL, "
        "datetime_lastmodified text NOT NULL, "
        "client_id TEXT NOT NULL, "
    )
    query_string += "PRIMARY KEY (datetime_created, client_id));"
    cur = con.cursor()
    cur.execute(query_string)
    con.commit()
