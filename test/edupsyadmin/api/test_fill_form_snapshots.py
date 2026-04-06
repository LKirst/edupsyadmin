from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.api.fill_form import fill_form


def test_fill_form_mantelbogen_snapshot(
    pdf_snapshot, tmp_path, mock_config, pdf_forms, client_dict_internal
):
    """Visual snapshot test for the 'mantelbogen' PDF form."""
    clientd = add_convenience_data(client_dict_internal)

    # Find the mantelbogen form in pdf_forms
    form_path = next(f for f in pdf_forms if "mantelbogen" in f.name)

    fill_form(clientd, [form_path], out_dir=tmp_path, use_fillpdf=True)
    filled_pdf = tmp_path / f"{clientd.get('client_id')}_{form_path.name}"

    assert pdf_snapshot == filled_pdf


def test_fill_form_anschreiben_snapshot(
    pdf_snapshot, tmp_path, mock_config, pdf_forms, client_dict_internal
):
    """Visual snapshot test for the 'anschreiben' PDF form."""
    clientd = add_convenience_data(client_dict_internal)

    # Find the anschreiben form in pdf_forms
    form_path = next(f for f in pdf_forms if "anschreiben" in f.name)

    fill_form(clientd, [form_path], out_dir=tmp_path, use_fillpdf=True)
    filled_pdf = tmp_path / f"{clientd.get('client_id')}_{form_path.name}"

    assert pdf_snapshot == filled_pdf


def test_fill_form_stellungnahme_snapshot(
    pdf_snapshot, tmp_path, mock_config, pdf_forms, client_dict_internal
):
    """Visual snapshot test for the 'stellungnahme' PDF form."""
    clientd = add_convenience_data(client_dict_internal)

    # Find the stellungnahme form in pdf_forms
    form_path = next(f for f in pdf_forms if "stellungnahme" in f.name)

    fill_form(clientd, [form_path], out_dir=tmp_path, use_fillpdf=True)
    filled_pdf = tmp_path / f"{clientd.get('client_id')}_{form_path.name}"

    assert pdf_snapshot == filled_pdf


def test_fill_form_reportlab_snapshot(
    pdf_snapshot, tmp_path, mock_config, pdf_forms, client_dict_internal
):
    """Visual snapshot test for the reportlab-generated PDF form."""
    clientd = add_convenience_data(client_dict_internal)

    # Find the reportlab form in pdf_forms
    form_path = next(f for f in pdf_forms if "reportlab" in f.name)

    fill_form(clientd, [form_path], out_dir=tmp_path, use_fillpdf=True)
    filled_pdf = tmp_path / f"{clientd.get('client_id')}_{form_path.name}"

    assert pdf_snapshot == filled_pdf
