import argparse
import importlib
import importlib.resources
import os
import shutil
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from platformdirs import user_config_dir, user_data_path

from edupsyadmin.__version__ import __version__
from edupsyadmin.api.managers import ClientNotFoundError
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr, get_key_from_keyring
from edupsyadmin.core.logger import logger

__all__ = ("main",)

APP_UID = "liebermann-schulpsychologie.github.io"
USER_DATA_DIR = user_data_path(
    appname="edupsyadmin", version=__version__, ensure_exists=True
)
DEFAULT_DB_URL = "sqlite:///" + os.path.join(USER_DATA_DIR, "edupsyadmin.db")
DEFAULT_CONFIG_PATH = os.path.join(
    user_config_dir(appname="edupsyadmin", version=__version__, ensure_exists=True),
    "config.yml",
)
DEFAULT_SALT_PATH = os.path.join(
    user_config_dir(appname="edupsyadmin", version=__version__, ensure_exists=True),
    "salt.txt",
)


def _setup_encryption(app_uid: str, app_username: str) -> None:
    """Initialize the global encryption instance with a key from the keyring."""
    logger.debug(
        f"Loading encryption key for uid='{app_uid}', username='{app_username}'"
    )

    # Get key from keyring
    key = get_key_from_keyring(app_uid, app_username)

    if not key:
        raise RuntimeError(
            "No encryption key found in keyring for "
            f"uid='{app_uid}', username='{app_username}'. "
            "Please set a password in the configuration editor first "
            "(edupsyadmin edit_config)."
        )

    # Set the key on the global encryption instance
    encr.set_key(key)
    logger.debug("Encryption initialized successfully")


def _setup_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Dynamically discover and set up command subparsers."""
    commands_path = Path(__file__).parent / "commands"
    for file in sorted(commands_path.glob("*.py")):
        if file.name.startswith("_"):
            continue

        module_name = f"edupsyadmin.cli.commands.{file.stem}"
        command_module = importlib.import_module(module_name)

        if not hasattr(command_module, "add_arguments"):
            continue

        command_name = file.stem.replace("_", "-")

        parser_args = {
            "formatter_class": RawDescriptionHelpFormatter,
            "description": getattr(command_module, "COMMAND_DESCRIPTION", None),
            "help": getattr(command_module, "COMMAND_HELP", None),
            "epilog": getattr(command_module, "COMMAND_EPILOG", None),
        }
        # Filter out None values so we don't override argparse defaults
        parser_args = {k: v for k, v in parser_args.items() if v is not None}

        parser = subparsers.add_parser(command_name, **parser_args)
        command_module.add_arguments(parser)


def _args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command line arguments.

    :param argv: argument list to parse
    """
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--config_path", default=None, help=argparse.SUPPRESS)
    parser.add_argument(
        "--salt_path", default=DEFAULT_SALT_PATH, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"edupsyadmin {__version__}",
        help="print version and exit",
    )
    # default must be None, otherwise the value from the config for logging
    # level will be overwritten
    parser.add_argument(
        "-w", "--warn", default=None, help="logger warning level [WARN]"
    )

    # Global arguments
    parser.add_argument("--app_username", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--app_uid", default=APP_UID, help=argparse.SUPPRESS)
    parser.add_argument(
        "--database_url", default=DEFAULT_DB_URL, help=argparse.SUPPRESS
    )

    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(title="subcommands", dest="command_name")
    _setup_subparsers(subparsers)

    args = parser.parse_args(argv)

    if args.command is None:  # Correctly defaulted to None if no subcommand selected
        # No subcommand was specified, or a global flag like --help was used
        # without a subcommand.
        parser.print_help()
        raise SystemExit(1)

    if not args.config_path:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config_path = DEFAULT_CONFIG_PATH
    if not args.salt_path:
        args.salt_path = DEFAULT_SALT_PATH
    return args


def main(argv: list[str] | None = None) -> int:
    """Execute the application CLI.

    :param argv: argument list to parse (sys.argv by default)
    :return: exit status
    """
    args = _args(argv)

    # start logging
    logger.start(args.warn or "DEBUG")  # can't use default from config yet

    # config
    # if the config file doesn't exist, copy a sample config
    if not os.path.exists(args.config_path):
        template_path = str(
            importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
        )
        shutil.copy(template_path, args.config_path)
        logger.info(
            "Could not find the specified config file. "
            f"Created a sample config at {args.config_path}. "
            "Fill it with your values."
        )
    config.load(args.config_path)
    config.core.config = args.config_path
    if args.warn:
        config.core.logging = args.warn

    # restart logging based on config
    logger.stop()  # clear handlers to prevent duplicate records
    logger.start(config.core.logging)

    if not args.app_username:
        logger.debug("Trying to get app_username from config.")
        try:
            args.app_username = config.core.app_username
            logger.debug(f"Using app_username from config: '{args.app_username}'")
        except (KeyError, AttributeError):
            # For edit-config, username might not be set yet.
            if args.command_name == "edit-config":
                args.app_username = "default"
                logger.debug("Defaulting app_username to 'default' for edit-config.")
            else:
                logger.error(
                    "app_username not found. Either pass it via the command line "
                    "or set it in the config.yml (e.g., by running "
                    "'edupsyadmin edit-config')."
                )
                return 1
    else:
        logger.debug(f"Using username passed as cli argument: '{args.app_username}'")

    # These commands do not require encryption to be set up
    no_encryption_commands = ["info", "edit-config", "setup-demo", "migrate-encryption"]
    if args.command_name not in no_encryption_commands:
        _setup_encryption(args.app_uid, args.app_username)

    # handle commandline args
    command = args.command
    logger.debug(f"Executing command: {args.command_name}")
    logger.debug(f"Commandline arguments: {vars(args)}")

    try:
        command(args)
    except (RuntimeError, ClientNotFoundError, ValueError, KeyError) as err:
        logger.critical(err)
        return 1
    logger.debug("successful completion")
    return 0
