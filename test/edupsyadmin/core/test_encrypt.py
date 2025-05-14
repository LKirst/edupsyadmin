"""Test suite for the core.encrypt module."""

import pytest

from edupsyadmin.core.encrypt import Encryption
from edupsyadmin.core.logger import logger

secret_message = "This is a secret message."
USER_NAME = "encryptiontest_user_do_not_use"
UID = "encryptionexample.com"


class EncryptionTest:
    @pytest.fixture
    def encrypted_message(self, mock_salt_path: str, mock_keyring):
        """Create an encrypted message."""
        encr = Encryption()
        encr.set_fernet(USER_NAME, mock_salt_path, UID)
        token = encr.encrypt(secret_message)
        return token

    def test_encrypt(self, mock_salt_path: str, mock_keyring):
        encr = Encryption()
        encr.set_fernet(USER_NAME, mock_salt_path, UID)
        token = encr.encrypt(secret_message)

        assert isinstance(token, str)
        assert secret_message != token
        mock_keyring.assert_called_with(UID, USER_NAME)

    def test_decrypt(self, encrypted_message, mock_salt_path: str, mock_keyring):
        encr = Encryption()
        encr.set_fernet(USER_NAME, mock_salt_path, UID)
        decrypted = encr.decrypt(encrypted_message)

        assert decrypted == secret_message
        mock_keyring.assert_called_with(UID, USER_NAME)

    def test_set_fernet(self, capsys, mock_salt_path: str, mock_keyring):
        logger.start(
            "DEBUG"
        )  # TODO: Why is this necessary despite the logging fixture?
        encr = Encryption()
        encr.set_fernet(USER_NAME, mock_salt_path, UID)
        encr.set_fernet(USER_NAME, mock_salt_path, UID)

        stdout, stderr = capsys.readouterr()
        assert "using existing fernet" in stderr
        mock_keyring.assert_called_with(UID, USER_NAME)

    def test_update_salt_file(self, mock_salt_path):
        encr = Encryption()
        salt = encr._load_or_create_salt(mock_salt_path)
        with open(mock_salt_path, "rb") as f:
            salt_fromfile = f.read()
        salt == salt_fromfile
