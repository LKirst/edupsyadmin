import os

import keyring
import pytest

from edupsy_admin.api.managers import (
    ClientsManager,
    enter_client_cli,
    enter_client_untiscsv,
)
from edupsy_admin.core.config import config
from edupsy_admin.core.logger import logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

client_data = {
    "school": "test_school",
    "gender": "m",
    "entry_date": "2021-06-30",
    "class_name": "11TKKG",
    "first_name": "John",
    "last_name": "Doe",
    "birthday": "1990-01-01",
    "street": "123 Main St",
    "city": "New York",
    "telephone1": "555-1234",
    "email": "john.doe@example.com",
}

conf1_content = """
core:
  logging: WARN
  uid: liebermann-schulpsychologie.github.io
school:
  test_school:
    school_name: Test School
    school_street: 123 Test St
    school_head_w_school: Principal of Test School
    end: 12
"""


@pytest.fixture()
def clients_manager(tmp_path):
    """Create a test config file and an encryption key"""
    # create a config file
    conf1_path = tmp_path / "conf2.yml"
    conf1_path.write_text(conf1_content.strip())

    # set config values
    config.load(str(conf1_path))
    # TODO: I don't understand why this throws an error
    config.core.config = str(conf1_path)
    config.logging = "DEBUG"
    logger.start(config.logging)

    # create a keyring entry for testing if it does not exist
    cred = keyring.get_credential(TEST_UID, TEST_USERNAME)
    if cred is None:
        keyring.set_password(TEST_UID, TEST_USERNAME, "test_pw_do_not_use")

    database_url = "sqlite:///test.sqlite"
    manager = ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        config_path=str(conf1_path),
    )

    yield manager
    os.remove(config.core.config)


def test_add_client(clients_manager):
    client_id = clients_manager.add_client(**client_data)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "John"
    assert client["last_name"] == "Doe"


def test_edit_client(clients_manager):
    client_id = clients_manager.add_client(**client_data)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    updated_data = {"first_name_encr": "Jane", "last_name_encr": "Smith"}
    clients_manager.edit_client(client_id, updated_data)
    updated_client = clients_manager.get_decrypted_client(client_id)
    assert updated_client["first_name"] == "Jane"
    assert updated_client["last_name"] == "Smith"
    assert updated_client["datetime_lastmodified"] > client["datetime_lastmodified"]


def test_delete_client(clients_manager):
    client_id = clients_manager.add_client(**client_data)
    clients_manager.delete_client(client_id)
    # TODO: add assert


def test_enter_client_cli(clients_manager, monkeypatch):
    # simulate the commandline input
    inputs = iter(client_data)

    def mock_input(prompt):
        return client_data[next(inputs)]

    monkeypatch.setattr("builtins.input", mock_input)

    client_id = enter_client_cli(clients_manager)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "John"
    assert client["last_name"] == "Doe"


def test_enter_client_untiscsv(clients_manager):
    testcsv = "test/data/webuntis_example.csv"
    client_id = enter_client_untiscsv(clients_manager, testcsv)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "Max"
    assert client["last_name"] == "Mustermann"


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))