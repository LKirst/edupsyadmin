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
