from pathlib import Path
import pytest
import pypdf
from edupsy_admin.api.fill_form import fill_form
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
}


def create_pdf_form(pdf_filename):
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    page_width, page_height = letter

    c.drawString(100, 740, "first_name text field:")
    x = 100
    y = 700
    width = 400
    height = 30
    c.acroForm.textfield(
        name="first_name",
        tooltip="Enter text here",
        x=x,
        y=y,
        width=width,
        height=height,
        borderColor=colors.black,
        fillColor=colors.white,
        textColor=colors.black,
        forceBorder=True,
        maxlen=100,
        value="",
    )

    c.save()


@pytest.fixture
def pdf_form(tmp_path):
    pdf_form_path = tmp_path / "test_form.pdf"
    create_pdf_form(str(pdf_form_path))
    return pdf_form_path


def test_fill_form(pdf_form):
    """Test the fill_form function."""
    form_paths = [pdf_form]
    fill_form(client_data, form_paths, use_fillpdf=True)

    output_pdf_path = Path(f"{client_data['client_id']}_test_form.pdf")
    assert output_pdf_path.exists(), "Output PDF was not created."

    with open(output_pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        form_data = reader.get_form_text_fields()
        assert form_data["first_name"] == "John", "first_name was not filled correctly."
