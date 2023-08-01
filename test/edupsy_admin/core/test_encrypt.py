""" Test suite for the core.encrypt module.
"""


import os
import pytest
import keyring
from pathlib import Path

from edupsy_admin.core.config import config
from edupsy_admin.core.logger import logger
from edupsy_admin.core.encrypt import Encryption

secret_message=b"This is a secret message."

@pytest.fixture
def configfile():
    """Create a test config file"""
    # create a config file if it does not exist
    cfg_path = Path("test/data/testconfig.yml")
    if not cfg_path.parent.exists():
        os.makedirs(cfg_path.parent)
    open(cfg_path, mode="a").close()
    config.load(str(cfg_path))

    # set config values
    config.core = {}
    config.core.config = str(cfg_path)
    config.username = "test_user_do_not_use"
    config.uid = "example.com"
    config.logging="DEBUG"
    logger.start(config.logging)

    # create a keyring entry for testing if it does not exist
    cred = keyring.get_credential(config.uid, config.username)
    if cred is None:
        keyring.set_password(config.uid, config.username, "test_pw_do_not_use")

    yield
    os.remove(config.core.config)

@pytest.fixture
def encrypted_message(configfile):
    """Create an encrypted message."""
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    token=encr.encrypt(secret_message)
    return token


def test_encrypt(configfile):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    token=encr.encrypt(secret_message)

    assert isinstance(token, bytes)
    assert secret_message != token

def test_decrypt(encrypted_message):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    decrypted=encr.decrypt(encrypted_message)

    assert decrypted == secret_message

def test_set_fernet(capsys, configfile):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    encr.set_fernet(config.username, config.core.config, config.uid)

    _, stderr = capsys.readouterr()
    assert "fernet was already set; using existing fernet" in stderr
