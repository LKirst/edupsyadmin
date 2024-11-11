"""Main application entry point.

python -m edupsy_admin  ...

"""

from .core import logger


def main():
    """Execute the application."""
    logger.debug("executing __main__.main()")
    logger.warning("I have not implememented __main__.main() yet!")


# Make the script executable.

if __name__ == "__main__":
    raise SystemExit(main())
