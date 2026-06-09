from pathlib import Path

from pypdf import PdfReader

from edupsyadmin.api.client_view import ClientView
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


def test_flatten_form(pdf_forms: list, tmp_path: Path, mock_config: Path) -> None:
    fill_form(
        ClientView.model_validate(client_data),
        pdf_forms,
        out_dir=tmp_path,
    )
    # Since len(pdf_forms) > 1, we expect a merged file
    filled_pdf_path = tmp_path / f"{client_data['client_id']}_merged.pdf"
    assert filled_pdf_path.is_file()

    # flatten the form
    flattened_pdf_path = tmp_path / f"print_{client_data['client_id']}_merged.pdf"
    flatten_pdf(filled_pdf_path)
    assert flattened_pdf_path.is_file()
    with flattened_pdf_path.open("rb") as f:
        reader = PdfReader(f)
        form_data = reader.get_fields()
        assert form_data is None, "pdf form was not flattened"


def test_flatten_encrypted_form(
    pdf_forms: list,
    tmp_path: Path,
    mock_config: Path,
) -> None:
    """Test flattening an encrypted PDF form."""
    password = "test_password"
    fill_form(
        ClientView.model_validate(client_data),
        pdf_forms,
        out_dir=tmp_path,
        password=password,
    )
    # Since len(pdf_forms) > 1, we expect a merged file
    filled_pdf_path = tmp_path / f"{client_data['client_id']}_merged.pdf"
    assert filled_pdf_path.is_file()

    # Verify it is encrypted
    with filled_pdf_path.open("rb") as f:
        reader = PdfReader(f)
        assert reader.is_encrypted

    # flatten the form
    flatten_pdf(filled_pdf_path, password=password)
    flattened_pdf_path = tmp_path / f"print_{client_data['client_id']}_merged.pdf"
    assert flattened_pdf_path.is_file()

    with flattened_pdf_path.open("rb") as f:
        reader = PdfReader(f)
        assert reader.is_encrypted
        reader.decrypt(password)
        form_data = reader.get_fields()
        assert form_data is None, "pdf form was not flattened"
