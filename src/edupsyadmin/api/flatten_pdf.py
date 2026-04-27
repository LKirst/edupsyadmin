#!/usr/bin/env python
"""Flatten PDF forms to make form fields non-editable.

This module provides utilities to flatten PDF forms using either pdf2image
or fillpdf libraries, each with different trade-offs.
"""

import argparse
import sys
from pathlib import Path

from edupsyadmin.api.flattening import (
    flatten_with_fillpdf,
    flatten_with_pdf2image,
    flatten_with_pypdf,
)

DEFAULT_LIBRARY = "pypdf"
DEFAULT_PREFIX = "print_"


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

    if library == "pypdf":
        flatten_with_pypdf(fn_in, fn_out)

    elif library == "pdf2image":
        flatten_with_pdf2image(fn_in, fn_out)

    elif library == "fillpdf":
        flatten_with_fillpdf(fn_in, fn_out)

    else:
        raise ValueError(
            f"Unknown library: {library}. Choose pdf2image, fillpdf or pypdf.",
        )

    print(f"Flattened {fn_in} to {fn_out}")
    return fn_out


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
        except (FileNotFoundError, InvalidPDFError) as e:
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
        choices=["fillpdf", "pdf2image", "pypdf"],
        help=f"Library to use for flattening (default: {DEFAULT_LIBRARY}).",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Prefix for output files (default: {DEFAULT_PREFIX}).",
    )

    args = parser.parse_args()

    flatten_pdfs(args.inpaths, args.library, args.prefix)


if __name__ == "__main__":
    main()
