"""PDF flattening implementations.

This subpackage provides different strategies for flattening PDF forms.
"""

from edupsyadmin.api.flattening.flatten_fillpdf import flatten_with_fillpdf
from edupsyadmin.api.flattening.flatten_pdf2image import flatten_with_pdf2image
from edupsyadmin.api.flattening.flatten_pypdf import flatten_with_pypdf

__all__ = [
    "flatten_with_fillpdf",
    "flatten_with_pdf2image",
    "flatten_with_pypdf",
]
