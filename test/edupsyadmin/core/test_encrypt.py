"""Test suite for the core.encrypt module."""

import os

import pytest
import yaml

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import Encryption, _convert_conf_to_dict
from edupsyadmin.core.logger import logger

secret_message = "This is a secret message."


@pytest.fixture
def configfile(tmp_path):
    """Create a test config file"""
    # create an empty config file
    cfg_path = tmp_path / "configfile.yml"
    with open(cfg_path, mode="w"):
        pass

    # load the config
    config.load(str(cfg_path))

    # set config values
    config.core = {}
    config.core.config = str(cfg_path)
    config.username = "test_user_do_not_use"
    config.uid = "example.com"
    config.logging = "DEBUG"
    logger.start(config.logging)

    yield
    os.remove(config.core.config)


@pytest.fixture
def encrypted_message(configfile, mock_keyring):
    """Create an encrypted message."""
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    token = encr.encrypt(secret_message)
    return token


def test_encrypt(configfile, mock_keyring):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    token = encr.encrypt(secret_message)

    assert isinstance(token, bytes)
    assert secret_message != token
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_decrypt(encrypted_message, mock_keyring):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    decrypted = encr.decrypt(encrypted_message)

    assert decrypted == secret_message
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_set_fernet(capsys, configfile, mock_keyring):
    encr = Encryption()
    encr.set_fernet(config.username, config.core.config, config.uid)
    encr.set_fernet(config.username, config.core.config, config.uid)

    _, stderr = capsys.readouterr()
    assert "fernet was already set; using existing fernet" in stderr
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_update_config(configfile):
    encr = Encryption()
    _convert_conf_to_dict(config)
    salt = encr._load_or_create_salt(config.core.config)
    dictyaml_salt_config = _convert_conf_to_dict(config)
    dictyaml_salt_target = {
        "core": {"config": config.core.config, "salt": salt},
        "username": "test_user_do_not_use",
        "uid": "example.com",
        "logging": "DEBUG",
    }
    with open(config.core.config, "r") as f:
        dictyaml_salt_fromfile = yaml.safe_load(f)

    # all items in dictyaml_salt_target should be in dictyaml_salt_config
    # and in dictyaml_salt_fromfile
    assert all(
        item in dictyaml_salt_config.items() for item in dictyaml_salt_target.items()
    )
    assert all(
        item in dictyaml_salt_fromfile.items() for item in dictyaml_salt_target.items()
    )
