"""High-level API for PDF flattening."""

import sys
from collections.abc import Sequence
from pathlib import Path

from edupsyadmin.api.flattening.base import DEFAULT_PREFIX, InvalidPDFError
from edupsyadmin.api.flattening.pypdf_backend import flatten_with_pypdf


def flatten_pdf(
    fn_in: str | Path,
    output_prefix: str = DEFAULT_PREFIX,
    password: str | None = None,
) -> Path:
    """Flatten a PDF form, making form fields non-editable.

    :param fn_in: Path to the input PDF file.
    :param output_prefix: Prefix to add to the output filename.
    :param password: Password to decrypt the input PDF and encrypt the output.
    :return: Path to the flattened PDF file.
    :raises InvalidPDFError: If the input file is not a PDF.
    :raises FileNotFoundError: If the input file doesn't exist.
    """
    fn_in = Path(fn_in)
    if not fn_in.exists():
        raise FileNotFoundError(f"Input file not found: {fn_in}")
    if fn_in.suffix.lower() != ".pdf":
        raise InvalidPDFError(f"Input file is not a PDF: {fn_in}")

    fn_out = add_prefix(fn_in, prefix=output_prefix)
    flatten_with_pypdf(fn_in, fn_out, password=password)
    return fn_out


def flatten_pdfs(
    form_paths: Sequence[str | Path],
    output_prefix: str = DEFAULT_PREFIX,
    password: str | None = None,
) -> list[Path]:
    """Flatten multiple PDF forms.

    :param form_paths: List of paths to the input PDF files.
    :param output_prefix: Prefix to add to the output filenames.
    :param password: Password to decrypt the input PDFs and encrypt the outputs.
    :return: List of paths to the flattened PDF files.
    """
    output_paths = []
    for fn_in in form_paths:
        try:
            output_paths.append(flatten_pdf(fn_in, output_prefix, password=password))
        except (FileNotFoundError, InvalidPDFError) as e:
            print(f"Error processing {fn_in}: {e}", file=sys.stderr)
            continue
    return output_paths


def add_prefix(file_path: str | Path, prefix: str = DEFAULT_PREFIX) -> Path:
    """Add a prefix to a filename."""
    file_path = Path(file_path)
    return file_path.parent / f"{prefix}{file_path.name}"
