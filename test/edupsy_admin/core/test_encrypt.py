""" Test suite for the core.encrypt module.
"""

import pytest
import os
from pathlib import Path
import keyring
from edupsy_admin.core.encrypt import *

TEST_UID = "example.com"
TEST_USER = "test_user_do_not_use"
TEST_PW = "test_pw_do_not_use"
TEST_CONFIG = Path("test/data/conf_encrypt.yml")

@pytest.fixture(autouse=True)
def configfile():
    if not TEST_CONFIG.parent.exists():
        os.makedirs(TEST_CONFIG.parent)
    open(TEST_CONFIG, mode='a').close()
    yield
    os.remove(TEST_CONFIG)

@pytest.fixture
def encryption():
    """Return an Encryption object for texting"""
    cred = keyring.get_credential(TEST_UID, TEST_USER)
    if cred is None:
        keyring.set_password(TEST_UID, TEST_USER, TEST_PW)
    encryption = Encryption(username=TEST_USER, configpath=str(TEST_CONFIG), uid=TEST_UID)
    return encryption

class EncryptionTest(object):
    """Test suite for the Encryption class."""

    def test_encrypt_and_decrypt(self, encryption):
        secret_message = b"This is a test message."
        token=encryption.encrypt(secret_message)
        decrypted_message=encryption.decrypt(token)
        assert decrypted_message == secret_message
        assert token != secret_message
