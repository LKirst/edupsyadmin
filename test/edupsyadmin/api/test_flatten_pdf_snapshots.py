import pytest

from edupsyadmin.api.add_convenience_data import add_convenience_data
from edupsyadmin.api.fill_form import fill_form
from edupsyadmin.api.flatten_pdf import (
    flatten_pdf,
)


@pytest.fixture
def filled_client_data(client_dict_internal, mock_config):
    """Prepare stable client data for snapshots."""
    clientd = add_convenience_data(client_dict_internal)
    # Override dynamic dates for stable snapshots
    clientd["today_date_de"] = "16.10.2025"
    clientd["school_year"] = "2025/2026"
    return clientd


def get_filled_pdf(tmp_path, form_path, client_data):
    """Fill a PDF form and return the path to the filled file."""
    fill_form(client_data, [form_path], out_dir=tmp_path, use_fillpdf=True)
    return tmp_path / f"{client_data.get('client_id')}_{form_path.name}"


@pytest.mark.parametrize("form_name", ["libreoffice", "reportlab"])
def test_flatten_pdf_pdf2image_snapshot(
    pdf_snapshot,
    pdf_forms,
    tmp_path,
    form_name,
    filled_client_data,
    mock_config,
):
    """Snapshot test for flattening a filled PDF with pdf2image."""
    # Find the requested form in pdf_forms
    form_path = next(f for f in pdf_forms if form_name in f.name)

    # Fill the form first
    filled_pdf = get_filled_pdf(tmp_path, form_path, filled_client_data)

    # Flatten the filled PDF
    flattened_pdf = flatten_pdf(
        filled_pdf,
        library="pdf2image",
        output_prefix="flat_p2i_",
    )

    assert pdf_snapshot == flattened_pdf


@pytest.mark.parametrize("form_name", ["libreoffice", "reportlab"])
def test_flatten_pdf_pypdf_snapshot(
    pdf_snapshot,
    pdf_forms,
    tmp_path,
    form_name,
    filled_client_data,
    mock_config,
):
    """Snapshot test for flattening a filled PDF with pdf2image."""
    # Find the requested form in pdf_forms
    form_path = next(f for f in pdf_forms if form_name in f.name)

    # Fill the form first
    filled_pdf = get_filled_pdf(tmp_path, form_path, filled_client_data)

    # Flatten the filled PDF
    flattened_pdf = flatten_pdf(
        filled_pdf,
        library="pypdf",
        output_prefix="flat_pypdf_",
    )

    assert pdf_snapshot == flattened_pdf


@pytest.mark.parametrize("form_name", ["libreoffice", "reportlab"])
def test_flatten_pdf_fillpdf_snapshot(
    pdf_snapshot,
    pdf_forms,
    tmp_path,
    form_name,
    filled_client_data,
    mock_config,
):
    """Snapshot test for flattening a filled PDF with fillpdf."""
    # Find the requested form in pdf_forms
    form_path = next(f for f in pdf_forms if form_name in f.name)

    # Fill the form first
    filled_pdf = get_filled_pdf(tmp_path, form_path, filled_client_data)

    # Flatten the filled PDF
    flattened_pdf = flatten_pdf(
        filled_pdf,
        library="fillpdf",
        output_prefix="flat_fill_",
    )

    assert pdf_snapshot == flattened_pdf
