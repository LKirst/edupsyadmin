import base64
import os

import keyring
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import config
from .logger import logger


class Encryption:
    fernet = None

    def set_fernet(self, username: str, config_path: str, uid: str) -> None:
        """use a password to derive a key
        (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
        """
        if self.fernet is not None:
            logger.debug("fernet was already set; using existing fernet")
            return

        salt = self._load_or_create_salt(config_path)
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
            logger.critical("call set_fernet() before calling encrypt()")
        token = self.fernet.encrypt(data.encode())
        return token

    def decrypt(self, token: bytes) -> str:
        if self.fernet is None:
            logger.critical("call set_fernet() before calling decrypt()")
        data = self.fernet.decrypt(token).decode()
        return data

    def _load_or_create_salt(self, config_path: str) -> bytes:
        config.load(config_path)
        if "core" in config.keys() and "salt" in config.core.keys():
            logger.info("using existing salt from the config file")
            salt = config.core.salt
        else:
            logger.info("creating new salt and writing it to the config file")
            salt = os.urandom(16)
            with open(config_path, "a") as f:
                if "core" in config.keys():
                    config.core.update({"salt": salt})
                else:
                    config.update({"core": {"salt": salt}})

                dictyaml = _convert_conf_to_dict(config)  # convert to dict for pyyaml
                logger.debug(f"config as a dict: {dictyaml}")
                yaml.dump(dictyaml, f)  # I couldn't get safe_dump to work with bytes

        return salt

    def _retrieve_password(self, username: str, uid: str) -> bytes:
        # TODO: Make sure the password is only retrieved once (for example in cli.py)
        # Currently this is called both in managers.py and in clients.py
        logger.info(f"retrieving password for {uid} using keyring")
        cred = keyring.get_credential(uid, username)
        if not cred or not cred.password:
            raise ValueError(f"Password not found for uid: {uid}, username: {username}")

        return cred.password.encode()


def _convert_conf_to_dict(conf) -> dict:
    if isinstance(conf, dict):
        conf = dict(conf)
    for key, value in conf.items():
        if isinstance(value, dict):
            conf[key] = dict(_convert_conf_to_dict(value))
    return conf
