import warnings
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import

PDF_RESOLUTION = 95.0


class InvalidPDFError(Exception):
    """Raised when the input file is not a valid PDF."""

    pass


def flatten_with_pdf2image(fn_in: Path, fn_out: Path) -> None:
    """Flatten PDF using pdf2image library.

    :param fn_in: Input PDF path.
    :param fn_out: Output PDF path.
    """
    convert_from_path = lazy_import("pdf2image").convert_from_path
    images = convert_from_path(fn_in)
    if not images:
        raise InvalidPDFError(f"Could not convert PDF to images: {fn_in}")

    first_image = images[0]
    remaining_images = images[1:]

    first_image.save(
        fn_out,
        "PDF",
        resolution=PDF_RESOLUTION,
        save_all=True,
        append_images=remaining_images,
    )

    warnings.warn(
        "pdf2image may fail for tick-boxes and radio buttons.",
        UserWarning,
        stacklevel=3,
    )
