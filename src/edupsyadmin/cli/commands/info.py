import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Show app version and what paths the app uses"
COMMAND_HELP = "Get useful information for debugging"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      # Show app version, paths and other info
      edupsyadmin info
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the info command.

    :param parser: subcommand parser
    """
    parser.set_defaults(command=execute)


def execute(args: Namespace) -> None:
    """Execute the info command."""
    info_module = lazy_import("edupsyadmin.info")
    info_module.info(
        app_uid=args.app_uid,
        app_username=args.app_username,
        database_url=args.database_url,
        config_path=args.config_path,
        salt_path=args.salt_path,
    )
