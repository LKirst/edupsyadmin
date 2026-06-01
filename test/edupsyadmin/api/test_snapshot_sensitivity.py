from pdf2image import convert_from_path
from PIL import Image, ImageChops, ImageStat

from edupsyadmin.api.client_view import ClientView
from edupsyadmin.api.fill_form import fill_form


def test_snapshot_sensitivity_radio_button(
    mock_config, pdf_forms, tmp_path, client_dict_internal
):
    """
    Verify that the snapshot comparison logic in conftest.py is strict enough
    to detect a single toggled radio button, even if the rest of the
    document is identical.
    """
    # Use the ReportLab form
    form_path = next(f for f in pdf_forms if "reportlab" in f.name)

    # 1. Fill correctly (notenschutz = True)
    client_data_1 = ClientView.model_validate(client_dict_internal).model_dump()
    client_data_1["notenschutz"] = True
    correct_dir = tmp_path / "correct"
    correct_dir.mkdir(parents=True, exist_ok=True)
    fill_form(client_data_1, [form_path], out_dir=correct_dir)
    pdf_1 = correct_dir / f"{client_data_1['client_id']}_{form_path.name}"

    # 2. Fill incorrectly (notenschutz = False)
    client_data_2 = client_data_1.copy()
    client_data_2["notenschutz"] = False
    incorrect_dir = tmp_path / "incorrect"
    incorrect_dir.mkdir(parents=True, exist_ok=True)
    fill_form(client_data_2, [form_path], out_dir=incorrect_dir)
    pdf_2 = incorrect_dir / f"{client_data_2['client_id']}_{form_path.name}"

    # 3. Compare using the same logic as PDFSnapshotExtension.matches in conftest.py
    def get_png(pdf_path):
        images = convert_from_path(pdf_path, dpi=150)
        widths, heights = zip(*(i.size for i in images), strict=False)
        max_width = max(widths)
        total_height = sum(heights)
        combined = Image.new("RGB", (max_width, total_height))
        y_offset = 0
        for im in images:
            combined.paste(im, (0, y_offset))
            y_offset += im.size[1]
        return combined

    img1 = get_png(pdf_1)
    img2 = get_png(pdf_2)

    diff = ImageChops.difference(img1, img2)
    diff_gray = diff.convert("L")
    significant_diff_mask = diff_gray.point(lambda p: 1 if p > 100 else 0, mode="1")

    stat = ImageStat.Stat(significant_diff_mask)
    changed_pixels = stat.sum[0]
    total_pixels = img1.size[0] * img1.size[1]
    percent_changed = (changed_pixels / total_pixels) * 100

    # We expect a radio button change to be significantly ABOVE the 0.001% threshold.
    # Total pixels in A4 at 150dpi is approx 1240 * 1750 = 2.1M.
    # 0.001% of 2.1M is ~21 pixels.
    # A radio button toggle (observed at ~111 pixels) should be caught.

    assert percent_changed > 0.001, (
        f"Sensitivity failure! Toggled radio button only changed "
        f"{percent_changed:.4f}% of pixels, "
        f"which is below the detection threshold. "
        f"(Changed pixels: {int(changed_pixels)})"
    )
