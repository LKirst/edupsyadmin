import pytest

from edupsyadmin.api.managers import (
    ClientNotFound,
    enter_client_cli,
    enter_client_untiscsv,
)


class ManagersTest:
    def test_add_client(self, mock_keyring, clients_manager, sample_client_dict):
        client_id = clients_manager.add_client(**sample_client_dict)
        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert client["first_name"] == sample_client_dict["first_name"]
        assert client["last_name"] == sample_client_dict["last_name"]
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

    def test_edit_client(self, mock_keyring, clients_manager, sample_client_dict):
        client_id = clients_manager.add_client(**sample_client_dict)
        client = clients_manager.get_decrypted_client(client_id=client_id)
        updated_data = {"first_name_encr": "Jane", "last_name_encr": "Smith"}
        clients_manager.edit_client(client_id, updated_data)
        updated_client = clients_manager.get_decrypted_client(client_id)
        assert updated_client["first_name"] == "Jane"
        assert updated_client["last_name"] == "Smith"
        assert updated_client["datetime_lastmodified"] > client["datetime_lastmodified"]
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

    def test_delete_client(self, clients_manager, sample_client_dict):
        client_id = clients_manager.add_client(**sample_client_dict)
        clients_manager.delete_client(client_id)
        try:
            clients_manager.get_decrypted_client(client_id)
            assert (
                False
            ), "Expected ClientNotFound exception when retrieving a deleted client"
        except ClientNotFound as e:
            assert e.client_id == client_id

    def test_enter_client_cli(
        self, mock_keyring, clients_manager, monkeypatch, sample_client_dict
    ):
        # simulate the commandline input
        inputs = iter(sample_client_dict)

        def mock_input(prompt):
            return sample_client_dict[next(inputs)]

        monkeypatch.setattr("builtins.input", mock_input)

        client_id = enter_client_cli(clients_manager)
        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert client["first_name"] == sample_client_dict["first_name"]
        assert client["last_name"] == sample_client_dict["last_name"]
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")

    def test_enter_client_untiscsv(
        self, mock_keyring, clients_manager, mock_webuntis, sample_client_dict
    ):
        client_id = enter_client_untiscsv(
            clients_manager, mock_webuntis, school=None, name="MustermMax1"
        )
        client = clients_manager.get_decrypted_client(client_id=client_id)
        assert client["first_name"] == "Max"
        assert client["last_name"] == "Mustermann"
        assert client["school"] == "FirstSchool"
        mock_keyring.assert_called_with("example.com", "test_user_do_not_use")


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
