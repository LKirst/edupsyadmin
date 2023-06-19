import datetime
from .create_tbl_names import get_names
from .utils_sql import get_sql_con, get_tbl_info


def session_tbl(con, fn):
    """Create a table for sessions.

    Parameters
    ----------
    con : _type_
        _description_
    fn : function
        _description_
    """
    names = get_names(fn)
    query_string = (
        "CREATE TABLE session("
        "datetime_session text NOT NULL, "
        "session_type text NOT NULL, "
        "datetime_created text NOT NULL, "
        "datetime_lastmodified text NOT NULL, "
        "session_description text, "
        "client_id TEXT NOT NULL, "
    )
    for _, row in names.iterrows():
        query_string += (
            f"{row['full_name']+'_session INTEGER'}, "
            f"{row['full_name']+'_note TEXT'}, "
        )
    query_string += "PRIMARY KEY (datetime_session, client_id));"
    cur = con.cursor()
    cur.execute(query_string)
    con.commit()


def add_session(con, datetime_session, session_type, session_description, **kwargs):
    """Add a session to the table of sessions.

    Parameters
    ----------
    con : _type_
        _description_
    datetime_session : _type_
        _description_
    session_type : _type_
        _description_
    session_description : _type_
        _description_
    """

    now = datetime.datetime.now()
    now_str = str(now)
    session = {
        "datetime_session": datetime_session,
        "session_type": session_type,
        "datetime_created": now_str,
        "datetime_lastmodified": now_str,
        "session_description": session_description,
    }
    sessions.update(kwargs)

    query_str = "INSERT INTO sessions (" f"{session.keys()[0]}"
    for key in session.keys()[1:]:
        query_str += f", {key}"
    query_str += f") VALUES ({session.values()[0]}"
    for value in session.values()[1:]:
        query_str += f", {value}"
    query_str += ");"

    cur.execute(query_str)
    con.commit()


def edit_session(con, datetime_session, session_type, **kwargs):
    """Edit an existing session in the db of sessions.

    Parameters
    ----------
    con : _type_
        _description_
    datetime_session : _type_
        _description_
    session_type : _type_
        _description_
    """

    now = datetime.datetime.now()
    now_str = str(now)
    kwargs.update({"datetime_lastmodified": now_str})

    cur = con.cursor()
    for key, value in kwargs.items():
        query_st = (
            f"UPDATE sessions "
            f"SET {key}={value}) "
            f"WHERE (datetime_session={datetime_session} "
            f"AND session_type={session_type});"
        )
        cur.execute(query_str)

    con.commit()


def get_sessions(con, columns, date_from, date_to):
    """_summary_

    Parameters
    ----------
    con : _type_
        _description_
    columns : _type_
        _description_
    date_from : _type_
        _description_
    date_to : _type_
        _description_
    order_by : _type_, optional
        _description_, by default None

    Returns
    -------
    _type_
        _description_
    """

    query_str = (
        f"SELECT {columns} FROM sessions "
        "WHERE datetime_session BETWEEN "
        f"{date_from} AND {date_to}"
    )

    cur = con.cursor()
    res = cur.execute(query_str)

    return res.fetchall()
