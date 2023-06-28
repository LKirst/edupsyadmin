import base64
import os
import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .logger import logger

class Encryption:
    def __init__(self):
        """Use a password with Fernet to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        logger.info("retrieving password using keyring")
        cred=keyring.get_credential("edupsy", "")
        password=str.encode(cred.password) # passwords as bytes
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._f = Fernet(key)

    def encrypt(self, data: bytes, username: str):
        token = self._f.encrypt(data)
        return token

    def decrypt(self, token: bytes, username: str):
        data = self._f.decrypt(token)
        return data
