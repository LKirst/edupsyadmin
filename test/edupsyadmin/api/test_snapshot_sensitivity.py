from snapshot_utils import PDFSnapshotExtension

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.fill_form import fill_form
from edupsyadmin.api.flatten_pdf import flatten_pdf


def test_snapshot_sensitivity_checkbox(
    mock_config, pdf_forms, tmp_path, client_dict_internal
):
    """
    Verify that the snapshot comparison logic is strict enough to detect
    a single toggled checkbox (notenschutz).
    """
    # Use the ReportLab form
    form_path = next(f for f in pdf_forms if "reportlab" in f.name)

    # 1. Fill correctly (notenschutz = True)
    client_view_1 = ClientView.model_validate(client_dict_internal)
    client_view_1.notenschutz = True
    correct_dir = tmp_path / "cb_true"
    correct_dir.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_1, [form_path], out_dir=correct_dir)
    pdf_1 = correct_dir / f"{client_view_1.client_id}_{form_path.name}"
    flat_pdf_1 = flatten_pdf(pdf_1, output_prefix="flat_")

    # 2. Fill incorrectly (notenschutz = False)
    client_view_2 = ClientView.model_validate(client_dict_internal)
    client_view_2.notenschutz = False
    incorrect_dir = tmp_path / "cb_false"
    incorrect_dir.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_2, [form_path], out_dir=incorrect_dir)
    pdf_2 = incorrect_dir / f"{client_view_2.client_id}_{form_path.name}"
    flat_pdf_2 = flatten_pdf(pdf_2, output_prefix="flat_")

    # 3. Compare
    extension = PDFSnapshotExtension()

    # Convert PDFs to PNG bytes using the extension's serialize method
    png_bytes_1 = extension.serialize(flat_pdf_1)
    png_bytes_2 = extension.serialize(flat_pdf_2)

    # The extension's matches method should return False (i.e., it should
    # DETECT the change)
    matches = extension.matches(serialized_data=png_bytes_1, snapshot_data=png_bytes_2)

    assert not matches, (
        f"Checkbox toggle was NOT detected. "
        f"The threshold ({extension.PERCENT_CHANGED_THRESHOLD}%) is likely too lax."
    )


def test_snapshot_sensitivity_radio_button(
    mock_config, pdf_forms, tmp_path, client_dict_internal
):
    """
    Verify that the snapshot comparison logic is strict enough to detect
    a single toggled radio button (lrst_schpsy).
    """
    # Use the ReportLab form
    form_path = next(f for f in pdf_forms if "reportlab" in f.name)

    # 1. Fill with first radio option (lrst_last_test_by_encr = "schpsy" -> 1)
    client_view_1 = ClientView.model_validate(client_dict_internal)
    client_view_1.lrst_last_test_by_encr = "schpsy"
    dir_1 = tmp_path / "radio_1"
    dir_1.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_1, [form_path], out_dir=dir_1)
    pdf_1 = dir_1 / f"{client_view_1.client_id}_{form_path.name}"
    flat_pdf_1 = flatten_pdf(pdf_1, output_prefix="flat_")

    # 2. Fill with second radio option (lrst_last_test_by_encr = "psychia" -> 2)
    client_view_2 = ClientView.model_validate(client_dict_internal)
    client_view_2.lrst_last_test_by_encr = "psychia"
    dir_2 = tmp_path / "radio_2"
    dir_2.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_2, [form_path], out_dir=dir_2)
    pdf_2 = dir_2 / f"{client_view_2.client_id}_{form_path.name}"
    flat_pdf_2 = flatten_pdf(pdf_2, output_prefix="flat_")

    # 3. Compare using the actual extension logic
    extension = PDFSnapshotExtension()

    png_bytes_1 = extension.serialize(flat_pdf_1)
    png_bytes_2 = extension.serialize(flat_pdf_2)

    matches = extension.matches(serialized_data=png_bytes_1, snapshot_data=png_bytes_2)

    assert not matches, (
        f"Radio button toggle was NOT detected. "
        f"The threshold ({extension.PERCENT_CHANGED_THRESHOLD}%) is likely too lax."
    )


def test_snapshot_sensitivity_text_field(
    mock_config, pdf_forms, tmp_path, client_dict_internal
):
    """
    Verify that the snapshot comparison logic is strict enough to detect
    a change in a text field (first_name_encr).
    """
    # Use the ReportLab form
    form_path = next(f for f in pdf_forms if "reportlab" in f.name)

    # 1. Fill with one name
    client_view_1 = ClientView.model_validate(client_dict_internal)
    client_view_1.first_name_encr = "Alice"
    dir_1 = tmp_path / "text_1"
    dir_1.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_1, [form_path], out_dir=dir_1)
    pdf_1 = dir_1 / f"{client_view_1.client_id}_{form_path.name}"
    flat_pdf_1 = flatten_pdf(pdf_1, output_prefix="flat_")

    # 2. Fill with another name
    client_view_2 = ClientView.model_validate(client_dict_internal)
    client_view_2.first_name_encr = "Bob"
    dir_2 = tmp_path / "text_2"
    dir_2.mkdir(parents=True, exist_ok=True)
    fill_form(client_view_2, [form_path], out_dir=dir_2)
    pdf_2 = dir_2 / f"{client_view_2.client_id}_{form_path.name}"
    flat_pdf_2 = flatten_pdf(pdf_2, output_prefix="flat_")

    # 3. Compare using the actual extension logic
    extension = PDFSnapshotExtension()

    png_bytes_1 = extension.serialize(flat_pdf_1)
    png_bytes_2 = extension.serialize(flat_pdf_2)

    matches = extension.matches(serialized_data=png_bytes_1, snapshot_data=png_bytes_2)

    assert not matches, (
        f"Text field change was NOT detected. "
        f"The threshold ({extension.PERCENT_CHANGED_THRESHOLD}%) is likely too lax."
    )
