import base64
import os
import keyring
import yaml
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .logger import logger
from .config import config


def get_encryption_key(
    username: str = None,
    configpath: str = None,
    uid: str = None
) -> bytes:
    """Use a password to derive a key
    (see https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet)
    """
    if None in [username, configpath, uid]:
        global config
        logger.debug("trying to use config.username, config.core.config and config.uid")
        username=config.username
        configpath=config.core.config
        uid=config.uid

    salt = _load_or_create_salt(configpath)
    password = _retrieve_password(username, uid)

    # derive a key using the password and salt
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
    core_config = config.setdefault("core", {})
    salt = core_config.get("salt")

    if salt:
        logger.info("using existing salt from the config file")
    else:
        salt = os.urandom(16)
        core_config["salt"] = salt
        with open(configpath, "w") as f:
            dictyaml = dict(config)
            yaml.dump(dictyaml, f) # safe_dump does not work with bytes
        logger.info("created a new salt and wrote it to the config file")

    return salt


def _retrieve_password(username: str, uid: str) -> bytes:
    logger.info(f"retrieving password for {uid} using keyring")
    cred = keyring.get_credential(uid, username)
    if not cred or not cred.password:
        raise ValueError(f"Password not found for uid: {uid}, username: {username}")

    return cred.password.encode()
