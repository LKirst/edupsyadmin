import textwrap
from argparse import ArgumentParser

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = (
    "Create a sandboxed demo environment (demo-config.yml, demo-salt.txt, demo.db)."
)
COMMAND_HELP = "Create a sandboxed demo environment."
COMMAND_EPILOG = textwrap.dedent(
    """\
    Example:
      # Create a sandboxed demo environment
      edupsyadmin setup_demo
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the setup_demo command."""
    parser.set_defaults(command=execute)


def execute() -> None:
    """Create a sandboxed demo environment."""
    setup_demo = lazy_import("edupsyadmin.api.setup_demo").setup_demo
    setup_demo()
