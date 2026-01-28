"""Make the cli package executable."""

import sys

# The __init__.py file in this package is the main entry point.
from edupsyadmin.cli import main

if __name__ == "__main__":
    sys.exit(main())
