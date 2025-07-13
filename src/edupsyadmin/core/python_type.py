import datetime

from sqlalchemy import VARCHAR, Boolean, Date, DateTime, Float, Integer, String
from sqlalchemy.types import TypeDecorator


def get_python_type(sqlalchemy_type: type) -> type:
    """
    Maps SQLAlchemy types to Python standard types.

    :param sqlalchemy_type: The SQLAlchemy type to be mapped.
    :return: A string representing the Python standard type.
    """

    if isinstance(sqlalchemy_type, TypeDecorator):
        sqlalchemy_type = sqlalchemy_type.impl

    if isinstance(sqlalchemy_type, Integer):
        return int
    if isinstance(sqlalchemy_type, String | VARCHAR):
        return str
    if isinstance(sqlalchemy_type, Float):
        return float
    if isinstance(sqlalchemy_type, Date):
        return datetime.date
    if isinstance(sqlalchemy_type, DateTime):
        return datetime.datetime
    if isinstance(sqlalchemy_type, Boolean):
        return bool
    raise ValueError(f"could not match {sqlalchemy_type} to a builtin type")
