#!/usr/bin/env python
"""CLI tool for flattening PDF forms."""

import argparse

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

    args = parser.parse_args()

    try:
        paths = flatten_pdfs(args.inpaths, args.prefix)
        for p in paths:
            print(f"Flattened to {p}")
    except (FileNotFoundError, InvalidPDFError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
