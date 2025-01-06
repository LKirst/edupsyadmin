import importlib.resources
import os
import shutil
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import keyring
import pytest
from sample_pdf_form import create_pdf_form
from sample_webuntis_export import create_sample_webuntis_export

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger

TEST_USERNAME = "test_user_do_not_use"
TEST_UID = "example.com"


@pytest.fixture(autouse=True)
def setup_logging() -> Generator[None, None, None]:
    """
    Fixture to set up logging. Remember to use the
    pytest --log-cli-level=DEBUG --capture=tee-sys flags if you want to see
    logging messages even if the test doesn't fail.
    """
    logger.start(level="DEBUG")
    yield
    logger.stop()


@pytest.fixture
def mock_keyring(monkeypatch):
    class MockCredential:
        def __init__(self, password: str):
            self.password = password

    mock_get_credential = Mock(
        side_effect=lambda service, username: MockCredential(password="mocked_password")
    )
    monkeypatch.setattr(keyring, "get_credential", mock_get_credential)

    return mock_get_credential


@pytest.fixture
def mock_config(tmp_path: Path) -> Generator[list[str], None, None]:
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    conf_path = [str(tmp_path / "mock_conf.yml")]
    shutil.copy(template_path, conf_path[0])
    print(f"mock_config fixture - conf_path: {conf_path}")
    config.load(conf_path)

    # set or override some config values
    config.core.config = conf_path
    config.core.app_username = "test_user_do_not_use"
    config.core.app_uid = "example.com"
    config.core.logging = "DEBUG"

    yield conf_path
    os.remove(conf_path[0])


@pytest.fixture
def mock_webuntis(tmp_path: Path) -> Path:
    webuntis_path = tmp_path / "webuntis.csv"
    create_sample_webuntis_export(webuntis_path)
    print(f"webuntis_path: {webuntis_path}")
    return webuntis_path


@pytest.fixture(
    params=[
        {
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
            "notenschutz": False,
            "nachteilsausgleich": True,
            "lrst_diagnosis": "iLrst",
            "nta_sprachen": 10,
        },
        {
            "client_id": 2,
            "school": "SecondSchool",
            "gender": "f",
            "entry_date": "2021-06-30",
            "class_name": "Ki12",
            "first_name": "Äöüß",
            "last_name": "Müller",
            "birthday": "1990-01-01",
            "street": "Umlautstraße 5ä",
            "city": "München",
            "telephone1": "+555-1234",
            "email": "example@example.com",
            "notenschutz": True,
            "nachteilsausgleich": True,
            "lrst_diagnosis": "lrst",
            "nta_sprachen": None,
        },
    ]
)
def sample_client_dict(request) -> dict[str, any]:
    return request.param


@pytest.fixture()
def clients_manager(tmp_path, mock_config, mock_keyring):
    """Create a clients_manager"""
    database_path = tmp_path / "test.sqlite"
    database_url = f"sqlite:///{database_path}"
    manager = ClientsManager(
        database_url,
        app_uid=TEST_UID,
        app_username=TEST_USERNAME,
        config_path=mock_config,
    )

    yield manager


@pytest.fixture
def pdf_forms(tmp_path: Path, request: pytest.FixtureRequest) -> list[Path]:
    """
    Use with
    @pytest.mark.parametrize("pdf_forms", [3], indirect=True)
    to create the desired number of files
    """
    files = [
        Path("test/edupsyadmin/data/sample_form_mantelbogen.pdf").resolve(),
        Path("test/edupsyadmin/data/sample_form_anschreiben.pdf").resolve(),
    ]
    print(f"cwd: {os.getcwd()}")
    num_files = getattr(request, "param", 1)
    pdf_form_paths = []
    for i in range(num_files):
        filename = "sample_form_reportlab.pdf"
        if i == 0:
            pdf_form_path = tmp_path / filename
            create_pdf_form(str(pdf_form_path))
            pdf_form_paths.append(pdf_form_path)
        else:
            pdf_form_paths.append(files[i - 1])
    logger.debug(f"PDF forms fixture created at {pdf_form_paths}")
    return pdf_form_paths
