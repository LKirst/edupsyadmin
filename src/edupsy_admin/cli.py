""" Implementation of the command line interface.

"""
import os
from argparse import ArgumentParser
from inspect import getfullargspec

from platformdirs import user_data_path

from . import __version__
from .api.clients import new_client, create_documentation
from .core.config import config
from .core.logger import logger


__all__ = ("main",)

APP_UID = "liebermann-schulpsychologie.github.io"
USER_DATA_DIR = user_data_path(
        appname = "edupsy_admin",
        version = __version__,
        ensure_exists = True
        )
DATABASE_URL = "sqlite:///" +  os.path.join(USER_DATA_DIR, "edupsy_admin.db")


def main(argv=None) -> int:
    """Execute the application CLI.

    :param argv: argument list to parse (sys.argv by default)
    :return: exit status
    """
    args = _args(argv)

    # start logging
    logger.start(args.warn or "DEBUG")  # can't use default from config yet
    logger.debug("starting execution")

    # config
    config.load(args.config_path)
    config.core.config = args.config_path
    if args.warn:
        config.core.logging = args.warn

    # restart logging based on config
    logger.stop()  # clear handlers to prevent duplicate records
    logger.start(config.core.logging)

    # handle commandline args
    command = args.command
    logger.debug(f"commandline arguments: {vars(args)}")
    args = vars(args)
    spec = getfullargspec(command)
    if not spec.varkw:
        # No kwargs, remove unexpected arguments.
        args = {key: args[key] for key in args if key in spec.args}
    try:
        command(**args)
    except RuntimeError as err:
        logger.critical(err)
        return 1
    logger.debug("successful completion")
    return 0


def _args(argv):
    """Parse command line arguments.

    :param argv: argument list to parse
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config_path", action="append", help="config file [etc/config.yml]"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"edupsy_admin {__version__}",
        help="print version and exit",
    )
    parser.add_argument(
        "-w", "--warn", default="WARN", help="logger warning level [WARN]"
    )
    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(title="subcommands")

    common = ArgumentParser(add_help=False)  # common subcommand arguments
    common.add_argument("app_username", help="username for encryption")
    common.add_argument("--app_uid", default=APP_UID)
    common.add_argument("--database_url", default=DATABASE_URL)
    _new_client(subparsers, common)
    _create_documentation(subparsers, common)

    args = parser.parse_args(argv)
    if not args.command:
        # No sucommand was specified.
        parser.print_help()
        raise SystemExit(1)
    if not args.config_path:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config_path = "etc/config.yml"
    return args


def _new_client(subparsers, common):
    """CLI adaptor for the api.clients.new_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    parser = subparsers.add_parser("new_client", parents=[common])
    parser.set_defaults(
        command=new_client,
        help="Add a new client",
    )
    parser.add_argument("--csv", help=(
        "An untis csv with one row. If you pass no csv path, you can "
        "interactively enter the data"
        ))
    parser.add_argument(
            "--keepfile", action="store_true",
            help="Don't delete the csv after adding it to the db.")
    return


def _create_documentation(subparsers, common):
    """CLI adaptor for the api.clients.create_documentation command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    parser = subparsers.add_parser("create_documentation", parents=[common])
    parser.set_defaults(
        command=create_documentation,
        help="Fill a pdf form",
    )
    parser.add_argument("client_id", type=int)
    parser.add_argument("form_paths", nargs='+')
    return


# Make the module executable.
if __name__ == "__main__":
    try:
        status = main()
    except:
        logger.critical("shutting down due to fatal error")
        raise  # print stack trace
    else:
        raise SystemExit(status)
