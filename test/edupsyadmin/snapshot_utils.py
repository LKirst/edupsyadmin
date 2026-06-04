import contextlib
import io
from pathlib import Path
from typing import Any

import pytest
from pdf2image import convert_from_path
from PIL import Image, ImageChops, ImageStat
from syrupy.extensions.image import PNGImageSnapshotExtension

from edupsyadmin.core.logger import Logger

snapshot_logger = Logger("snapshot_logger")

actual_snapshot_path_key = pytest.StashKey[Path]()


class PDFSnapshotExtension(PNGImageSnapshotExtension):
    """Extension for syrupy to handle PDF snapshots by converting them to PNG."""

    current_item: pytest.Item | None = None

    # Thresholds for OS-level rendering differences
    AVG_DIFF_THRESHOLD = 1.0
    PERCENT_CHANGED_THRESHOLD = 0.001

    def matches(self, *, serialized_data: Any, snapshot_data: Any) -> bool:
        """
        Compare two PNG images with tolerance for OS-level rendering differences
        (font anti-aliasing, Poppler versions) while catching content regressions.

        Thresholds:
        - avg_diff < AVG_DIFF_THRESHOLD: General visual consistency (0-255 scale)
        - percent_changed < PERCENT_CHANGED_THRESHOLD: Localized content changes
        """
        # If they are byte-identical, they match perfectly
        if serialized_data == snapshot_data:
            return True

        if not serialized_data or not snapshot_data:
            return False

        try:
            actual = Image.open(io.BytesIO(serialized_data)).convert("RGB")
            expected = Image.open(io.BytesIO(snapshot_data)).convert("RGB")
        except Exception:
            return False

        if actual.size != expected.size:
            snapshot_logger.warning(
                f"Size mismatch: actual={actual.size}, expected={expected.size}"
            )
            return False

        # Calculate difference between images
        diff = ImageChops.difference(actual, expected)

        # Create a mask of pixels with significant differences (>100 on 0-255 scale)
        diff_gray = diff.convert("L")
        significant_diff_mask = diff_gray.point(lambda p: 1 if p > 100 else 0, mode="1")

        # Count significant pixels
        stat = ImageStat.Stat(significant_diff_mask)
        changed_pixels = stat.sum[0]
        total_pixels = actual.size[0] * actual.size[1]
        percent_changed = (changed_pixels / total_pixels) * 100

        # avg_diff for general visual consistency
        avg_stat = ImageStat.Stat(diff)
        avg_diff = sum(avg_stat.mean) / len(avg_stat.mean)

        matches = (
            avg_diff < self.AVG_DIFF_THRESHOLD
            and percent_changed < self.PERCENT_CHANGED_THRESHOLD
        )

        if not matches:
            snapshot_logger.info(
                f"Snapshot mismatch: avg_diff={avg_diff:.4f}, "
                f"changed_pixels={int(changed_pixels)} ({percent_changed:.4f}%), "
                f"actual_size={actual.size}, "
                f"threshold={self.PERCENT_CHANGED_THRESHOLD}%"
            )
        else:
            snapshot_logger.debug(
                f"Snapshot match: avg_diff={avg_diff:.4f}, "
                f"changed_pixels={int(changed_pixels)} ({percent_changed:.4f}%)"
            )

        return matches

    def serialize(self, data: Any, **_kwargs: Any) -> Any:
        if isinstance(data, str | Path):
            # It's a path to a PDF
            actual_png_path = Path(data).with_suffix(".png")
            if self.current_item:
                self.current_item.stash[actual_snapshot_path_key] = actual_png_path

            images = convert_from_path(
                data,
                dpi=150,  # low resolution to minimize file size
            )
            if not images:
                return super().serialize(b"")

            # Stitch images together vertically
            widths, heights = zip(*(i.size for i in images), strict=False)
            max_width = max(widths)
            total_height = sum(heights)

            combined = Image.new("RGB", (max_width, total_height))
            y_offset = 0
            for im in images:
                combined.paste(im, (0, y_offset))
                y_offset += im.size[1]

            img_byte_arr = io.BytesIO()
            combined.save(img_byte_arr, format="PNG")
            png_bytes = img_byte_arr.getvalue()

            # Save the PNG next to the PDF for easy comparison
            with contextlib.suppress(Exception):
                actual_png_path.write_bytes(png_bytes)

            return super().serialize(png_bytes)
        return super().serialize(data)
