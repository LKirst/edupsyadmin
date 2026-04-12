#!/usr/bin/env python
"""Flatten PDF forms to make form fields non-editable.

This module provides utilities to flatten PDF forms using either pdf2image
or fillpdf libraries, each with different trade-offs.
"""

import argparse
import sys
import warnings
from pathlib import Path

try:
    from pdf2image import convert_from_path

    INSTALLED_PDF2IMAGE = True
except ModuleNotFoundError:
    INSTALLED_PDF2IMAGE = False

try:
    from fillpdf import fillpdfs

    INSTALLED_FILLPDF = True
except ModuleNotFoundError:
    INSTALLED_FILLPDF = False

DEFAULT_LIBRARY = "pdf2image"
DEFAULT_PREFIX = "print_"
PDF_RESOLUTION = 100.0


class LibraryNotInstalledError(Exception):
    """Raised when the requested PDF library is not installed."""

    pass


class InvalidPDFError(Exception):
    """Raised when the input file is not a valid PDF."""

    pass


def flatten_pdf(
    fn_in: str | Path,
    library: str = DEFAULT_LIBRARY,
    output_prefix: str = DEFAULT_PREFIX,
) -> Path:
    """Flatten a PDF form, making form fields non-editable.

    This function takes an input PDF file with editable form fields and
    creates a "flattened" version where the fields are part of the content
    and can no longer be edited. This is useful for archiving or sharing
    completed forms.

    Two libraries can be used for this process:

    - 'pdf2image': Converts each page to an image and then combines them
      back into a PDF. This perfectly preserves the visual appearance but
      fails for tick-boxes and radio buttons. It also makes text unselectable.
      This library requires 'poppler' to be installed on the system.
    - 'fillpdf': Manipulates the PDF structure directly. It preserves
      selectable text but may fail for multiline text fields.

    A new file is created with the specified prefix (default: "print_").

    :param fn_in: Path to the input PDF file.
    :param library: The library to use for flattening ('pdf2image' or 'fillpdf').
                    Defaults to DEFAULT_LIBRARY.
    :param output_prefix: Prefix to add to the output filename.
    :return: Path to the flattened PDF file.
    :raises LibraryNotInstalledError: If the chosen library is not installed.
    :raises InvalidPDFError: If the input file doesn't exist or isn't a PDF.
    :raises FileNotFoundError: If the input file doesn't exist.
    """
    fn_in = Path(fn_in)

    # Validate input file
    if not fn_in.exists():
        raise FileNotFoundError(f"Input file not found: {fn_in}")

    if fn_in.suffix.lower() != ".pdf":
        raise InvalidPDFError(f"Input file is not a PDF: {fn_in}")

    fn_out = add_prefix(fn_in, prefix=output_prefix)

    if library == "pdf2image":
        if not INSTALLED_PDF2IMAGE:
            raise LibraryNotInstalledError(
                "pdf2image is not installed. Install it with: pip install pdf2image",
            )
        _flatten_with_pdf2image(fn_in, fn_out)

    elif library == "fillpdf":
        if not INSTALLED_FILLPDF:
            raise LibraryNotInstalledError(
                "fillpdf is not installed. Install it with: pip install fillpdf",
            )
        _flatten_with_fillpdf(fn_in, fn_out)

    else:
        raise ValueError(
            f"Unknown library: {library}. Choose 'pdf2image' or 'fillpdf'.",
        )

    print(f"Flattened {fn_in} to {fn_out}")
    return fn_out


def _flatten_with_pdf2image(fn_in: Path, fn_out: Path) -> None:
    """Flatten PDF using pdf2image library.

    :param fn_in: Input PDF path.
    :param fn_out: Output PDF path.
    """
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
    # TODO: find solution for tick-boxes and radio buttons (only an issue on Windows?)


def _flatten_with_fillpdf(fn_in: Path, fn_out: Path) -> None:
    """Flatten PDF using fillpdf library.

    :param fn_in: Input PDF path.
    :param fn_out: Output PDF path.
    """
    fillpdfs.flatten_pdf(str(fn_in), str(fn_out), as_images=False)

    warnings.warn(
        "fillpdf does not correctly render multiline text input fields.",
        UserWarning,
        stacklevel=3,
    )


def flatten_pdfs(
    form_paths: list[str | Path],
    library: str = DEFAULT_LIBRARY,
    output_prefix: str = DEFAULT_PREFIX,
) -> list[Path]:
    """Flatten multiple PDF forms.

    :param form_paths: List of paths to PDF files to flatten.
    :param library: The library to use for flattening.
    :param output_prefix: Prefix to add to output filenames.
    :return: List of paths to flattened PDF files.
    """
    output_paths = []
    for fn_in in form_paths:
        try:
            output_path = flatten_pdf(fn_in, library, output_prefix)
            output_paths.append(output_path)
        except (FileNotFoundError, InvalidPDFError, LibraryNotInstalledError) as e:
            print(f"Error processing {fn_in}: {e}", file=sys.stderr)
            continue

    return output_paths


def add_prefix(file_path: str | Path, prefix: str = DEFAULT_PREFIX) -> Path:
    """Add a prefix to a filename.

    :param file_path: Original file path.
    :param prefix: Prefix to add to the filename.
    :return: New path with prefixed filename.
    """
    file_path = Path(file_path)
    return file_path.parent / f"{prefix}{file_path.name}"


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Flatten PDF forms to make form fields non-editable.",
    )
    parser.add_argument(
        "inpaths",
        nargs="+",
        help="The paths of the PDFs which you want to flatten.",
    )
    parser.add_argument(
        "--library",
        default=DEFAULT_LIBRARY,
        choices=["fillpdf", "pdf2image"],
        help=f"Library to use for flattening (default: {DEFAULT_LIBRARY}).",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Prefix for output files (default: {DEFAULT_PREFIX}).",
    )

    args = parser.parse_args()

    # Check if at least one library is installed
    if not INSTALLED_PDF2IMAGE and not INSTALLED_FILLPDF:
        print(
            "Error: Neither pdf2image nor fillpdf is installed. "
            "Please install at least one library.",
            file=sys.stderr,
        )
        sys.exit(1)

    flatten_pdfs(args.inpaths, args.library, args.prefix)


if __name__ == "__main__":
    main()
