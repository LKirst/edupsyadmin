from pathlib import Path

import pypdf

from edupsy_admin.api.fill_form import fill_form

# Sample client data
client_data = {
    "client_id": 123,
    "first_name": "John",
    "notenschutz": False,
    "nachteilsausgleich": True,
}


def test_fill_form(pdf_form: str, tmp_path: Path) -> None:
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
