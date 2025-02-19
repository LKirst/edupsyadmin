from pathlib import Path

from pypdf import PdfReader

from edupsyadmin.api.fill_form import fill_form
from edupsyadmin.api.flatten_pdf import flatten_pdf

# Sample client data
client_data = {
    "client_id": 123,
    "first_name": "John",
    "notenschutz": False,
    "nachteilsausgleich": True,
    "gender": "f",
    "address_multiline": "Somestreet 42\n12345 Sometown",
}


def test_flatten_form(pdf_forms: list, tmp_path: Path) -> None:
    fill_form(client_data, pdf_forms, out_dir=tmp_path, use_fillpdf=True)
    for form in pdf_forms:
        # fill a form
        filled_pdf_path = tmp_path / f"{client_data['client_id']}_{form.name}"
        assert filled_pdf_path.is_file()

        # flatten the form
        flattened_pdf_path = tmp_path / f"print_{client_data['client_id']}_{form.name}"
        flatten_pdf(filled_pdf_path, "pdf2image")
        assert flattened_pdf_path.is_file()
        with open(flattened_pdf_path, "rb") as f:
            reader = PdfReader(f)
            form_data = reader.get_fields()
            assert form_data is None, "pdf form was not flattened"
