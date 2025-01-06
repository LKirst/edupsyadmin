"""Test suite for the core.encrypt module."""

import pytest
import yaml

from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import Encryption, _convert_conf_to_dict
from edupsyadmin.core.logger import logger

secret_message = "This is a secret message."


@pytest.fixture
def encrypted_message(mock_config: list[str], mock_keyring):
    """Create an encrypted message."""
    encr = Encryption()
    encr.set_fernet(config.core.app_username, mock_config[0], config.core.app_uid)
    token = encr.encrypt(secret_message)
    return token


def test_encrypt(mock_config: list[str], mock_keyring):
    encr = Encryption()
    encr.set_fernet(config.core.app_username, mock_config[0], config.core.app_uid)
    token = encr.encrypt(secret_message)

    assert isinstance(token, bytes)
    assert secret_message != token
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_decrypt(encrypted_message, mock_config: list[str], mock_keyring):
    encr = Encryption()
    encr.set_fernet(config.core.app_username, mock_config[0], config.core.app_uid)
    decrypted = encr.decrypt(encrypted_message)

    assert decrypted == secret_message
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_set_fernet(capsys, mock_config: list[str], mock_keyring):
    logger.start("DEBUG")  # TODO: Why is this necessary despite the logging fixture?
    encr = Encryption()
    encr.set_fernet(config.core.app_username, mock_config[0], config.core.app_uid)
    encr.set_fernet(config.core.app_username, mock_config[0], config.core.app_uid)

    stdout, stderr = capsys.readouterr()
    assert "fernet was already set; using existing fernet" in stderr
    mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


def test_update_config(mock_config: list[str]):
    encr = Encryption()
    salt = encr._load_or_create_salt(mock_config[0])
    dictyaml_salt_config = _convert_conf_to_dict(config)
    logger.debug(f"dictyaml_salt_config {dictyaml_salt_config}")
    dictyaml_salt_target = {
        "core": {
            "logging": "DEBUG",
            "app_uid": "example.com",
            "app_username": "test_user_do_not_use",
            "config": mock_config,
            "salt": salt,
        }
    }
    with open(mock_config[0], "r") as f:
        dictyaml_salt_fromfile = yaml.safe_load(f)

    # all items in dictyaml_salt_target should be in dictyaml_salt_config
    # and in dictyaml_salt_fromfile
    for item in dictyaml_salt_target["core"].items():
        assert item in dictyaml_salt_config["core"].items()
        assert item in dictyaml_salt_fromfile["core"].items()
