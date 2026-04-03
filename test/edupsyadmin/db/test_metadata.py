import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.db.clients import SystemMetadata


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "test_metadata.sqlite"
    db_url = f"sqlite:///{db_path}"
    upgrade_db(db_url)

    engine = create_engine(db_url)
    with Session(engine) as session:
        yield session


def test_system_metadata_crud(db_session):
    # Create
    meta = SystemMetadata(key="test_key", value="some-value")
    db_session.add(meta)
    db_session.commit()

    # Read
    db_session.expire_all()
    retrieved = db_session.get(SystemMetadata, "test_key")
    assert retrieved is not None
    assert retrieved.value == "some-value"

    # Update
    retrieved.value = "new-value"
    db_session.commit()

    db_session.expire_all()
    updated = db_session.get(SystemMetadata, "test_key")
    assert updated.value == "new-value"

    # Delete
    db_session.delete(updated)
    db_session.commit()

    db_session.expire_all()
    deleted = db_session.get(SystemMetadata, "test_key")
    assert deleted is None
