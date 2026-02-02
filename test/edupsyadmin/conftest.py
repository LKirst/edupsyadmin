import importlib.resources
import os
import shutil
from collections.abc import Generator
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import keyring
import pytest
import yaml
from cryptography.fernet import Fernet
from keyring.backends.null import Keyring as NullKeyring
from sample_pdf_form import create_pdf_form
from sample_webuntis_export import create_sample_webuntis_export

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import Logger, logger
from edupsyadmin.db import Base

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

testing_logger = Logger("conftest_logger")


@pytest.fixture(autouse=True)
def _reset_globals():
    """Reset singletons after every test to prevent flaky tests."""
    yield
    config._instance = None
    encr._fernet = None


@pytest.fixture(autouse=True)
def clear_metadata():
    Base.metadata.clear()
    yield


@pytest.fixture(autouse=True, scope="session")
def setup_logging() -> Generator[None]:
    """
    Fixture to set up logging. Remember to use the
    pytest --log-cli-level=DEBUG --capture=tee-sys flags if you want to see
    logging messages even if the test doesn't fail.
    """
    logger.start(level="DEBUG")
    testing_logger.start(level="DEBUG")
    yield
    logger.stop()


@pytest.fixture(scope="session")
def monkeysession():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(autouse=True, scope="function")
def mock_keyring(monkeypatch):
    """A mock keyring that stores secrets in a dictionary."""
    store = {}

    def get_credential(service, username):
        password = store.get(f"{service}:{username}")
        if password is None:
            return None
        cred = MagicMock()
        cred.password = password
        return cred

    def set_password(service, username, password):
        store[f"{service}:{username}"] = password

    def delete_password(service, username):
        key = f"{service}:{username}"
        if key in store:
            del store[key]
        else:
            raise keyring.errors.PasswordDeleteError("Password not found")

    # Mock the main functions used by the app
    monkeypatch.setattr(keyring, "get_credential", get_credential)
    monkeypatch.setattr(keyring, "set_password", set_password)
    monkeypatch.setattr(keyring, "delete_password", delete_password)

    # Also mock get_keyring() to prevent it from finding a real backend
    # and to avoid the "no backends found" warning.
    null_keyring = NullKeyring()
    monkeypatch.setattr(keyring, "get_keyring", lambda: null_keyring)


@pytest.fixture(scope="function")
def mock_config(
    tmp_path_factory: pytest.TempPathFactory, pdf_forms, request
) -> Generator[str]:
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    conf_path = tmp_path_factory.mktemp("tmp", numbered=True) / "mock_conf.yml"
    shutil.copy(template_path, conf_path)
    testing_logger.debug(
        f"mock_config fixture (test: {request.node.name}) - conf_path: {conf_path}"
    )
    config.load(conf_path)

    # set or override some config values
    config.core.config = conf_path
    config.core.app_username = f"user_read_from_file-{request.node.name}"
    config.core.logging = "DEBUG"
    config.form_set["lrst"] = [str(path) for path in pdf_forms]

    # write the changed config to file
    with open(config.core.config, "w", encoding="UTF-8") as f:
        # convert to dict for pyyaml, excluding the runtime 'config' path
        dictyaml = config.model_dump(exclude={"core": {"config"}})
        yaml.dump(dictyaml, f)

    # set different username than written to file to test which one is used
    config.core.app_username = f"user_set_in_fixture-{request.node.name}"

    # app uid is not set in the config, so don't write it to file
    config.core.app_uid = "example.com"

    yield conf_path
    os.remove(conf_path)


@pytest.fixture(scope="function")
def mock_config_snapshots(
    tmp_path_factory: pytest.TempPathFactory, request
) -> Generator[str]:
    """
    If I use the mock_config from above, shapshots are different on every
    machine because the pdf paths are absolute.
    """
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    conf_path = tmp_path_factory.mktemp("tmp", numbered=True) / "mock_conf.yml"
    shutil.copy(template_path, conf_path)
    config.load(conf_path)

    # set or override some config values
    config.core.config = conf_path
    config.core.app_username = f"user_read_from_file-{request.node.name}"
    config.core.logging = "DEBUG"
    del config.school["SecondSchool"]  # keep it simple for snapshots

    # write the changed config to file
    with open(config.core.config, "w", encoding="UTF-8") as f:
        # convert to dict for pyyaml, excluding the runtime 'config' path
        dictyaml = config.model_dump(exclude={"core": {"config"}})
        yaml.dump(dictyaml, f)

    # set different username than written to file to test which one is used
    config.core.app_username = f"user_set_in_fixture-{request.node.name}"

    # app uid is not set in the config, so don't write it to file
    config.core.app_uid = "example.com"

    yield conf_path
    os.remove(conf_path)


@pytest.fixture
def mock_salt_path(tmp_path):
    salt_path = tmp_path / "salt.txt"
    yield salt_path


@pytest.fixture
def mock_webuntis(tmp_path: Path) -> Path:
    webuntis_path = tmp_path / "webuntis.csv"
    create_sample_webuntis_export(webuntis_path)
    testing_logger.debug(f"webuntis_path: {webuntis_path}")
    return webuntis_path


@pytest.fixture
def client_dict_all_str() -> dict[str, str]:
    return {
        "client_id": "",
        "school": "FirstSchool",
        "gender_encr": "m",
        "entry_date": "2021-06-30",
        "class_name": "11TKKG",
        "first_name_encr": "John",
        "last_name_encr": "Doe",
        "birthday_encr": "1990-01-01",
        "street_encr": "123 Main St",
        "city_encr": "New York",
        "telephone1_encr": "555-1234",
        "email_encr": "john.doe@example.com",
        "nos_rs": "0",
        "nta_zeitv_vieltext": "10",
        "nta_nos_end_grade": "11",
        "lrst_diagnosis_encr": "iLst",
        "lrst_last_test_date_encr": "2025-05-11",
        "lrst_last_test_by_encr": "schpsy",
        "keyword_taet_encr": "slbb.slb.sonstige",
    }


@pytest.fixture(
    params=[
        {
            "client_id": None,
            "school": "FirstSchool",
            "gender_encr": "m",
            "entry_date": date(2021, 6, 30),
            "class_name": "11TKKG",
            "first_name_encr": "John",
            "last_name_encr": "Doe",
            "birthday_encr": "1990-01-01",
            "street_encr": "123 Main St",
            "city_encr": "New York",
            "telephone1_encr": "555-1234",
            "email_encr": "john.doe@example.com",
            "nos_rs": False,
            "nos_les": False,
            "nta_zeitv_vieltext": 10,
            "nta_nos_end_grade": 11,
            "lrst_diagnosis_encr": "iLst",
            "lrst_last_test_date_encr": date(2025, 5, 11),
            "lrst_last_test_by_encr": "schpsy",
            "keyword_taet_encr": "slbb.slb.sonstige",
        },
        {
            "client_id": 2,
            "school": "SecondSchool",
            "gender_encr": "f",
            "entry_date": date(2021, 6, 30),
            "class_name": "Ki12",
            "first_name_encr": "Äöüß",
            "last_name_encr": "Müller",
            "birthday_encr": "1990-01-01",
            "street_encr": "Umlautstraße 5ä",
            "city_encr": "München",
            "telephone1_encr": "+555-1234",
            "email_encr": "example@example.com",
            "nos_rs": True,
            "nta_zeitv_vieltext": None,
            "nta_nos_end_grade": None,
            "lrst_diagnosis_encr": "",
            "lrst_last_test_date_encr": "",
            "lrst_last_test_by_encr": "",
            "keyword_taet_encr": "",
        },
    ],
    scope="session",
)
def client_dict_set_by_user(request) -> dict[str, Any]:
    """
    The data the user sets [works with clients.__init__()].
    """
    return request.param


@pytest.fixture(
    params=[
        {
            "client_id": None,
            "school": "FirstSchool",
            "gender_encr": "m",
            "entry_date": date(2021, 6, 30),
            "class_name": "11TKKG",
            "class_int": 11,
            "first_name_encr": "John",
            "last_name_encr": "Doe",
            "birthday_encr": "1990-01-01",
            "street_encr": "123 Main St",
            "city_encr": "New York",
            "telephone1_encr": "555-1234",
            "email_encr": "john.doe@example.com",
            "nos_rs": True,
            "nos_les": False,
            "notenschutz": True,
            "nta_zeitv_vieltext": 10,
            "nachteilsausgleich": True,
            "nta_nos_end": True,
            "nta_nos_end_grade": 11,
            "lrst_diagnosis_encr": "iLst",
            "lrst_last_test_date_encr": date(2025, 5, 11),
            "lrst_last_test_by_encr": "schpsy",
            "document_shredding_date": date(2025, 12, 24),
            "keyword_taet_encr": "slbb.slb.sonstige",
        },
        {
            "client_id": 2,
            "school": "SecondSchool",
            "gender_encr": "f",
            "entry_date": date(2021, 6, 30),
            "class_name": "Ki12",
            "class_int": 12,
            "first_name_encr": "Äöüß",
            "last_name_encr": "Müller",
            "birthday_encr": "1990-01-01",
            "street_encr": "Umlautstraße 5ä",
            "city_encr": "München",
            "telephone1_encr": "+555-1234",
            "email_encr": "example@example.com",
            "nos_rs": False,
            "nos_les": False,
            "notenschutz": False,
            "nta_zeitv_vieltext": None,
            "nachteilsausgleich": False,
            "nta_nos_end": False,
            "nta_nos_end_grade": None,
            "lrst_diagnosis_encr": "",
            "lrst_last_test_date_encr": "",
            "lrst_last_test_by_encr": "",
            "document_shredding_date": date(2025, 12, 24),
            "keyword_taet_encr": "",
        },
    ],
    scope="session",
)
def client_dict_internal(request) -> dict[str, Any]:
    """
    The attributes of a clients object. Includes data that the clients object
    sets internally.
    """
    return request.param


@pytest.fixture
def clients_manager(tmp_path, mock_salt_path, mock_config):
    """
    Create a clients_manager.
    Initialises the global encr instance.
    """

    # initialize encr as in cli.py
    dummy_key = Fernet.generate_key()
    encr.set_key(dummy_key)

    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    manager = ClientsManager(database_url)

    yield manager


@pytest.fixture
def pdf_forms(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    """
    Create sample PDF forms for testing.

    Uses its own temporary directory to avoid interfering with tests that
    manage their own `tmp_path`.
    """
    forms_dir = tmp_path_factory.mktemp("pdf_forms")
    sample_files = [
        Path("test/edupsyadmin/data/sample_form_mantelbogen.pdf").resolve(),
        Path("test/edupsyadmin/data/sample_form_anschreiben.pdf").resolve(),
        Path("test/edupsyadmin/data/sample_form_stellungnahme.pdf").resolve(),
    ]
    testing_logger.debug(f"cwd: {os.getcwd()}")
    pdf_form_paths = []

    reportlab_form_filename = "sample_form_reportlab.pdf"
    reportlab_form_path = forms_dir / reportlab_form_filename
    create_pdf_form(str(reportlab_form_path))
    pdf_form_paths.append(reportlab_form_path)

    pdf_form_paths.extend(sample_files)
    testing_logger.debug(f"PDF forms fixture created at {pdf_form_paths}")

    return pdf_form_paths
