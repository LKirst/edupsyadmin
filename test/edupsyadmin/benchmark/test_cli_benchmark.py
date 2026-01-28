import argparse

import pytest

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.cli.commands import get_clients as get_clients_command

# Using constants from test_cli.py for consistency
TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"


@pytest.mark.parametrize("num_clients", [10, 100, 1000])
def test_get_clients_benchmark(
    benchmark, mock_keyring, mock_config, tmp_path, num_clients
):
    """Benchmark the get_clients command."""
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange: Set up a database with a significant number of clients
    clients_manager = ClientsManager(
        database_url=database_url,
    )
    for i in range(num_clients):  # Add clients for the benchmark
        clients_manager.add_client(
            school="FirstSchool",
            gender_encr="f",
            class_name="11TKKG",
            first_name_encr=f"Erika_{i}",
            last_name_encr="Mustermann",
            birthday_encr="2000-12-24",
        )

    def run_command():
        # Act: Run the command that is being benchmarked
        args = argparse.Namespace(
            app_username=TEST_USERNAME,
            app_uid=TEST_UID,
            database_url=database_url,
            salt_path=salt_path,
            nta_nos=False,
            school=None,
            client_id=None,
            out=None,
            tui=False,
            columns=None,
        )
        get_clients_command.execute(args)

    # Assert: benchmark the execution of the command
    benchmark(run_command)
