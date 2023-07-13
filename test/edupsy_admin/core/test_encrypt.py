""" Test suite for the core.encrypt module.
"""


import os
import pytest
import keyring
from pathlib import Path

from edupsy_admin.core.config import config
from edupsy_admin.core.logger import logger
from edupsy_admin.core.encrypt import get_encryption_key

@pytest.fixture
def configfile():
    """Create a test config file and an encryption key"""
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


def test_get_encryption_key(configfile):
    # Call the function
    key = get_encryption_key()

    # Assertions
    assert isinstance(key, bytes)
    assert len(key) > 0
