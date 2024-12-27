import importlib.resources
import os
import shutil
from pathlib import Path

import pytest
from sample_pdf_form import create_pdf_form
from sample_webuntis_export import create_sample_webuntis_export

from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger


@pytest.fixture(autouse=True)
def setup_logging() -> None:
    """
    Fixture to set up logging. Remember to use the
    pytest --log-cli-level=DEBUG --capture=tee-sys flags if you want to see
    logging messages even if the test doesn't fail.
    """
    logger.start(level="DEBUG")
    yield
    logger.stop()


@pytest.fixture
def mock_config(tmp_path):
    template_path = importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
    conf_path = tmp_path / "mock_conf.yml"
    shutil.copy(template_path, conf_path)
    print(f"conf_path: {conf_path}")
    config.load(str(conf_path))

    config.core = {}
    config.core.config = str(conf_path)
    config.username = "test_user_do_not_use"
    config.uid = "example.com"
    config.logging = "DEBUG"

    yield conf_path
    os.remove(conf_path)


@pytest.fixture
def mock_webuntis(tmp_path):
    webuntis_path = tmp_path / "webuntis.csv"
    create_sample_webuntis_export(webuntis_path)
    print(f"webuntis_path: {webuntis_path}")
    yield webuntis_path


@pytest.fixture
def pdf_form(tmp_path: Path) -> Path:
    pdf_form_path = tmp_path / "test_form.pdf"
    create_pdf_form(str(pdf_form_path))
    logger.debug(f"PDF form fixture created at {pdf_form_path}")
    return pdf_form_path
