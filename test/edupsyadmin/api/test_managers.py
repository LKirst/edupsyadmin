import keyring
import pytest

from edupsyadmin.api.managers import (
    ClientNotFound,
    ClientsManager,
    enter_client_cli,
    enter_client_untiscsv,
)
from edupsyadmin.core.logger import logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

client_data = {
    "client_id": None,
    "school": "FirstSchool",
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


@pytest.fixture()
def clients_manager(tmp_path, mock_config):
    """Create a clients_manager"""
    logger.start("DEBUG")

    # create a keyring entry for testing if it does not exist
    cred = keyring.get_credential(TEST_UID, TEST_USERNAME)
    if cred is None:
        keyring.set_password(TEST_UID, TEST_USERNAME, "test_pw_do_not_use")

    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    manager = ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        config_path=str(mock_config),
    )

    yield manager


def test_add_client(mock_config, clients_manager):
    client_id = clients_manager.add_client(**client_data)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "John"
    assert client["last_name"] == "Doe"


def test_edit_client(mock_config, clients_manager):
    client_id = clients_manager.add_client(**client_data)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    updated_data = {"first_name_encr": "Jane", "last_name_encr": "Smith"}
    clients_manager.edit_client(client_id, updated_data)
    updated_client = clients_manager.get_decrypted_client(client_id)
    assert updated_client["first_name"] == "Jane"
    assert updated_client["last_name"] == "Smith"
    assert updated_client["datetime_lastmodified"] > client["datetime_lastmodified"]


def test_delete_client(mock_config, clients_manager):
    client_id = clients_manager.add_client(**client_data)
    clients_manager.delete_client(client_id)
    try:
        clients_manager.get_decrypted_client(client_id)
        assert (
            False
        ), "Expected ClientNotFound exception when retrieving a deleted client"
    except ClientNotFound as e:
        assert e.client_id == client_id


def test_enter_client_cli(mock_config, clients_manager, monkeypatch):
    # simulate the commandline input
    inputs = iter(client_data)

    def mock_input(prompt):
        return client_data[next(inputs)]

    monkeypatch.setattr("builtins.input", mock_input)

    client_id = enter_client_cli(clients_manager)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "John"
    assert client["last_name"] == "Doe"


def test_enter_client_untiscsv(mock_config, clients_manager, mock_webuntis):
    client_id = enter_client_untiscsv(clients_manager, mock_webuntis, school=None)
    client = clients_manager.get_decrypted_client(client_id=client_id)
    assert client["first_name"] == "Max"
    assert client["last_name"] == "Mustermann"


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
