from datetime import date
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import Column, Integer, create_engine, text
from sqlalchemy.orm import Session, declarative_base

from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger as app_logger
from edupsyadmin.db.clients import EncryptedDate, EncryptedInteger, EncryptedString

Base = declarative_base()


class MockModel(Base):
    __tablename__ = "mock_model"
    id = Column(Integer, primary_key=True)
    enc_int = Column(EncryptedInteger)
    enc_date = Column(EncryptedDate)
    enc_str = Column(EncryptedString)


@pytest.fixture
def db_session(tmp_path):
    """
    Provide a clean database session for each test.
    """
    # Setup encryption
    dummy_key = Fernet.generate_key()
    encr.set_keys([dummy_key])

    db_path = tmp_path / "test_types.sqlite"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()


# EncryptedInteger tests


@pytest.mark.parametrize(
    "value",
    [
        123,
        0,
        1,
        -1,
    ],
)
def test_encrypted_integer_roundtrip(db_session, value):
    """Tests that integers encrypt and decrypt correctly through ORM."""
    obj = MockModel(enc_int=value)
    db_session.add(obj)
    db_session.commit()

    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_int == value


def test_encrypted_integer_none(db_session):
    """None values should be handled correctly - encrypted as empty string, not NULL."""
    obj = MockModel(enc_int=None)
    db_session.add(obj)
    db_session.commit()

    # Check that the database column is NOT NULL (it's encrypted empty string)
    result = db_session.execute(
        text(f"SELECT enc_int FROM {MockModel.__tablename__} WHERE id = :id"),
        {"id": obj.id},
    ).fetchone()
    assert result[0] is not None, "Encrypted column should not be NULL in database"

    # Check that the decrypted value is None
    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_int is None


@pytest.mark.parametrize(
    "decrypted_value,expected_error",
    [
        ("not-an-int", "Could not convert decrypted value 'not-an-int' to int"),
        ("12.5", "Could not convert decrypted value '12.5' to int"),
        ("abc123", "Could not convert decrypted value 'abc123' to int"),
    ],
    ids=["text", "float_string", "mixed"],
)
def test_encrypted_integer_invalid_decryption(
    db_session, monkeypatch, decrypted_value, expected_error
):
    """Invalid decrypted data should return None and log error."""
    obj = MockModel(enc_int=123)
    db_session.add(obj)
    db_session.commit()

    # Mock decrypt to return invalid value
    monkeypatch.setattr(encr, "decrypt", lambda x: decrypted_value)

    db_session.expire_all()
    with patch.object(app_logger, "error") as mock_error:
        retrieved = db_session.get(MockModel, obj.id)
        assert retrieved.enc_int is None

        # Multiple columns get decrypted, so check that our error is in the calls
        assert mock_error.call_count >= 1
        error_messages = [str(call.args[0]) for call in mock_error.call_args_list]
        assert any(expected_error in msg for msg in error_messages), (
            f"Expected error '{expected_error}' not found in {error_messages}"
        )


# EncryptedDate


def test_encrypted_date_roundtrip(db_session):
    """Test that dates encrypt and decrypt correctly through ORM."""
    test_date = date(2026, 4, 4)
    obj = MockModel(enc_date=test_date)
    db_session.add(obj)
    db_session.commit()

    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_date == test_date


def test_encrypted_date_none(db_session):
    """None values should be handled correctly - encrypted as empty string, not NULL."""
    obj = MockModel(enc_date=None)
    db_session.add(obj)
    db_session.commit()

    # Check that the database column is NOT NULL (it's encrypted empty string)
    result = db_session.execute(
        text(f"SELECT enc_date FROM {MockModel.__tablename__} WHERE id = :id"),
        {"id": obj.id},
    ).fetchone()
    assert result[0] is not None, "Encrypted column should not be NULL in database"

    # Check that the decrypted value is None
    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_date is None


@pytest.mark.parametrize(
    "decrypted_value,expected_error",
    [
        ("not-a-date", "Could not convert decrypted value 'not-a-date' to date"),
        ("2023-13-01", "Could not convert decrypted value '2023-13-01' to date"),
        ("2023/05/20", "Could not convert decrypted value '2023/05/20' to date"),
        ("20-05-2023", "Could not convert decrypted value '20-05-2023' to date"),
    ],
    ids=["text", "invalid_month", "wrong_separator", "wrong_format"],
)
def test_encrypted_date_invalid_decryption(
    db_session, monkeypatch, decrypted_value, expected_error
):
    """Invalid decrypted data should return None and log error."""
    test_date = date(2023, 5, 20)
    obj = MockModel(enc_date=test_date)
    db_session.add(obj)
    db_session.commit()

    # Mock decrypt to return invalid value
    monkeypatch.setattr(encr, "decrypt", lambda x: decrypted_value)

    db_session.expire_all()
    with patch.object(app_logger, "error") as mock_error:
        retrieved = db_session.get(MockModel, obj.id)
        assert retrieved.enc_date is None

        # Multiple columns get decrypted, so check that our error is in the calls
        assert mock_error.call_count >= 1
        error_messages = [str(call.args[0]) for call in mock_error.call_args_list]
        assert any(expected_error in msg for msg in error_messages), (
            f"Expected error '{expected_error}' not found in {error_messages}"
        )


# EncryptedString tests


@pytest.mark.parametrize(
    "value",
    [
        "Hello, World!",
        "",  # empty string
        "Äöü",  # unicode
        "a" * 1000,  # long string
        "line1\nline2",  # multiline
        "tab\there",  # special chars
        "  spaces  ",  # whitespace
    ],
)
def test_encrypted_string_roundtrip(db_session, value):
    """Test that strings encrypt and decrypt correctly through ORM."""
    obj = MockModel(enc_str=value)
    db_session.add(obj)
    db_session.commit()

    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_str == value


def test_encrypted_string_none(db_session):
    """None should be converted to empty string per implementation."""
    obj = MockModel(enc_str=None)
    db_session.add(obj)
    db_session.commit()

    # Check that the database column is NOT NULL (it's encrypted empty string)
    result = db_session.execute(
        text(f"SELECT enc_str FROM {MockModel.__tablename__} WHERE id = :id"),
        {"id": obj.id},
    ).fetchone()
    assert result[0] is not None, "Encrypted column should not be NULL in database"

    # Check that the decrypted value is None
    db_session.expire_all()
    retrieved = db_session.get(MockModel, obj.id)
    assert retrieved.enc_str == ""
