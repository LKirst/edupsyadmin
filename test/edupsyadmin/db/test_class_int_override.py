from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.db.clients import Client


@pytest.fixture(autouse=True)
def setup_encryption(mock_config, mock_keyring):
    from cryptography.fernet import Fernet

    from edupsyadmin.core.encrypt import encr

    dummy_key = Fernet.generate_key()
    encr.set_keys([dummy_key])


def test_class_int_auto_derivation(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        client = Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="5a",
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=date(2010, 1, 1),
        )
        assert client.class_int_encr == 5
        assert client.class_int_override is False

        session.add(client)
        session.commit()

        session.refresh(client)
        assert client.class_int_encr == 5


def test_class_int_manual_override(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        # Override on creation
        client = Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="Vorklasse",
            class_int_encr=0,
            class_int_override=True,
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=date(2010, 1, 1),
        )
        assert client.class_int_encr == 0
        assert client.class_int_override is True

        session.add(client)
        session.commit()

        session.refresh(client)
        assert client.class_int_encr == 0

        # Change class_name_encr, should NOT affect class_int_encr
        client.class_name_encr = "Vorklasse B"
        session.commit()

        session.refresh(client)
        assert client.class_int_encr == 0


def test_class_int_reset_override(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        client = Client(
            school="test_school",
            gender_encr="m",
            class_name_encr="5a",
            class_int_encr=10,
            class_int_override=True,
            first_name_encr="John",
            last_name_encr="Doe",
            birthday_encr=date(2010, 1, 1),
        )
        session.add(client)
        session.commit()
        assert client.class_int_encr == 10

        # Reset override
        client.class_int_override = False
        session.commit()

        session.refresh(client)
        # Should be recalculated to 5
        assert client.class_int_encr == 5
