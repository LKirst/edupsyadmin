import base64
import os
from pathlib import Path

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from edupsyadmin.core.logger import logger


class Encryption:
    fernet = None

    def set_fernet(
        self, username: str, user_data_dir: str | os.PathLike, uid: str
    ) -> None:
        """use a password to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        if self.fernet is not None:
            logger.debug("fernet was already set; using existing fernet")
            return

        salt = self._load_or_create_salt(user_data_dir)
        password = self._retrieve_password(username, uid)

        # derive a key using the password and salt
        logger.debug("deriving key from password")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        secret_key = base64.urlsafe_b64encode(kdf.derive(password))
        self.fernet = Fernet(secret_key)

    def encrypt(self, data: str) -> bytes:
        if self.fernet is None:
            raise RuntimeError("call set_fernet() before calling encrypt()")
        token = self.fernet.encrypt(data.encode())
        return token

    def decrypt(self, token: bytes | str) -> str:
        if self.fernet is None:
            raise RuntimeError("call set_fernet() before calling decrypt()")
        if isinstance(token, str):
            token = token.encode()
        data = self.fernet.decrypt(token).decode()
        return data

    def _load_or_create_salt(self, salt_path: str | os.PathLike) -> bytes:
        if Path(salt_path).is_file():
            logger.info(f"using existing salt from {salt_path}")
            with open(salt_path, "rb") as binary_file:
                salt = binary_file.read()
        else:
            logger.info(f"creating new salt and writing to {salt_path}")
            salt = os.urandom(16)
            with open(salt_path, "wb") as binary_file:
                binary_file.write(salt)
        return salt

    def _retrieve_password(self, username: str, uid: str) -> bytes:
        # TODO: Make sure the password is only retrieved once (for example in cli.py)
        # Currently this is called both in managers.py and in clients.py
        logger.info(f"retrieving password for {uid} using keyring")
        cred = keyring.get_credential(uid, username)
        if not cred or not cred.password:
            raise ValueError(f"Password not found for uid: {uid}, username: {username}")

        return cred.password.encode()
