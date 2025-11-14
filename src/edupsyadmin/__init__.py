"""Package for the edupsyadmin application."""

from edupsyadmin import api, core
from edupsyadmin.__main__ import main
from edupsyadmin.__version__ import __version__ as __version__  # public re-export

__all__ = ["__version__", "api", "core", "main"]
