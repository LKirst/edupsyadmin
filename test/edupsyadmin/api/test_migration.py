import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, inspect

from edupsyadmin.api.migration import (
    MigrationError,
    re_encrypt_all_data,
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
    assert "system_metadata" in tables

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
    # The columns must match what the initial migration (4087c43f0c7c) expects.
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE clients (
                client_id INTEGER PRIMARY KEY,
                school TEXT,
                entry_date DATE,
                estimated_graduation_date DATE,
                document_shredding_date DATE,
                class_name TEXT,
                class_int INTEGER,
                first_name_encr TEXT NOT NULL DEFAULT '',
                last_name_encr TEXT NOT NULL DEFAULT '',
                gender_encr TEXT NOT NULL DEFAULT '',
                birthday_encr TEXT NOT NULL DEFAULT '',
                street_encr TEXT NOT NULL DEFAULT '',
                city_encr TEXT NOT NULL DEFAULT '',
                parent_encr TEXT NOT NULL DEFAULT '',
                telephone1_encr TEXT NOT NULL DEFAULT '',
                telephone2_encr TEXT NOT NULL DEFAULT '',
                email_encr TEXT NOT NULL DEFAULT '',
                notes_encr TEXT NOT NULL DEFAULT '',
                keyword_taet_encr TEXT NOT NULL DEFAULT '',
                lrst_diagnosis_encr TEXT NOT NULL DEFAULT '',
                lrst_last_test_date_encr TEXT NOT NULL DEFAULT '',
                lrst_last_test_by_encr TEXT NOT NULL DEFAULT '',
                datetime_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                datetime_lastmodified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notenschutz BOOLEAN NOT NULL DEFAULT 0,
                nos_rs BOOLEAN NOT NULL DEFAULT 0,
                nos_rs_ausn BOOLEAN NOT NULL DEFAULT 0,
                nos_les BOOLEAN NOT NULL DEFAULT 0,
                nos_other BOOLEAN NOT NULL DEFAULT 0,
                nachteilsausgleich BOOLEAN NOT NULL DEFAULT 0,
                nta_zeitv BOOLEAN NOT NULL DEFAULT 0,
                nta_font BOOLEAN NOT NULL DEFAULT 0,
                nta_aufg BOOLEAN NOT NULL DEFAULT 0,
                nta_struktur BOOLEAN NOT NULL DEFAULT 0,
                nta_arbeitsm BOOLEAN NOT NULL DEFAULT 0,
                nta_ersgew BOOLEAN NOT NULL DEFAULT 0,
                nta_vorlesen BOOLEAN NOT NULL DEFAULT 0,
                nta_other BOOLEAN NOT NULL DEFAULT 0,
                nta_nos_end BOOLEAN NOT NULL DEFAULT 0,
                min_sessions INTEGER NOT NULL DEFAULT 45,
                n_sessions INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute("INSERT INTO clients (school) VALUES ('LegacySchool')")

    # 2. Initialize encryption with a dummy key for migrations that need it
    from cryptography.fernet import Fernet

    from edupsyadmin.core.encrypt import encr

    encr.set_keys([Fernet.generate_key()])

    # 3. Run migration
    # This should detect 'clients' and 'stamp' it instead of trying to CREATE TABLE
    upgrade_db(db_url)

    # 3. Verify
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "clients" in tables
    assert "alembic_version" in tables
    assert "system_metadata" in tables

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
                class_name_encr="2b",
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

    def test_re_encrypt_all_data_commit_failure(self, clients_manager):
        """Test rollback on commit failure."""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()
        encr.set_keys([new_key, old_key])

        with clients_manager.Session() as session:
            client = Client(
                school="FirstSchool",
                gender_encr="m",
                class_name_encr="1a",
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
