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


@pytest.fixture(autouse=True)
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
    config.logging = "DEBUG"
    logger.start(config.logging)

    # create a keyring entry for testing if it does not exist
    cred = keyring.get_credential(config.uid, config.username)
    if cred is None:
        keyring.set_password(config.uid, config.username, "test_pw_do_not_use")

    yield
    os.remove(config.core.config)


# Fixture to create a test instance of ClientsManager
@pytest.fixture
def clients_manager():
    database_url = "sqlite:///test.db"
    manager = ClientsManager(database_url)
    yield manager
    manager.close()


# Test the add_client() method
def test_add_client(clients_manager):
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "birthday": "1990-01-01",
        "street": "123 Main St",
        "city": "New York",
        "parent": "Jane Doe",
        "telephone": "555-1234",
        "email": "john.doe@example.com",
        "gender": "Male",
        "notes": "Some notes",
        "school": "ABC School",
        "date_of_graduation": "2021-06-30",
    }
    clients_manager.add_client(client_data)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 1
    assert clients[0]["first_name"] == "John"
    assert clients[0]["last_name"] == "Doe"


# Test the edit_client() method
def test_edit_client(clients_manager):
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "birthday": "1990-01-01",
        "street": "123 Main St",
        "city": "New York",
        "parent": "Jane Doe",
        "telephone": "555-1234",
        "email": "john.doe@example.com",
        "gender": "Male",
        "notes": "Some notes",
        "school": "ABC School",
        "date_of_graduation": "2021-06-30",
    }
    clients_manager.add_client(client_data)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 1
    client_id = clients[0]["id"]

    updated_data = {"first_name": "Jane", "last_name": "Smith"}
    clients_manager.edit_client(client_id, updated_data)
    updated_client = clients_manager.get_all_clients()[0]
    assert updated_client["first_name"] == "Jane"
    assert updated_client["last_name"] == "Smith"
    assert (
        updated_client["datetime_lastmodified"] > client_data["datetime_lastmodified"]
    )


# Test the delete_client() method
def test_delete_client(clients_manager):
    client_data = {
        "first_name": "John",
        "last_name": "Doe",
        "birthday": "1990-01-01",
        "street": "123 Main St",
        "city": "New York",
        "parent": "Jane Doe",
        "telephone": "555-1234",
        "email": "john.doe@example.com",
        "gender": "Male",
        "notes": "Some notes",
        "school": "ABC School",
        "date_of_graduation": "2021-06-30",
    }
    clients_manager.add_client(client_data)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 1
    client_id = clients[0]["id"]

    clients_manager.delete_client(client_id)
    clients = clients_manager.get_all_clients()
    assert len(clients) == 0


def test_collect_client_data_cli(monkeypatch):
    def mock_input(prompt):
        return "John"

    monkeypatch.setattr("builtins.input", mock_input)

    client_data = collect_client_data_cli()
    assert isinstance(client_data, Client)

    # StringEncryptedType
    assert client_data.first_name != "John"
    assert client_data.last_name != "Doe"
    assert client_data.birthday != "1990-01-01"


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
