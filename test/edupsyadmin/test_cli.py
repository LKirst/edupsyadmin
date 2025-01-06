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
import yaml

from edupsyadmin.cli import main
from edupsyadmin.core.encrypt import _convert_conf_to_dict


@pytest.fixture
def client(mock_keyring, clients_manager, sample_client_dict):
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


def test_main(command):
    """Test the main() function."""
    try:
        status = main(split(command))
    except SystemExit as ex:
        status = ex.code
    assert status == 0
    return


def test_main_none():
    """Test the main() function with no arguments."""
    with pytest.raises(SystemExit) as exinfo:
        main([])  # displays a help message and exits gracefully
    assert exinfo.value.code == 1


def test_script(command):
    """Test command line execution."""
    # Call with the --help option as a basic sanity check.
    # This creates a new Python interpreter instance that doesn't inherit mocks.
    cmdl = f"{executable} -m edupsyadmin.cli {command} --help"
    assert 0 == call(cmdl.split())
    return


def test_new_client(mock_keyring, mock_config, mock_webuntis, tmp_path):
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    args = [
        "-c",
        str(mock_config[0]),
        "new_client",
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


@pytest.mark.parametrize("pdf_forms", [3], indirect=True)
def test_create_documentation(mock_keyring, client, pdf_forms, change_wd):
    from edupsyadmin.core.config import config

    client_id, database_url = client
    config.form_set.lrst = [str(path) for path in pdf_forms]  # override the sample_pdfs
    with open(str(config.core.config[0]), "w", encoding="UTF-8") as f:
        dictyaml = _convert_conf_to_dict(config)  # convert to dict for pyyaml
        yaml.dump(dictyaml, f)  # write the config to file for main()

    args = [
        "-c",
        str(config.core.config[0]),
        "create_documentation",
        "--database_url",
        database_url,
        "--form_set",
        "lrst",
        str(client_id),
    ]
    assert 0 == main(args)

    # I've changed the wd with a fixture, so I can check without an absolute path
    output_paths = [f"{client[0]}_{Path(path).name}" for path in pdf_forms]
    for path in output_paths:
        assert os.path.exists(
            path
        ), f"Output file {path} was not created in {os.getcwd()}"


# Make the script executable.
if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
