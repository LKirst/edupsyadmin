import base64
import os
from pathlib import Path
from typing import Final

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from keyring.errors import PasswordDeleteError

from edupsyadmin.core.logger import logger

DEFAULT_KDF_ITERATIONS: Final[int] = 600000
OLD_KDF_ITERATIONS: Final[int] = 480000  # Needed for migration


class Encryption:
    """Handles encryption and decryption of data."""

    _fernet: Fernet | None = None

    def __init__(self, key: bytes | None = None) -> None:
        if key:
            self.set_key(key)

    def set_key(self, key: bytes) -> None:
        """Initializes the Fernet instance with a given key."""
        logger.debug("Setting new Fernet key.")
        self._fernet = Fernet(key)

    @property
    def is_initialized(self) -> bool:
        """Returns whether an encryption key is configured."""
        return self._fernet is not None

    def encrypt(self, data: str) -> str:
        """Encrypts a string."""
        if self._fernet is None:
            raise RuntimeError("Encryption key not set.")
        token = self._fernet.encrypt(data.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypts a token string."""
        if self._fernet is None:
            raise RuntimeError("Encryption key not set.")
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


def set_password_in_keyring(uid: str, username: str, password: str) -> None:
    """Stores a password in the keyring."""
    logger.debug(f"Storing password for '{username}' in keyring.")
    keyring.set_password(uid, username, password)


def get_key_from_keyring(uid: str, username: str) -> bytes | None:
    """Retrieves the base64-encoded encryption key from the keyring 'password' field."""
    logger.debug(f"Retrieving key for '{username}' from keyring.")
    backend = keyring.get_keyring()
    logger.debug(f"Using keyring backend: '{backend.__class__.__name__}'")
    cred = keyring.get_credential(uid, username) or None
    key_str = cred.password if cred else None
    return key_str.encode() if key_str else None


def set_key_in_keyring(uid: str, username: str, key: bytes) -> None:
    """
    Stores the base64-encoded encryption key in the keyring.

    This function first attempts to delete any existing key for the given
    uid/username pair to prevent duplicate entries on backends that don't
    support overwriting.
    """
    logger.debug(f"Storing key for '{username}' in keyring.")
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

    set_password_in_keyring(uid, username, key.decode())


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
