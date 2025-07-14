import importlib.resources
import os
import shutil
from collections.abc import Generator
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import keyring
import pytest
import yaml
from sample_pdf_form import create_pdf_form
from sample_webuntis_export import create_sample_webuntis_export

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config, convert_config_to_dict
from edupsyadmin.core.logger import Logger, logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"

testing_logger = Logger("conftest_logger")


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


@pytest.fixture(scope="session")
def mock_keyring(monkeysession):
    class MockCredential:
        def __init__(self, password: str):
            self.password = password

    mock_get_credential = Mock(
        side_effect=lambda service, username: MockCredential(password="mocked_password")
    )
    monkeysession.setattr(keyring, "get_credential", mock_get_credential)

    return mock_get_credential


@pytest.fixture(scope="function")
def mock_config(
    tmp_path_factory: pytest.TempPathFactory, pdf_forms, request
) -> Generator[list[str]]:
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    conf_path = [str(tmp_path_factory.mktemp("tmp", numbered=True) / "mock_conf.yml")]
    shutil.copy(template_path, conf_path[0])
    testing_logger.debug(
        f"mock_config fixture (test: {request.node.name}) - conf_path: {conf_path}"
    )
    config.load(conf_path)

    # set or override some config values
    config.core.config = conf_path
    config.core.app_username = f"user_read_from_file-{request.node.name}"
    config.core.logging = "DEBUG"
    config.form_set.lrst = [str(path) for path in pdf_forms]

    # write the changed config to file
    with open(str(config.core.config[0]), "w", encoding="UTF-8") as f:
        dictyaml = convert_config_to_dict(config)  # convert to dict for pyyaml
        yaml.dump(dictyaml, f)

    # set different username than written to file to test which one is used
    config.core.app_username = f"user_set_in_fixture-{request.node.name}"

    # app uid is not set in the config, so don't write it to file
    config.core.app_uid = "example.com"

    yield conf_path
    os.remove(conf_path[0])


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
        "lrst_diagnosis": "iLst",
        "lrst_last_test_date": "2025-05-11",
        "lrst_last_test_by": "schpsy",
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
            "nta_zeitv_vieltext": 10,
            "nta_nos_end_grade": 11,
            "lrst_diagnosis": "iLst",
            "lrst_last_test_date": date(2025, 5, 11),
            "lrst_last_test_by": "schpsy",
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
            "nos_les": False,
            "nta_zeitv_vieltext": None,
            "nta_nos_end_grade": None,
            "lrst_diagnosis": None,
            "lrst_last_test_date": None,
            "lrst_last_test_by": None,
        },
    ],
    scope="session",
)
def client_dict_set_by_user(request) -> dict[str, any]:
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
            "lrst_diagnosis": "iLst",
            "lrst_last_test_date": date(2025, 5, 11),
            "lrst_last_test_by": "schpsy",
            "document_shredding_date": date(2025, 12, 24),
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
            "lrst_diagnosis": None,
            "lrst_last_test_date": None,
            "lrst_last_test_by": None,
            "document_shredding_date": date(2025, 12, 24),
        },
    ],
    scope="session",
)
def client_dict_internal(request) -> dict[str, any]:
    """
    The attributes of a clients object. Includes data that the clients object
    sets internally.
    """
    return request.param


@pytest.fixture
def clients_manager(tmp_path, mock_salt_path, mock_config, mock_keyring):
    """Create a clients_manager"""
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    manager = ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        salt_path=mock_salt_path,
    )

    yield manager


@pytest.fixture
def pdf_forms(tmp_path: Path) -> list[Path]:
    sample_files = [
        Path("test/edupsyadmin/data/sample_form_mantelbogen.pdf").resolve(),
        Path("test/edupsyadmin/data/sample_form_anschreiben.pdf").resolve(),
        Path("test/edupsyadmin/data/sample_form_stellungnahme.pdf").resolve(),
    ]
    testing_logger.debug(f"cwd: {os.getcwd()}")
    pdf_form_paths = []

    reportlab_form_filename = "sample_form_reportlab.pdf"
    reportlab_form_path = tmp_path / reportlab_form_filename
    create_pdf_form(str(reportlab_form_path))
    pdf_form_paths.append(reportlab_form_path)

    pdf_form_paths.extend(sample_files)
    testing_logger.debug(f"PDF forms fixture created at {pdf_form_paths}")

    return pdf_form_paths
