import base64
import os
import keyring
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .logger import logger
from .config import config

class Encryption():

    fernet = None

    def set_fernet(
        self, username: str, configpath: str, uid: str):
        """use a password to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        if self.fernet is not None:
            return

        salt = self._load_or_create_salt(configpath)
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

    def encrypt(self, data: bytes) -> bytes:
        if self.fernet is None:
            logger.critical('call set_fernet before you use the Encryption object to encrypt')
        token = self.fernet.encrypt(data)
        return token

    def decrypt(self, token: bytes) -> bytes:
        if self.fernet is None:
            logger.critical('call set_fernet before you use the Encryption object to decrypt')
        data=self.fernet.decrypt(token)
        return data

    def _load_or_create_salt(self, configpath: str) -> bytes:
        config.load(configpath)
        if "core" in config.keys() and "salt" in config.core.keys():
            logger.info("using existing salt from the config file")
            salt = config.core.salt
        else:
            logger.info("creating new salt and writing it to the config file")
            salt = os.urandom(16)
            with open(configpath, "a") as f:
                if "core" in config.keys():
                    config.core.update({"salt": salt})
                else:
                    config.update({"core": {"salt": salt}})

                dictyaml = _convert_conf_to_dict(config)  # convert to dict for pyyaml
                logger.debug(f"config as a dict: {dictyaml}")
                yaml.dump(dictyaml, f) # I couldn't get safe_dump to work with bytes

        return salt

    def _retrieve_password(self, username: str, uid: str) -> bytes:
        logger.info(f"retrieving password for {uid} using keyring")
        cred = keyring.get_credential(uid, username)
        if not cred or not cred.password:
            raise ValueError(f"Password not found for uid: {uid}, username: {username}")

        return cred.password.encode()


def _convert_conf_to_dict(conf):
    if isinstance(conf,dict):
        conf=dict(conf)
    for key, value in conf.items():
        if isinstance(value, dict):
            conf[key] = dict(_convert_conf_to_dict(value))
    return conf