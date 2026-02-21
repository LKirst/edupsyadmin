import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, inspect

from edupsyadmin.api.migration import upgrade_db


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
