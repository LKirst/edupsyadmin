"""Test suite for the core.encrypt module."""

import contextlib
import os
from pathlib import Path

import keyring
import pytest
from cryptography.fernet import Fernet

# Import the class, the global instance, and helper functions
from edupsyadmin.core.encrypt import (
    Encryption,
    check_key_validity,
    derive_key_from_password,
    encr,  # The global instance
    get_keys_from_keyring,
    load_or_create_salt,
    set_keys_in_keyring,
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
    encr._fernet = None
    yield
    encr._fernet = None


@pytest.fixture
def generated_key() -> bytes:
    """Returns a valid Fernet key."""
    return Fernet.generate_key()


@pytest.fixture
def generated_key_list() -> list[bytes]:
    """Returns a list of three valid Fernet keys."""
    return [Fernet.generate_key() for _ in range(3)]


@pytest.fixture
def temp_salt_file(tmp_path) -> Path:
    """Returns a path to a non-existent salt file in a temp directory."""
    return tmp_path / "salt.txt"


class TestEncryptionUnit:
    """Tests the Encryption class logic in isolation using MultiFernet."""

    def test_uninitialized(self):
        local_encr = Encryption()
        assert not local_encr.is_initialized
        with pytest.raises(RuntimeError, match="Encryption keys not set"):
            local_encr.encrypt("test")

    def test_set_keys(self, generated_key_list):
        local_encr = Encryption()
        local_encr.set_keys(generated_key_list)
        assert local_encr.is_initialized

        # Test basic encryption (should use the FIRST key)
        token = local_encr.encrypt("hello")
        assert token != "hello"
        assert local_encr.decrypt(token) == "hello"

    def test_key_rotation_decryption(self, generated_key_list):
        local_encr = Encryption()
        key_new, key_medium, key_old = generated_key_list

        # Set up MultiFernet with new key as primary
        local_encr.set_keys([key_new, key_medium, key_old])

        # 1. Encrypt new data, ensure it can be decrypted
        new_data = "new data"
        new_token = local_encr.encrypt(new_data)
        assert local_encr.decrypt(new_token) == new_data

        # 2. Simulate data that was encrypted with an OLD key
        old_data = "old data"
        old_token = Fernet(key_old).encrypt(old_data.encode())

        # 3. Ensure MultiFernet can decrypt the old token
        assert local_encr.decrypt(old_token.decode()) == old_data

    def test_set_keys_with_empty_list(self):
        local_encr = Encryption()
        with pytest.raises(ValueError, match="Key list cannot be empty"):
            local_encr.set_keys([])


class TestGlobalEncryptionInstance:
    """Tests specifically for the global 'encr' singleton."""

    def test_global_starts_uninitialized(self):
        assert not encr.is_initialized
        with pytest.raises(RuntimeError):
            encr.encrypt("fail")

    def test_global_set_keys_usage(self, generated_key):
        encr.set_keys([generated_key])
        assert encr.is_initialized

        ciphertext = encr.encrypt("secret")
        assert encr.decrypt(ciphertext) == "secret"

    def test_global_reset_verification(self):
        assert not encr.is_initialized


class TestKeyHelpers:
    """Tests for keyring interaction and salt management."""

    def test_load_or_create_salt_creates_new(self, temp_salt_file):
        assert not temp_salt_file.exists()
        salt = load_or_create_salt(temp_salt_file)
        assert temp_salt_file.exists()
        assert len(salt) == 16

    def test_load_or_create_salt_loads_existing(self, temp_salt_file):
        existing_salt = os.urandom(16)
        temp_salt_file.write_bytes(existing_salt)
        loaded_salt = load_or_create_salt(temp_salt_file)
        assert loaded_salt == existing_salt

    def test_keyring_store_and_retrieve_multiple_keys(self, generated_key_list):
        set_keys_in_keyring(TEST_UID, TEST_USER, generated_key_list)
        retrieved_keys = get_keys_from_keyring(TEST_UID, TEST_USER)
        assert retrieved_keys == generated_key_list
        assert isinstance(retrieved_keys, list)

    def test_keyring_backward_compatibility_retrieval(self, generated_key):
        """Test if get_keys can read the old single-key format."""
        # Simulate old format: store a single key string directly
        keyring.set_password(TEST_UID, TEST_USER, generated_key.decode("utf-8"))

        # Use the new getter
        retrieved_keys = get_keys_from_keyring(TEST_UID, TEST_USER)

        # Should be a list containing the single key
        assert isinstance(retrieved_keys, list)
        assert len(retrieved_keys) == 1
        assert retrieved_keys[0] == generated_key

    def test_keyring_missing_key(self):
        # Clean up any potential key from other tests
        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password("missing_uid", "missing_user")
        # Should return an empty list, not raise error
        assert get_keys_from_keyring("missing_uid", "missing_user") == []

    def test_derive_key(self):
        salt = os.urandom(16)
        iterations = 1000
        key1 = derive_key_from_password(TEST_PASSWORD, salt, iterations)
        key2 = derive_key_from_password(TEST_PASSWORD, salt, iterations)
        assert key1 == key2
        assert isinstance(key1, bytes)
        assert check_key_validity(key1)

        salt_diff = os.urandom(16)
        key_diff = derive_key_from_password(TEST_PASSWORD, salt_diff, iterations)
        assert key1 != key_diff


def test_full_workflow(temp_salt_file):
    """
    Simulates the full workflow with key rotation.
    """
    # 1. SETUP PHASE (Simulating first-time password set)
    salt = load_or_create_salt(temp_salt_file)
    first_key = derive_key_from_password("my_secret_pw", salt, iterations=1000)
    set_keys_in_keyring(TEST_UID, TEST_USER, [first_key])

    # 2. RUNTIME AND USAGE
    assert not encr.is_initialized
    loaded_keys = get_keys_from_keyring(TEST_UID, TEST_USER)
    assert loaded_keys == [first_key]
    encr.set_keys(loaded_keys)
    assert encr.is_initialized
    token1 = encr.encrypt("secret_data_1")
    assert encr.decrypt(token1) == "secret_data_1"

    # 3. KEY ROTATION PHASE (Simulating password change)
    second_key = derive_key_from_password("new_stronger_pw", salt, iterations=1000)
    # The new key is prepended
    rotated_keys = [second_key, *loaded_keys]
    set_keys_in_keyring(TEST_UID, TEST_USER, rotated_keys)

    # 4. POST-ROTATION RUNTIME
    encr._fernet = None  # Reset global instance
    assert not encr.is_initialized
    loaded_rotated_keys = get_keys_from_keyring(TEST_UID, TEST_USER)
    assert loaded_rotated_keys == rotated_keys
    encr.set_keys(loaded_rotated_keys)
    assert encr.is_initialized

    # 5. POST-ROTATION USAGE
    # Encrypt new data (uses the new, second key)
    token2 = encr.encrypt("secret_data_2")
    assert encr.decrypt(token2) == "secret_data_2"

    # Crucially, ensure data encrypted with the OLD key is still readable
    assert encr.decrypt(token1) == "secret_data_1"
