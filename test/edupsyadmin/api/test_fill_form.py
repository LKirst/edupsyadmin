from pathlib import Path
from unittest.mock import MagicMock

import pypdf

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.fill_form import batch_fill_forms, fill_form
from edupsyadmin.api.types import ClientRecord


def test_fill_form(
    mock_config, pdf_forms: list, tmp_path: Path, client_dict_internal: ClientRecord
) -> None:
    """Test the fill_form function."""
    clientd = ClientView.model_validate(client_dict_internal).model_dump()
    fill_form(clientd, pdf_forms, out_dir=tmp_path)

    for i, form in enumerate(pdf_forms):
        output_pdf_path = tmp_path / f"{clientd['client_id']}_{form.name}"
        assert output_pdf_path.exists(), "Output PDF was not created."

        if i == 0:
            with output_pdf_path.open("rb") as f:
                reader = pypdf.PdfReader(f)
                form_data = reader.get_form_text_fields()
                assert form_data["first_name_encr"] == clientd["first_name_encr"], (
                    f"first_name_encr was not filled correctly for client {clientd}"
                )

                btn_data = reader.get_fields()
                assert btn_data is not None
                expected_nos = "/Yes" if clientd["notenschutz"] else "/Off"
                expected_nta = "/Yes" if clientd["nachteilsausgleich"] else "/Off"
                assert btn_data["notenschutz"].get("/V", None) == expected_nos, (
                    f"notenschutz was not filled correctly for client {clientd}"
                )
                assert btn_data["nachteilsausgleich"].get("/V", None) == expected_nta, (
                    f"nachteilsausgleich was not filled correctly for client {clientd}"
                )

                expected_lrst_last_test_by = (
                    f"/{clientd['lrst_schpsy']}"
                    if clientd.get("lrst_schpsy")
                    else "/Off"
                )
                assert (
                    btn_data["lrst_schpsy"].get("/V", None)
                    == expected_lrst_last_test_by
                )


def test_batch_fill_forms(
    mock_config, pdf_forms: list, tmp_path: Path, client_dict_internal: ClientRecord
) -> None:
    """Test the batch_fill_forms function."""

    clients_manager = MagicMock()

    def get_view(cid):
        data = client_dict_internal.model_copy(update={"client_id": cid})
        return ClientView.model_validate(data)

    clients_manager.get_client_view.side_effect = get_view

    client_ids = [1, 2]
    results = batch_fill_forms(
        clients_manager,
        client_ids,
        pdf_forms,
        out_dir=tmp_path,
    )
    assert len(results) == 2
    assert all(res["success"] for res in results)
    assert clients_manager.get_client_view.call_count == 2

    for client_id in client_ids:
        for form in pdf_forms:
            output_pdf_path = tmp_path / f"{client_id}_{form.name}"
            assert output_pdf_path.exists()
