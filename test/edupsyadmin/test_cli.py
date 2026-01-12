"""Test suite for the cli module.

The script can be executed on its own or incorporated into a larger test suite.
However the tests are run, be aware of which version of the module is actually
being tested. If the library is installed in site-packages, that version takes
precedence over the version in this project directory. Use a virtualenv test
environment or setuptools develop mode to test against the development version.

"""

import os
from pathlib import Path
from shlex import split
from subprocess import call
from sys import executable
from unittest.mock import patch

import pytest

# I'm not importing ClientsManager direclty here because then I might mask
# errors that come up when ClientsManager is not imported in cli.py
from edupsyadmin.api import managers
from edupsyadmin.cli import (
    command_create_documentation,
    command_delete_client,
    command_edit_config,
    command_get_clients,
    command_new_client,
    command_set_client,
    main,
)
from edupsyadmin.core.logger import Logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

testing_logger = Logger("clitest_logger")


@pytest.fixture
def mock_client(mock_keyring, clients_manager, sample_client_dict):
    """Fixture to set up a client for testing."""
    client_id = clients_manager.add_client(**sample_client_dict)
    return client_id, clients_manager.database_url


@pytest.fixture
def change_wd(tmp_path):
    original_directory = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_directory)


@pytest.fixture(
    params=(
        "--help",
        "info",
        "info --help",
        "new_client --help",
        "set_client --help",
        "create_documentation --help",
        "get_clients --help",
        "flatten_pdfs --help",
        "taetigkeitsbericht --help",
        "delete_client --help",
        "edit_config --help",
    )
)
def command(request):
    """Return the command to run."""
    return request.param


class TestBasicSanityCheck:
    def test_main(self, command):
        """Test the main() function."""
        try:
            status = main(split(command))
        except SystemExit as ex:
            status = ex.code
        assert status == 0
        return

    def test_main_none(self):
        """Test the main() function with no arguments."""
        with pytest.raises(SystemExit) as exinfo:
            main([])  # displays a help message and exits gracefully
        assert exinfo.value.code == 1

    def test_script(self, command):
        """Test command line execution."""
        # Call with the --help option as a basic sanity check.
        # This creates a new Python interpreter instance that doesn't inherit mocks.
        cmdl = f"{executable} -m edupsyadmin.cli {command} --help"
        assert call(cmdl.split()) == 0
        return


def test_defaults_are_used(mock_config):
    """Test that default values for app_uid and database_url are used."""
    from edupsyadmin.cli import APP_UID, DEFAULT_DB_URL

    with patch("edupsyadmin.cli.command_info", autospec=True) as mock_command_info:
        main(split(f"-c {mock_config} info"))

        mock_command_info.assert_called_once()
        call_kwargs = mock_command_info.call_args.kwargs

        assert call_kwargs.get("app_uid") == APP_UID
        assert call_kwargs.get("database_url") == DEFAULT_DB_URL


def test_config_template(mock_keyring, tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("tmp", numbered=True)
    database_path = tmp_dir / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    config_path = str(tmp_dir / "mock_conf.yml")
    args = [
        "-w",
        "DEBUG",
        "-c",
        config_path,
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
        "info",
    ]
    assert main(args) == 0
    assert os.path.isfile(config_path), (
        f"Config file was not initialized: {config_path}"
    )


def test_new_client(mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    command_new_client(
        app_username=TEST_USERNAME,
        app_uid=TEST_UID,
        database_url=database_url,
        salt_path=salt_path,
        csv=str(mock_webuntis),
        name="MustermErika1",
        school="FirstSchool",
        keepfile=False,
        import_config=None,
    )

    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    client = clients_manager.get_decrypted_client(client_id=1)
    assert client["first_name_encr"] == "Erika"
    assert client["last_name_encr"] == "Mustermann"


def test_get_clients_all(capsys, mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange
    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    clients_manager.add_client(
        school="FirstSchool",
        gender_encr="f",
        class_name="11TKKG",
        first_name_encr="Erika",
        last_name_encr="Mustermann",
        birthday_encr="2000-12-24",
    )

    # Act
    command_get_clients(
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

    # Assert
    stdout, _ = capsys.readouterr()
    assert "Mustermann" in stdout
    assert "Erika" in stdout


def test_get_clients_single(capsys, mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange
    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    clients_manager.add_client(
        school="FirstSchool",
        gender_encr="f",
        class_name="11TKKG",
        first_name_encr="Erika",
        last_name_encr="Mustermann",
        birthday_encr="2000-12-24",
    )
    clients_manager.add_client(
        school="FirstSchool",
        gender_encr="m",
        class_name="11TKKG",
        first_name_encr="Max",
        last_name_encr="Mustermann",
        birthday_encr="2000-01-01",
    )

    # Act
    command_get_clients(
        app_username=TEST_USERNAME,
        app_uid=TEST_UID,
        database_url=database_url,
        salt_path=salt_path,
        nta_nos=False,
        school=None,
        client_id=1,
        out=None,
        tui=False,
        columns=None,
    )

    # Assert
    stdout, _ = capsys.readouterr()
    assert "Mustermann" in stdout
    assert "Erika" in stdout
    assert "Max" not in stdout


def test_set_client(capsys, mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange
    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    clients_manager.add_client(
        school="FirstSchool",
        gender_encr="f",
        class_name="11TKKG",
        first_name_encr="Erika",
        last_name_encr="Mustermann",
        birthday_encr="2000-12-24",
    )

    # Act
    command_set_client(
        app_username=TEST_USERNAME,
        app_uid=TEST_UID,
        database_url=database_url,
        salt_path=salt_path,
        client_id=[1],
        key_value_pairs=["street_encr=Veränderte Straße 5", "class_name=42ab"],
    )

    # Assert
    client = clients_manager.get_decrypted_client(client_id=1)
    assert client["street_encr"] == "Veränderte Straße 5"
    assert client["class_name"] == "42ab"


# TODO: test inject_data
def test_create_documentation(
    tmp_path, mock_webuntis, mock_keyring, mock_config, pdf_forms, change_wd
):
    testing_logger.start(level="DEBUG")
    testing_logger.debug(f"config path: {mock_config}")

    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange
    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    client_id = clients_manager.add_client(
        school="FirstSchool",
        gender_encr="f",
        class_name="11TKKG",
        first_name_encr="Erika",
        last_name_encr="Mustermann",
        birthday_encr="2000-12-24",
    )

    # Act
    command_create_documentation(
        app_username=TEST_USERNAME,
        app_uid=TEST_UID,
        database_url=database_url,
        salt_path=salt_path,
        client_id=[client_id],
        form_set="lrst",
        form_paths=None,
        inject_data=None,
    )

    # Assert
    output_paths = [f"{client_id}_{Path(path).name}" for path in pdf_forms]
    for path in output_paths:
        assert os.path.exists(path), (
            f"Output file {path} was not created in {os.getcwd()}"
        )


def test_delete_client(mock_keyring, mock_config, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    salt_path = tmp_path / "salt.txt"

    # Arrange
    clients_manager = managers.ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=salt_path,
    )
    client_id = clients_manager.add_client(
        school="FirstSchool",
        gender_encr="f",
        class_name="11TKKG",
        first_name_encr="Erika",
        last_name_encr="Mustermann",
        birthday_encr="2000-12-24",
    )

    # Act
    command_delete_client(
        app_username=TEST_USERNAME,
        app_uid=TEST_UID,
        database_url=database_url,
        salt_path=salt_path,
        client_id=client_id,
    )

    # Assert
    with pytest.raises(Exception):
        clients_manager.get_decrypted_client(client_id=client_id)


def test_edit_config_command(mock_config):
    """Test that the edit_config command starts the TUI."""
    with patch("edupsyadmin.cli.lazy_import") as mock_lazy_import:
        # Prevent the app from actually running
        mock_app_instance = mock_lazy_import.return_value.ConfigEditorApp.return_value
        mock_app_instance.run.return_value = None

        # Call the command function
        command_edit_config(config_path=mock_config)

        # Assert that the app was initialized with the correct config path
        mock_lazy_import.return_value.ConfigEditorApp.assert_called_once_with(
            mock_config
        )

        # Assert that the app was run
        mock_app_instance.run.assert_called_once()


# TODO: Do the same for `get_clients --tui` and `edit_client --tui`
def test_create_documentation_tui(mock_config):
    """Test that `create_documentation --tui` starts the FillFormApp."""
    with patch("edupsyadmin.cli.lazy_import") as mock_lazy_import:
        # Prevent the app from actually running
        mock_app_instance = mock_lazy_import.return_value.FillFormApp.return_value
        mock_app_instance.run.return_value = None

        # Call the main function with the mock config and the TUI flag
        main(split(f"-c {mock_config} create_documentation --tui"))

        # Assert that the app was initialized
        mock_lazy_import.return_value.FillFormApp.assert_called_once()
        # Assert that a clients_manager was passed to the app's constructor
        assert (
            "clients_manager"
            in mock_lazy_import.return_value.FillFormApp.call_args.kwargs
        )

        # Assert that the app was run
        mock_app_instance.run.assert_called_once()


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
