from pathlib import Path

import pypdf

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.api.fill_form import fill_form


def test_fill_form(
    mock_config, pdf_forms: list, tmp_path: Path, client_dict_internal: dict
) -> None:
    """Test the fill_form function."""
    clientd = add_convenience_data(client_dict_internal)
    fill_form(clientd, pdf_forms, out_dir=tmp_path, use_fillpdf=True)

    for i, form in enumerate(pdf_forms):
        output_pdf_path = tmp_path / f"{clientd['client_id']}_{form.name}"
        assert output_pdf_path.exists(), "Output PDF was not created."

        if i == 0:
            with open(output_pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                form_data = reader.get_form_text_fields()
                assert (
                    form_data["first_name_encr"] == clientd["first_name_encr"]
                ), f"first_name_encr was not filled correctly for client {clientd}"

                checkbox_data = reader.get_fields()
                expected_nos = "/Yes" if clientd["notenschutz"] else "/Off"
                expected_nta = "/Yes" if clientd["nachteilsausgleich"] else "/Off"
                assert (
                    checkbox_data["notenschutz"].get("/V", None) == expected_nos
                ), f"notenschutz was not filled correctly for client {clientd}"
                assert (
                    checkbox_data["nachteilsausgleich"].get("/V", None) == expected_nta
                ), f"nachteilsausgleich was not filled correctly for client {clientd}"
