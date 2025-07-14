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
        self, username: str, user_data_dir: str | os.PathLike[str], uid: str
    ) -> None:
        """use a password to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        if self.fernet is not None:
            logger.debug("using existing fernet")
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

    def encrypt(self, data: str) -> str:
        if self.fernet is None:
            raise RuntimeError("call set_fernet() before calling encrypt()")
        token = self.fernet.encrypt(data.encode(encoding="utf-8"))
        return token.decode(encoding="utf-8")

    def decrypt(self, token: str) -> str:
        if self.fernet is None:
            raise RuntimeError("call set_fernet() before calling decrypt()")
        token_bytes = token.encode(encoding="utf-8")
        return self.fernet.decrypt(token_bytes).decode(encoding="utf-8")

    def _load_or_create_salt(self, salt_path: str | os.PathLike[str]) -> bytes:
        # TODO: store the salt in the db, not in a separate file
        if Path(salt_path).is_file():
            logger.info(f"using existing salt from `{salt_path}`")
            with open(salt_path, "rb") as binary_file:
                salt = binary_file.read()
        else:
            logger.info(f"creating new salt and writing to `{salt_path}`")
            salt = os.urandom(16)
            with open(salt_path, "wb") as binary_file:
                binary_file.write(salt)
        return salt

    def _retrieve_password(self, username: str, uid: str) -> bytes:
        logger.info(
            f"retrieving password for uid: '{uid}' "
            f"and username: '{username}' using keyring"
        )
        backend = keyring.get_keyring()
        logger.info(f"using keyring backend: '{backend.__class__.__name__}'")
        cred = keyring.get_credential(uid, username)
        if not cred or not cred.password:
            raise ValueError(
                f"password not found for uid: '{uid}', username: '{username}', "
            )

        return cred.password.encode()


encr = Encryption()
