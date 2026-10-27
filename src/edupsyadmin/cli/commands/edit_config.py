import textwrap
from argparse import ArgumentParser, Namespace

lazy from edupsyadmin.tui.editconfig_app import ConfigEditorApp

COMMAND_DESCRIPTION = "Edit app configuration"
COMMAND_HELP = "Edit app configuration"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      # Open the configuration file in a TUI
      edupsyadmin edit-config
""",
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the editconfig command.

    :param parser: subcommand parser
    """
    parser.set_defaults(command=execute)


def execute(args: Namespace) -> None:
    """Execute the edit-config command."""
    ConfigEditorApp(
        args.config_path,
        args.app_uid,
        args.app_username,
        database_url=args.database_url,
    ).run()
