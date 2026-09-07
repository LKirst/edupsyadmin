"""Shared types and exceptions for PDF flattening."""


class InvalidPDFError(Exception):
    """Raised when the input file is not a valid PDF."""


DEFAULT_PREFIX = "print_"

__all__ = ["DEFAULT_PREFIX", "InvalidPDFError"]
