import datetime

import pytest
from sqlalchemy import (
    JSON,
    VARCHAR,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)

from edupsyadmin.db.clients import EncryptedString
from edupsyadmin.utils.python_type import get_python_type


def test_get_python_type_basic():
    """Test get_python_type with basic SQLAlchemy types."""
    assert get_python_type(Integer()) is int
    assert get_python_type(String()) is str
    assert get_python_type(VARCHAR()) is str
    assert get_python_type(Float()) is float
    assert get_python_type(Date()) is datetime.date
    assert get_python_type(DateTime()) is datetime.datetime
    assert get_python_type(Boolean()) is bool


def test_get_python_type_decorated():
    """Test get_python_type with a TypeDecorator."""
    assert get_python_type(EncryptedString()) is str


def test_get_python_type_unsupported():
    """Test that get_python_type raises ValueError for an unsupported type."""
    with pytest.raises(ValueError):
        get_python_type(JSON())
