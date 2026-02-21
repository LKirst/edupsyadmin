import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import create_engine, inspect

from edupsyadmin.api.migration import (
    MigrationError,
    re_encrypt_all_data,
    re_encrypt_database,
    upgrade_db,
)
from edupsyadmin.core.encrypt import encr
from edupsyadmin.db.clients import Client


def test_upgrade_db_new_database(tmp_path: Path):
    """Test that upgrade_db creates the schema in a new, empty database."""
    db_path = tmp_path / "new_app.db"
    db_url = f"sqlite:///{db_path}"

    # Run migration
    upgrade_db(db_url)

    # Verify schema
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "clients" in tables
    assert "alembic_version" in tables

    # Check some columns in clients
    columns = {col["name"] for col in inspector.get_columns("clients")}
    assert "client_id" in columns
    assert "first_name_encr" in columns
    assert "datetime_created" in columns


def test_upgrade_db_legacy_database(tmp_path: Path):
    """
    Test that upgrade_db correctly stamps a legacy database that already has
    the 'clients' table but no alembic_version.
    """
    db_path = tmp_path / "legacy_app.db"
    db_url = f"sqlite:///{db_path}"

    # 1. Create a legacy-style database manually (raw sqlite3)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE clients (client_id INTEGER PRIMARY KEY, school TEXT)"
        )
        conn.execute("INSERT INTO clients (school) VALUES ('LegacySchool')")

    # 2. Run migration
    # This should detect 'clients' and 'stamp' it instead of trying to CREATE TABLE
    upgrade_db(db_url)

    # 3. Verify
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "clients" in tables
    assert "alembic_version" in tables

    # Verify data was preserved
    with engine.connect() as conn:
        from sqlalchemy import text

        result = conn.execute(text("SELECT school FROM clients"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == "LegacySchool"


def test_upgrade_db_idempotency(tmp_path: Path):
    """Test that running upgrade_db multiple times is safe."""
    db_path = tmp_path / "idempotent.db"
    db_url = f"sqlite:///{db_path}"

    # Run twice
    upgrade_db(db_url)
    upgrade_db(db_url)

    engine = create_engine(db_url)
    inspector = inspect(engine)
    assert "clients" in inspector.get_table_names()
    assert "alembic_version" in inspector.get_table_names()


class TestMigrationEncryption:
    @pytest.fixture(autouse=True)
    def setup_encr(self):
        """Reset global encr before each test."""
        old_fernet = encr._fernet
        encr._fernet = None
        yield
        encr._fernet = old_fernet

    def test_re_encrypt_database_success(self, clients_manager):
        """Test rotating from old_key to new_key."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()

        # 1. Initialize with old key and add data
        encr.set_keys([old_key])
        with clients_manager.Session() as session:
            client = Client(
                school="FirstSchool",
                gender_encr="m",
                class_name="1a",
                first_name_encr="OldName",
                last_name_encr="OldSurname",
                birthday_encr="2000-01-01",
            )
            session.add(client)
            session.commit()
            client_id = client.client_id

        # 2. Re-encrypt to new key
        with clients_manager.Session() as session:
            re_encrypt_database(session, old_key, new_key)

        # 3. Verify: encr should now only have the new key
        # We can check this by trying to decrypt with only the new key
        encr.set_keys([new_key])
        with clients_manager.Session() as session:
            client = session.get(Client, client_id)
            assert client.first_name_encr == "OldName"

        # And it should FAIL with ONLY the old key if we reset it manually
        encr.set_keys([old_key])
        with clients_manager.Session() as session, pytest.raises(InvalidToken):
            _ = session.get(Client, client_id)

    def test_re_encrypt_all_data_success(self, clients_manager):
        """Test re-encrypting all data with the current primary key."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()

        # 1. Encrypt data with old key
        encr.set_keys([old_key])
        with clients_manager.Session() as session:
            client = Client(
                school="FirstSchool",
                gender_encr="f",
                class_name="2b",
                first_name_encr="Alice",
                last_name_encr="Wonderland",
                birthday_encr="1995-05-05",
            )
            session.add(client)
            session.commit()
            client_id = client.client_id

        # 2. Setup MultiFernet with [new_key, old_key]
        # This is what happens in a real rotation scenario before re_encrypt_all_data
        encr.set_keys([new_key, old_key])

        # 3. Re-encrypt all data
        with clients_manager.Session() as session:
            re_encrypt_all_data(session)

        # 4. Verify: data should now be encrypted with new_key
        # We verify by seeing if it works with ONLY new_key
        encr.set_keys([new_key])
        with clients_manager.Session() as session:
            client = session.get(Client, client_id)
            assert client.first_name_encr == "Alice"

    def test_re_encrypt_all_data_not_initialized(self, clients_manager):
        """Test that re_encrypt_all_data raises error if encr is not initialized."""
        encr._fernet = None
        with (
            clients_manager.Session() as session,
            pytest.raises(MigrationError, match="Encryption is not initialized"),
        ):
            re_encrypt_all_data(session)

    def test_re_encrypt_empty_db(self, clients_manager):
        """Test re-encryption with an empty database."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()
        encr.set_keys([new_key, old_key])

        with clients_manager.Session() as session:
            # Should not raise any error
            re_encrypt_all_data(session)

    def test_re_encrypt_database_validation_failure(self, clients_manager):
        """Test that validation errors during re-encryption are handled."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()
        encr.set_keys([old_key])

        with clients_manager.Session() as session:
            client = Client(
                school="FirstSchool",
                gender_encr="m",
                class_name="1a",
                first_name_encr="Test",
                last_name_encr="User",
                birthday_encr="2000-01-01",
            )
            session.add(client)
            session.commit()

        # Mock getattr to raise ValueError to simulate validation failure
        # (though it's hard to trigger a real validation failure on read-write
        # of same value unless the validator changed or data is corrupt)
        with (
            patch(
                "edupsyadmin.api.migration.getattr", side_effect=ValueError("Bad data")
            ),
            clients_manager.Session() as session,
            pytest.raises(MigrationError, match="Validation failed"),
        ):
            re_encrypt_database(session, old_key, new_key)

    def test_re_encrypt_all_data_commit_failure(self, clients_manager):
        """Test rollback on commit failure."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()
        encr.set_keys([new_key, old_key])

        with clients_manager.Session() as session:
            client = Client(
                school="FirstSchool",
                gender_encr="m",
                class_name="1a",
                first_name_encr="Test",
                last_name_encr="User",
                birthday_encr="2000-01-01",
            )
            session.add(client)
            session.commit()

        with (
            patch.object(session, "commit", side_effect=Exception("DB Error")),
            pytest.raises(MigrationError, match="Data re-encryption failed"),
        ):
            # We need to pass the mocked session or ensure re_encrypt_all_data uses it
            # re_encrypt_all_data takes db_session as argument
            re_encrypt_all_data(session)
