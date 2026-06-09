#!/usr/bin/env python
"""CLI tool for flattening PDF forms."""

import argparse
from pathlib import Path

from edupsyadmin.api.flattening import (
    DEFAULT_PREFIX,
    InvalidPDFError,
    flatten_pdf,
    flatten_pdfs,
)

__all__ = [
    "DEFAULT_PREFIX",
    "InvalidPDFError",
    "flatten_pdf",
    "flatten_pdfs",
]


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
        "--prefix",
        default=DEFAULT_PREFIX,
        help=f"Prefix for output files (default: {DEFAULT_PREFIX}).",
    )
    parser.add_argument(
        "--password",
        "-p",
        help="password to decrypt input PDF(s) and encrypt output PDF(s)",
    )

    args = parser.parse_args()

    password = args.password
    if not password:
        from pypdf import PdfReader

        for p in args.inpaths:
            p_path = Path(p)
            if p_path.exists() and p_path.suffix.lower() == ".pdf":
                try:
                    reader = PdfReader(str(p_path))
                    if reader.is_encrypted:
                        import getpass

                        password = getpass.getpass(
                            f"Passwort für verschlüsselte PDF '{p_path.name}': ",
                        )
                        break
                except Exception:
                    continue

    try:
        paths = flatten_pdfs(args.inpaths, args.prefix, password=password)
        for p in paths:
            print(f"Flattened to {p}")
    except (FileNotFoundError, InvalidPDFError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
