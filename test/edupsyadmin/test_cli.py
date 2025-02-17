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

import pytest

from edupsyadmin.cli import main
from edupsyadmin.core.logger import Logger

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


@pytest.fixture(params=("--help", "info"))
def command(request):
    """Return the command to run."""
    return request.param


class BasicSanityCheckTest:
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
        assert 0 == call(cmdl.split())
        return


# TODO: Test defaults for app_uid and database_url


def test_new_client(mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    args = [
        "-c",
        str(mock_config[0]),
        "new_client",
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
        "--csv",
        str(mock_webuntis),
        "--name",
        "MustermErika1",
        "--school",
        "FirstSchool",
    ]
    assert 0 == main(args)
    mock_keyring.assert_called_with(
        "example.com", "user_read_from_file-test_new_client"
    )


def test_get_clients(capsys, mock_keyring, mock_config, mock_webuntis, tmp_path):
    # add a client
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    args = [
        "-c",
        str(mock_config[0]),
        "new_client",
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
        "--csv",
        str(mock_webuntis),
        "--name",
        "MustermErika1",
        "--school",
        "FirstSchool",
    ]
    assert 0 == main(args)
    mock_keyring.assert_called_with(
        "example.com", "user_read_from_file-test_get_clients"
    )

    # test get_clients
    args = [
        "-c",
        str(mock_config[0]),
        "get_clients",
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
    ]
    assert 0 == main(args)
    mock_keyring.assert_called_with(
        "example.com", "user_read_from_file-test_get_clients"
    )
    stdout, stderr = capsys.readouterr()
    assert "Mustermann" in stdout
    assert "Erika" in stdout


def test_create_documentation(
    tmp_path, mock_webuntis, mock_keyring, mock_config, pdf_forms, change_wd
):
    testing_logger.start(level="DEBUG")
    testing_logger.debug(f"config path: {mock_config[0]}")

    # add a client
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    args = [
        "-c",
        str(mock_config[0]),
        "new_client",
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
        "--csv",
        str(mock_webuntis),
        "--name",
        "MustermErika1",
        "--school",
        "FirstSchool",
    ]
    assert 0 == main(args)
    mock_keyring.assert_called_with(
        "example.com", "user_read_from_file-test_create_documentation"
    )

    # create documentation
    client_id = 1
    args = [
        "-c",
        str(mock_config[0]),
        "create_documentation",
        "--app_uid",
        "example.com",
        "--database_url",
        database_url,
        "--form_set",
        "lrst",
        str(client_id),
    ]
    assert 0 == main(args)
    mock_keyring.assert_called_with(
        "example.com", "user_read_from_file-test_create_documentation"
    )

    # I've changed the wd with a fixture, so I can check without an absolute path
    output_paths = [f"{client_id}_{Path(path).name}" for path in pdf_forms]
    for path in output_paths:
        assert os.path.exists(
            path
        ), f"Output file {path} was not created in {os.getcwd()}"


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
