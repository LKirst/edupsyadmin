""" Test suite for the api module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the module is actually
being tested. If the library is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""
import os
import pytest
import keyring
from pathlib import Path

from edupsy_admin.api import *  # tests __all__
from edupsy_admin.core.config import config
from edupsy_admin.core.logger import logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

client_data = {
    "first_name_encr": "John",
    "last_name_encr": "Doe",
    "birthday_encr": "1990-01-01",
    "street_encr": "123 Main St",
    "city_encr": "New York",
    "parent_encr": "Jane Doe",
    "telephone_encr": "555-1234",
    "email_encr": "john.doe@example.com",
    "gender": "Male",
    "school": "ABC School",
    "date_of_graduation": "2021-06-30",
}


@pytest.fixture()
def clients_manager():
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
    config.logging = "DEBUG"
    logger.start(config.logging)

    # create a keyring entry for testing if it does not exist
    cred = keyring.get_credential(TEST_UID, TEST_USERNAME)
    if cred is None:
        keyring.set_password(TEST_UID, TEST_USERNAME, "test_pw_do_not_use")

    database_url = "sqlite:///test.sqlite"
    manager = ClientsManager(
            database_url,
            uid=TEST_UID, username=TEST_USERNAME, configpath=str(cfg_path))

    yield manager
    manager.close()
    os.remove(config.core.config)


# Test the add_client() method
def test_add_client(clients_manager):
    client_id = clients_manager.add_client(client_data)
    client = clients_manager.get_decrypted_client(client_id = client_id)
    assert client.first_name_encr == b"John"
    assert client.last_name_encr == b"Doe"


# Test the edit_client() method
def test_edit_client(clients_manager):
    client_id = clients_manager.add_client(client_data)
    client = clients_manager.get_decrypted_client(client_id = client_id)
    updated_data = {"first_name_encr": "Jane", "last_name_encr": "Smith"}
    clients_manager.edit_client(client_id, updated_data)
    updated_client = clients_manager.get_decrypted_client(client_id)
    assert updated_client.first_name_encr == b"Jane"
    assert updated_client.last_name_encr == b"Smith"
    assert (
        updated_client.datetime_lastmodified > client.datetime_lastmodified
    )


# Test the delete_client() method
def test_delete_client(clients_manager):
    clients_manager.add_client(client_data)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 1
    client_id = clients[0]["id"]

    clients_manager.delete_client(client_id)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 0


def test_collect_client_data_cli(clients_manager, monkeypatch):
    def mock_input(prompt):
        return "John"

    monkeypatch.setattr("builtins.input", mock_input)

    client_data = collect_client_data_cli()
    assert isinstance(client_data, Client)

    # StringEncryptedType
    assert client_data.first_name_encr != "John"
    assert client_data.last_name_encr != "Doe"
    assert client_data.birthday_encr != "1990-01-01"


def test_hello():
    """Test the hello() function."""
    assert hello() == "Hello, World!"
    return


def test_hello_name():
    """Test the hello() function with a name."""
    assert hello("foo") == "Hello, foo!"
    return


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
