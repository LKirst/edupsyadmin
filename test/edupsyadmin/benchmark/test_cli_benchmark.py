import argparse

import pytest
from cryptography.fernet import Fernet

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.migration import upgrade_db
from edupsyadmin.cli.commands import get_clients as get_clients_command
from edupsyadmin.core.encrypt import encr

# Using constants from test_cli.py for consistency
TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"


@pytest.mark.parametrize("num_clients", [10, 100, 1000])
def test_get_clients_benchmark(benchmark, mock_config, tmp_path, num_clients):
    """Benchmark the get_clients command."""
    # Set up encryption before database access
    encr.set_keys([Fernet.generate_key()])

    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange: Set up a database with a significant number of clients
    upgrade_db(database_url)
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
