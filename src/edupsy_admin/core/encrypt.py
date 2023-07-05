import base64
import os
import keyring
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .logger import logger
from .config import config

class Encryption:
    def __init__(self, username: str, configpath: str,
            uid: str = "liebermann-schulpsychologie.github.io"):
        """Use a password with Fernet to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        self.username=username
        logger.info(f"retrieving password for {uid} using keyring")
        cred=keyring.get_credential(uid, username)
        password=str.encode(cred.password) # passwords as bytes

        # read salt from or write it to the config file
        config.load(configpath)
        if 'core' in config.keys() and 'salt' in config.core.keys():
            logger.info("using existing salt from the config file")
            salt=config.core.salt
        else:
            logger.info("creating new salt and writing it to the config file")
            salt = os.urandom(16)
            with open(configpath, "a") as f:
                if 'core' in config.keys():
                    config.core.update({'salt':salt})
                else:
                    config.update({'core':{'salt':salt}})
                dictyaml = dict(config)
                print(f"dictyaml = {dictyaml}")
                yaml.safe_dump(dictyaml, f)

        # derive a key using the password and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._f = Fernet(key)

    def encrypt(self, data: bytes):
        token = self._f.encrypt(data)
        return token

    def decrypt(self, token: bytes):
        data = self._f.decrypt(token)
        return data
