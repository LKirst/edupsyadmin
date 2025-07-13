"""Package for the edupsyadmin application."""

from . import api, core
from .__main__ import main
from .__version__ import __version__ as __version__  # public re-export

__all__ = ["__version__", "api", "core", "main"]
