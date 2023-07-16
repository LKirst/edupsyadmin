import base64
import os
import keyring
import yaml
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .logger import logger
from .config import config


def get_encryption_key(
    username: str = None, configpath: str = None, uid: str = None
) -> bytes:
    """Use a password to derive a key
    (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
    """
    if None in [username, configpath, uid]:
        global config
        logger.debug("trying to use config.username, config.core.config and config.uid")
        username = config.username
        configpath = config.core.config
        uid = config.uid

    salt = _load_or_create_salt(configpath)
    password = _retrieve_password(username, uid)

    # derive a key using the password and salt
    logger.debug("deriving key from password")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))

    return key

def _load_or_create_salt(configpath: str) -> bytes:
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

def _convert_conf_to_dict(conf):
    if isinstance(conf,dict):
        conf=dict(conf)
    for key, value in conf.items():
        if isinstance(value, dict):
            conf[key] = dict(_convert_conf_to_dict(value))
    return conf


def _retrieve_password(username: str, uid: str) -> bytes:
    logger.info(f"retrieving password for {uid} using keyring")
    cred = keyring.get_credential(uid, username)
    if not cred or not cred.password:
        raise ValueError(f"Password not found for uid: {uid}, username: {username}")

    return cred.password.encode()
