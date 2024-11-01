from pathlib import Path
import pytest
import pypdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from edupsy_admin.core.logger import logger
from edupsy_admin.api.fill_form import fill_form

# Sample client data
client_data = {
    "client_id": 123,
    "school": "ABC School",
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
}


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

    c.save()


@pytest.fixture(autouse=True)
def setup_logging(caplog: pytest.LogCaptureFixture) -> None:
    """
    Fixture to set up logging. To always see logging, remember to use the
    pytest --log-cli-level=DEBUG --capture=tee-sys flags.
    """
    logger.start(level="DEBUG")
    yield
    logger.stop()


@pytest.fixture
def pdf_form(tmp_path: Path) -> Path:
    pdf_form_path = tmp_path / "test_form.pdf"
    create_pdf_form(str(pdf_form_path))
    logger.debug(f"PDF form fixture created at {pdf_form_path}")
    return pdf_form_path


def test_fill_form(
    pdf_form: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the fill_form function."""
    form_paths = [pdf_form]
    fill_form(client_data, form_paths, out_dir=tmp_path, use_fillpdf=True)

    output_pdf_path = tmp_path / f"{client_data['client_id']}_test_form.pdf"
    assert output_pdf_path.exists(), "Output PDF was not created."

    with open(output_pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        form_data = reader.get_form_text_fields()
        assert form_data["first_name"] == "John", "first_name was not filled correctly."

        checkbox_data = reader.get_fields()
        assert (
            checkbox_data["notenschutz"].get("/V", None) == "/Off"
        ), "notenschutz was not filled correctly."
        assert (
            checkbox_data["nachteilsausgleich"].get("/V", None) == "/Yes"
        ), "nachteilsausgleich was not filled correctly."
