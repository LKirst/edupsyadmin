from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.db.clients import Client


@pytest.fixture(autouse=True)
def setup_encryption(mock_config, mock_keyring):
    from cryptography.fernet import Fernet

    from edupsyadmin.core.encrypt import encr

    # initialize encr with a dummy key for testing
    dummy_key = Fernet.generate_key()
    encr.set_keys([dummy_key])


def test_client_birthday_required():
    # Missing birthday should raise ValueError
    with pytest.raises(ValueError, match=r"Das Geburtsdatum ist ein Pflichtfeld."):
        Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="1a",
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=None,  # type: ignore
        )


def test_optional_dates_none_stored_as_encrypted_empty_string(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        client = Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="1a",
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=date(2010, 1, 1),
            entry_date_encr=None,
        )
        session.add(client)
        session.commit()

        client_id = client.client_id

        # Verify raw value in DB is NOT NULL and is encrypted (not empty string)
        # In SQLite, we check if the column has a value.
        row = session.execute(text("SELECT entry_date_encr FROM clients")).fetchone()
        assert row is not None
        assert row[0] is not None
        assert len(row[0]) > 0
        assert row[0] != ""

        # Now verify that when read back through the model, it is None
        session.expunge_all()  # Clear session cache
        client_db = session.get(Client, client_id)
        assert client_db is not None
        assert client_db.entry_date_encr is None


def test_empty_string_handled_as_none_for_dates(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        client = Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="1a",
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=date(2010, 1, 1),
            entry_date_encr="",
        )
        assert client.entry_date_encr is None

        session.add(client)
        session.commit()

        client_id = client.client_id

        session.expunge_all()
        client_db = session.get(Client, client_id)
        assert client_db is not None
        assert client_db.entry_date_encr is None


def test_to_bool_or_none():
    from edupsyadmin.db.clients import to_bool_or_none

    assert to_bool_or_none(True) is True
    assert to_bool_or_none(False) is False
    assert to_bool_or_none("1") is True
    assert to_bool_or_none("0") is False
    assert to_bool_or_none("true") is True
    assert to_bool_or_none("FALSE") is False
    assert to_bool_or_none(1) is True
    assert to_bool_or_none(0) is False
    assert to_bool_or_none(None) is None
    assert to_bool_or_none("") is None
    assert to_bool_or_none("  ") is None

    with pytest.raises(ValueError, match="cannot be converted to a boolean"):
        to_bool_or_none("abc")
    with pytest.raises(ValueError, match="cannot be converted to a boolean"):
        to_bool_or_none(2)
    with pytest.raises(TypeError):
        to_bool_or_none([])  # ty: ignore[invalid-argument-type]


def test_to_int_or_none():
    from edupsyadmin.db.clients import to_int_or_none

    assert to_int_or_none(123) == 123
    assert to_int_or_none("456") == 456
    assert to_int_or_none(None) is None
    assert to_int_or_none("") is None
    assert to_int_or_none("  ") is None

    with pytest.raises(ValueError, match="cannot be converted to an integer"):
        to_int_or_none("abc")
    with pytest.raises(TypeError):
        to_int_or_none([])  # ty: ignore[invalid-argument-type]


def test_to_date_or_none():
    from edupsyadmin.db.clients import to_date_or_none

    test_date = date(2023, 1, 1)
    assert to_date_or_none(test_date) == test_date
    assert to_date_or_none("2023-01-01") == test_date
    assert to_date_or_none(None) is None
    assert to_date_or_none("") is None
    assert to_date_or_none("  ") is None

    with pytest.raises(ValueError, match="Invalid date format"):
        to_date_or_none("01.01.2023")
    with pytest.raises(TypeError):
        to_date_or_none(123)  # ty: ignore[invalid-argument-type]
