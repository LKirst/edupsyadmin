from pathlib import Path

import pypdf
import pytest

from edupsyadmin.api.fill_form import fill_form

# Sample client data
client_dict_simple = {
    "client_id": 123,
    "first_name": "John",
    "notenschutz": False,
    "nachteilsausgleich": True,
}

client_dict_specialchars = {
    "client_id": 124,
    "first_name": "Äöüß",
    "notenschutz": False,
    "nachteilsausgleich": True,
}


@pytest.mark.parametrize("client_data", [client_dict_simple, client_dict_specialchars])
@pytest.mark.parametrize("pdf_forms", [3], indirect=True)
def test_fill_form(pdf_forms: list, tmp_path: Path, client_data: dict) -> None:
    """Test the fill_form function."""
    fill_form(client_data, pdf_forms, out_dir=tmp_path, use_fillpdf=True)

    for i, form in enumerate(pdf_forms):
        output_pdf_path = tmp_path / f"{client_data['client_id']}_{form.name}"
        assert output_pdf_path.exists(), "Output PDF was not created."

        if i == 0:
            with open(output_pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                form_data = reader.get_form_text_fields()
                assert (
                    form_data["first_name"] == client_data["first_name"]
                ), "first_name was not filled correctly."

                checkbox_data = reader.get_fields()
                assert (
                    checkbox_data["notenschutz"].get("/V", None) == "/Off"
                ), "notenschutz was not filled correctly."
                assert (
                    checkbox_data["nachteilsausgleich"].get("/V", None) == "/Yes"
                ), "nachteilsausgleich was not filled correctly."
