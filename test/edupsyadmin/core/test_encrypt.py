"""Test suite for the core.encrypt module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

# Import the class, the global instance, and helper functions
from edupsyadmin.core.encrypt import (
    Encryption,
    derive_key_from_password,
    encr,  # The global instance
    get_key_from_keyring,
    load_or_create_salt,
    set_key_in_keyring,
)

# Constants for testing
TEST_UID = "test_uid"
TEST_USER = "test_user"
TEST_PASSWORD = "secure_test_password"


@pytest.fixture(autouse=True)
def reset_global_encr():
    """
    CRITICAL: Resets the global 'encr' instance before and after every test.
    This guarantees that Test A cannot affect Test B.
    """
    # Teardown (reset) before test starts to ensure clean slate
    encr._fernet = None

    yield

    # Teardown (reset) after test ends
    encr._fernet = None


@pytest.fixture
def mock_keyring():
    """
    Mocks the keyring module completely.
    Uses an in-memory dictionary to simulate storage.
    """
    storage = {}

    def mock_set_password(service, username, password):
        storage[f"{service}:{username}"] = password

    def mock_get_credential(service, username):
        key = f"{service}:{username}"
        if key in storage:
            # keyring.get_credential returns an object with a .password attribute
            cred = MagicMock()
            cred.password = storage[key]
            return cred
        return None

    # Patch the keyring module where it is IMPORTED (in edupsyadmin.core.encrypt)
    with patch("edupsyadmin.core.encrypt.keyring") as mock_kr:
        mock_kr.set_password.side_effect = mock_set_password
        mock_kr.get_credential.side_effect = mock_get_credential
        # Mock backend name for logging calls
        mock_kr.get_keyring.return_value.__class__.__name__ = "MockMemoryKeyring"
        yield mock_kr


@pytest.fixture
def generated_key() -> bytes:
    """Returns a valid Fernet key."""
    return Fernet.generate_key()


@pytest.fixture
def temp_salt_file(tmp_path) -> Path:
    """Returns a path to a non-existent salt file in a temp directory."""
    return tmp_path / "salt.txt"


class TestEncryptionUnit:
    """Tests the Encryption class logic in isolation using local instances."""

    def test_init_without_key(self):
        local_encr = Encryption()
        assert not local_encr.is_initialized

        with pytest.raises(RuntimeError, match="Encryption key not set"):
            local_encr.encrypt("test")

    def test_init_with_key(self, generated_key):
        local_encr = Encryption(generated_key)
        assert local_encr.is_initialized

        # Test basic encryption
        token = local_encr.encrypt("hello")
        assert token != "hello"
        assert local_encr.decrypt(token) == "hello"

    def test_set_key_later(self, generated_key):
        local_encr = Encryption()
        assert not local_encr.is_initialized

        local_encr.set_key(generated_key)
        assert local_encr.is_initialized
        assert local_encr.decrypt(local_encr.encrypt("data")) == "data"


class TestGlobalEncryptionInstance:
    """
    Tests specifically for the global 'encr' singleton.
    Relies on the 'reset_global_encr' fixture to avoid flakiness.
    """

    def test_global_starts_uninitialized(self):
        """Ensure global instance is clean at start of test."""
        assert not encr.is_initialized
        with pytest.raises(RuntimeError):
            encr.encrypt("fail")

    def test_global_set_key_usage(self, generated_key):
        """Test setting key on global instance."""
        encr.set_key(generated_key)
        assert encr.is_initialized

        ciphertext = encr.encrypt("secret")
        assert encr.decrypt(ciphertext) == "secret"

    def test_global_reset_verification(self):
        """
        This test exists solely to verify the fixture works.
        If the fixture failed, and 'test_global_set_key_usage' ran before this,
        this test would fail because the key would persist.
        """
        assert not encr.is_initialized


class TestKeyHelpers:
    """Tests for keyring interaction and salt management."""

    def test_load_or_create_salt_creates_new(self, temp_salt_file):
        assert not temp_salt_file.exists()

        salt = load_or_create_salt(temp_salt_file)

        assert temp_salt_file.exists()
        assert len(salt) == 16  # os.urandom(16)

    def test_load_or_create_salt_loads_existing(self, temp_salt_file):
        # Manually create file
        existing_salt = os.urandom(16)
        with open(temp_salt_file, "wb") as f:
            f.write(existing_salt)

        # Load it
        loaded_salt = load_or_create_salt(temp_salt_file)
        assert loaded_salt == existing_salt

    def test_keyring_store_and_retrieve(self, mock_keyring, generated_key):
        # Store key
        set_key_in_keyring(TEST_UID, TEST_USER, generated_key)

        # Retrieve key
        retrieved_key = get_key_from_keyring(TEST_UID, TEST_USER)

        # Assertions
        assert retrieved_key == generated_key
        assert isinstance(retrieved_key, bytes)

    def test_keyring_missing_key(self, mock_keyring):
        # Should return None, not raise error
        assert get_key_from_keyring("wrong_uid", "wrong_user") is None

    def test_derive_key(self):
        salt = os.urandom(16)
        iterations = 1000  # Use low iterations for test speed

        key1 = derive_key_from_password(TEST_PASSWORD, salt, iterations)
        key2 = derive_key_from_password(TEST_PASSWORD, salt, iterations)

        # Deterministic check
        assert key1 == key2
        assert isinstance(key1, bytes)

        # Salt variation check
        salt_diff = os.urandom(16)
        key_diff = derive_key_from_password(TEST_PASSWORD, salt_diff, iterations)
        assert key1 != key_diff


def test_full_workflow(mock_keyring, temp_salt_file):
    """
    Simulates the flow:
    1. User runs edit_config (generates password -> key)
    2. User runs app (loads key -> encrypts)
    """
    # 1. SETUP PHASE (Simulating edit_config)
    salt = load_or_create_salt(temp_salt_file)
    derived_key = derive_key_from_password("my_secret_pw", salt, iterations=1000)
    set_key_in_keyring(TEST_UID, TEST_USER, derived_key)

    # 2. RUNTIME PHASE (Simulating cli.py startup)
    # Ensure global is clean
    assert not encr.is_initialized

    # Load from keyring
    loaded_key: bytes = get_key_from_keyring(TEST_UID, TEST_USER)
    assert loaded_key == derived_key

    # Initialize global
    encr.set_key(loaded_key)
    assert encr.is_initialized

    # 3. USAGE PHASE (Simulating db usage)
    secret = "Client Name"
    token = encr.encrypt(secret)
    assert encr.decrypt(token) == secret
