from pathlib import Path

import pypdf
import pytest

from edupsyadmin.api.fill_form import fill_form


@pytest.mark.parametrize("pdf_forms", [3], indirect=True)
def test_fill_form(pdf_forms: list, tmp_path: Path, sample_client_dict: dict) -> None:
    """Test the fill_form function."""
    fill_form(sample_client_dict, pdf_forms, out_dir=tmp_path, use_fillpdf=True)

    for i, form in enumerate(pdf_forms):
        output_pdf_path = tmp_path / f"{sample_client_dict['client_id']}_{form.name}"
        assert output_pdf_path.exists(), "Output PDF was not created."

        if i == 0:
            with open(output_pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                form_data = reader.get_form_text_fields()
                assert form_data["first_name"] == sample_client_dict["first_name"], (
                    f"first_name was not filled correctly for "
                    f"client {sample_client_dict}"
                )

                checkbox_data = reader.get_fields()
                expected_nos = "/Yes" if sample_client_dict["notenschutz"] else "/Off"
                expected_nta = (
                    "/Yes" if sample_client_dict["nachteilsausgleich"] else "/Off"
                )
                assert checkbox_data["notenschutz"].get("/V", None) == expected_nos, (
                    f"notenschutz was not filled correctly for "
                    f"client {sample_client_dict}"
                )
                assert (
                    checkbox_data["nachteilsausgleich"].get("/V", None) == expected_nta
                ), (
                    f"nachteilsausgleich was not filled correctly for "
                    f"client {sample_client_dict}"
                )
