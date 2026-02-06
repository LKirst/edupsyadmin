import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Edit app configuration"
COMMAND_HELP = "Edit app configuration"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      # Open the configuration file in a TUI
      edupsyadmin edit-config
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the editconfig command.

    :param parser: subcommand parser
    """
    parser.set_defaults(command=execute)


def execute(args: Namespace) -> None:
    """Execute the edit-config command."""
    config_editor_app_cls = lazy_import("edupsyadmin.tui.editconfig").ConfigEditorApp
    config_editor_app_cls(args.config_path, args.app_uid, args.app_username).run()
