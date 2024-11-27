from pathlib import Path

import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from edupsy_admin.core.config import config
from edupsy_admin.core.logger import logger

conf_content = """
core:
  logging: WARN
  uid: example.com
school:
  test_school:
    school_name: Test School
    school_street: 123 Test St
    school_head_w_school: Principal of Test School
    end: 12
  default: test_school
"""

# ruff: noqa: E501
webuntis_content = """
name,longName,foreName,gender,birthDate,klasse.name,entryDate,exitDate,text,id,externKey,medicalReportDuty,schulpflicht,majority,address.email,address.mobile,address.phone,address.city,address.postCode,address.street,attribute.Notenschutz,attribute.Nachteilsausgleich
MustermMax1,Mustermann,Max,m,01.01.2000,11TKKG,12.09.2023,,,12345,4321,False,False,False,max.mustermann@example.de,491713920000,02214710000,München,80331,Beispiel Str. 55B,,
"""


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
    conf_path = tmp_path / "conf.yml"
    conf_path.write_text(conf_content.strip())
    print(f"conf_path: {conf_path}")
    config.load(str(conf_path))

    config.core = {}
    config.core.config = str(conf_path)
    config.username = "test_user_do_not_use"
    config.uid = "example.com"
    config.logging = "DEBUG"

    yield conf_path


@pytest.fixture
def mock_webuntis(tmp_path):
    webuntis_path = tmp_path / "webuntis.csv"
    webuntis_path.write_text(webuntis_content.strip())
    print(f"webuntis_path: {webuntis_path}")
    yield webuntis_path


def create_pdf_form(pdf_filename):
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    page_width, page_height = A4

    # a textfield widget
    c.drawString(100, 740, "first_name:")
    c.acroForm.textfield(
        name="first_name",
        tooltip="Enter text here",
        x=100,
        y=700,
        width=400,
        height=30,
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        maxlen=100,
        value="",
    )

    # two checkbox widgets (the value is either YES or OFF)
    c.drawString(130, 650, "notenschutz")
    c.acroForm.checkbox(
        name="notenschutz",
        x=100,
        y=650,
        size=20,
        borderWidth=3,
        borderColor=colors.black,
    )
    c.drawString(130, 550, "nachteilsausgleich")
    c.acroForm.checkbox(
        name="nachteilsausgleich",
        x=100,
        y=550,
        size=20,
        borderWidth=3,
        borderColor=colors.black,
    )

    # Radio buttons for gender selection
    # TODO: test whether the correct value was set
    c.drawString(100, 500, "Gender:")
    c.acroForm.radio(
        name="gender",
        value="f",
        x=100,
        y=480,
        size=20,
        borderWidth=1,
        borderColor=colors.black,
        fillColor=colors.white,
        forceBorder=True,
    )
    c.drawString(130, 480, "f")
    c.acroForm.radio(
        name="gender",
        value="m",
        x=100,
        y=450,
        size=20,
        borderWidth=1,
        borderColor=colors.black,
        fillColor=colors.white,
        forceBorder=True,
    )
    c.drawString(130, 450, "m")

    c.save()


@pytest.fixture
def pdf_form(tmp_path: Path) -> Path:
    pdf_form_path = tmp_path / "test_form.pdf"
    create_pdf_form(str(pdf_form_path))
    logger.debug(f"PDF form fixture created at {pdf_form_path}")
    return pdf_form_path
