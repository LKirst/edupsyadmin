import base64
import json
import os
from pathlib import Path
from typing import Final

import keyring
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from keyring.errors import PasswordDeleteError

from edupsyadmin.core.logger import logger

DEFAULT_KDF_ITERATIONS: Final[int] = 600000
OLD_KDF_ITERATIONS: Final[int] = 480000  # Needed for migration


class Encryption:
    """Handles encryption and decryption of data using MultiFernet for key rotation."""

    _fernet: MultiFernet | None = None

    def set_keys(self, keys: list[bytes]) -> None:
        """Initializes the MultiFernet instance with a given list of keys."""
        if not keys:
            raise ValueError("Key list cannot be empty.")
        logger.debug(f"Setting new MultiFernet with {len(keys)} key(s).")
        self._fernet = MultiFernet([Fernet(key) for key in keys])

    @property
    def is_initialized(self) -> bool:
        """Returns whether an encryption key is configured."""
        return self._fernet is not None

    def encrypt(self, data: str) -> str:
        """Encrypts a string using the primary key."""
        if self._fernet is None:
            raise RuntimeError("Encryption keys not set.")
        token = self._fernet.encrypt(data.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypts a token string, trying all available keys."""
        if self._fernet is None:
            raise RuntimeError("Encryption keys not set.")
        token_bytes = token.encode("utf-8")
        return self._fernet.decrypt(token_bytes).decode("utf-8")


def derive_key_from_password(password: str, salt: bytes, iterations: int) -> bytes:
    """Derives an encryption key from a password and salt using PBKDF2."""
    logger.debug(f"Deriving key with {iterations} iterations.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    # Fernet key must be 32 url-safe base64-encoded bytes
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def check_key_validity(key: bytes | None) -> bool:
    """Checks if a given key is a valid Fernet key."""
    if key is None:
        return False
    try:
        Fernet(key)
        return True
    except (ValueError, TypeError):
        return False


def get_keys_from_keyring(uid: str, username: str) -> list[bytes]:
    """
    Retrieves a list of base64-encoded encryption keys from the keyring.

    Handles both the new JSON list format and the legacy single-key format
    for backward compatibility.
    """
    logger.debug(f"Retrieving keys for '{username}' from keyring.")
    backend = keyring.get_keyring()
    logger.debug(f"Using keyring backend: '{backend.__class__.__name__}'")
    cred = keyring.get_credential(uid, username)
    key_data = cred.password if cred else None

    if not key_data:
        return []

    try:
        # New format: JSON list of base64-encoded keys
        key_list_str = json.loads(key_data)
        if isinstance(key_list_str, list):
            return [k.encode("utf-8") for k in key_list_str]
    except (json.JSONDecodeError, AttributeError):
        # Fallback for old format: single base64-encoded key
        logger.debug(
            "Could not decode as JSON, falling back to legacy single-key format."
        )
        return [key_data.encode("utf-8")]

    # Handle case where JSON is valid but not a list
    return [key_data.encode("utf-8")]


def set_keys_in_keyring(uid: str, username: str, keys: list[bytes]) -> None:
    """
    Stores a list of base64-encoded encryption keys in the keyring as a JSON list.

    This function first attempts to delete any existing key for the given
    uid/username pair to prevent duplicate entries on backends that don't
    support overwriting.
    """
    logger.debug(f"Storing {len(keys)} key(s) for '{username}' in keyring.")
    try:
        keyring.delete_password(uid, username)
        logger.debug(f"Deleted existing key for '{username}'.")
    except PasswordDeleteError:
        # This error occurs if no password exists to delete. It's safe to ignore.
        logger.debug(f"No existing key for '{username}' to delete.")
    except Exception as e:
        # Some backends might raise a different error if the password
        # does not exist. We can treat this as a non-critical event
        # and log it at a lower level.
        logger.debug(
            f"Non-critical error while trying to delete key for '{username}': {e!r}"
        )

    key_list_str = [k.decode("utf-8") for k in keys]
    keyring.set_password(uid, username, json.dumps(key_list_str))


def load_or_create_salt(salt_path: Path) -> bytes:
    """Loads a salt from a file or creates a new one if it doesn't exist."""
    # TODO: store the salt in the db, not in a separate file
    if salt_path.is_file():
        logger.debug(f"Using existing salt from `{salt_path}`")
        return salt_path.read_bytes()
    logger.debug(f"Creating new salt and writing to `{salt_path}`")
    salt = os.urandom(16)

    salt_path.touch(mode=0o600)
    salt_path.write_bytes(salt)
    return salt


# global encryption instance
encr = Encryption()
