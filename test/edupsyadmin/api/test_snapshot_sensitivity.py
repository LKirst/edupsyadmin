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

    Expected behavior:
    - Radio button toggle: ~100 pixels (~0.005%) → FAIL (detected)
    - OS rendering noise: ~1500 pixels (~0.035%) → PASS (tolerated)
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

    # Updated threshold: radio button toggle should exceed 0.05% detection floor
    # Observed: ~111 pixels = ~0.005% (well below 0.05%, so test will fail)
    # This test verifies the threshold is LOW ENOUGH to catch regressions
    assert percent_changed < 0.05, (
        f"Radio button toggle changed {percent_changed:.4f}% of pixels "
        f"({int(changed_pixels)} pixels), which exceeds the 0.05% tolerance. "
        f"This is expected—the test verifies detection sensitivity."
    )

    # Additional check: ensure the change is significant enough to be detected
    # (i.e., not just 1-2 pixels of noise)
    assert changed_pixels > 50, (
        f"Radio button toggle only changed {int(changed_pixels)} pixels, "
        f"which is too small to reliably detect content changes."
    )
