"""PDF flattening.

This package provides utilities to flatten PDF forms, making form fields
non-editable by merging their appearance streams into the page content.
"""

from edupsyadmin.api.flattening.api import flatten_pdf, flatten_pdfs
from edupsyadmin.api.flattening.base import DEFAULT_PREFIX, InvalidPDFError
from edupsyadmin.api.flattening.pypdf_backend import flatten_with_pypdf

__all__ = [
    "DEFAULT_PREFIX",
    "InvalidPDFError",
    "flatten_pdf",
    "flatten_pdfs",
    "flatten_with_pypdf",
]
