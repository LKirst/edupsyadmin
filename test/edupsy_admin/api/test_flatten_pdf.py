from pathlib import Path

from pypdf import PdfReader

from edupsy_admin.api.fill_form import fill_form
from edupsy_admin.api.flatten_pdf import flatten_pdf

# Sample client data
client_data = {
    "client_id": 123,
    "first_name": "John",
    "notenschutz": False,
    "nachteilsausgleich": True,
}


def test_flatten_form(pdf_form: str, tmp_path: Path) -> None:
    # fill a form
    fill_form(client_data, [pdf_form], out_dir=tmp_path, use_fillpdf=True)
    filled_pdf_path = tmp_path / f"{client_data['client_id']}_test_form.pdf"

    # flatten the form
    flattened_pdf_path = tmp_path / f"print_{client_data['client_id']}_test_form.pdf"
    flatten_pdf(filled_pdf_path, "pdf2image")
    with open(flattened_pdf_path, "rb") as f:
        reader = PdfReader(f)
        form_data = reader.get_fields()
        assert form_data is None, "pdf form was not flattened"
