import warnings
from pathlib import Path

from edupsyadmin.cli.utils import lazy_import


def flatten_with_fillpdf(fn_in: Path, fn_out: Path) -> None:
    """Flatten PDF using fillpdf library.

    :param fn_in: Input PDF path.
    :param fn_out: Output PDF path.
    """
    fillpdfs = lazy_import("fillpdf.fillpdfs")
    fillpdfs.flatten_pdf(str(fn_in), str(fn_out), as_images=False)

    warnings.warn(
        "fillpdf does not correctly render multiline text input fields.",
        UserWarning,
        stacklevel=3,
    )
