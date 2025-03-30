"""Implementation of the command line interface."""

import importlib
import importlib.resources
import os
import shutil
import sys
from argparse import ArgumentParser
from inspect import getfullargspec

from platformdirs import user_config_dir, user_data_path

from edupsyadmin import __version__
from edupsyadmin.core.config import config
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


# Lazy import utility function
def lazy_import(name):
    """
    Lazy import utility function. This function is from the Python
    documentation
    (https://docs.python.org/3/library/importlib.html#implementing-lazy-imports).
    """
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


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
    # if the (first) config file doesn't exist, copy a sample config
    if not os.path.exists(args.config_path[0]):
        template_path = str(
            importlib.resources.files("edupsyadmin.data") / "sampleconfig.yml"
        )
        shutil.copy(template_path, args.config_path[0])
        logger.info(
            (
                "Could not find the specified config file. "
                f"Created a sample config at {args.config_path[0]}. "
                "Fill it with your values."
            )
        )
    config.load(args.config_path)
    config.core.config = args.config_path
    if args.warn:
        config.core.logging = args.warn

    # restart logging based on config
    logger.stop()  # clear handlers to prevent duplicate records
    logger.start(config.core.logging)

    if not args.app_username:
        logger.debug(f"using config.core.app_username: '{config.core.app_username}'")
        try:
            args.app_username = config.core.app_username
        except KeyError as exc:
            logger.error(
                (
                    "Either pass app_username from the "
                    "commandline or set app_username in the config.yml"
                )
            )
            raise exc
    else:
        logger.debug(f"using username passed as cli argument: '{args.app_username}'")

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
    # append allows multiple instances of the same object
    # args.config_path will therefore be a list!
    parser.add_argument("-c", "--config_path", action="append", help="config file path")
    parser.add_argument("-s", "--salt_path", help="salt file path")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"edupsyadmin {__version__}",
        help="print version and exit",
    )
    parser.add_argument(
        "-w", "--warn", default="WARN", help="logger warning level [WARN]"
    )
    parser.set_defaults(command=None)
    subparsers = parser.add_subparsers(title="subcommands")

    common = ArgumentParser(add_help=False)  # common subcommand arguments
    common.add_argument(
        "--app_username",
        help=(
            "username for encryption; if it is not set here, the app will "
            "try to read it from the config file"
        ),
    )
    common.add_argument("--app_uid", default=APP_UID)
    common.add_argument("--database_url", default=DEFAULT_DB_URL)
    _info(subparsers, common)
    _new_client(subparsers, common)
    _set_client(subparsers, common)
    _create_documentation(subparsers, common)
    _get_clients(subparsers, common)
    _flatten_pdfs(subparsers, common)
    _mk_report(subparsers, common)
    _taetigkeitsbericht(subparsers, common)
    _delete_client(subparsers, common)

    args = parser.parse_args(argv)
    if not args.command:
        # No sucommand was specified.
        parser.print_help()
        raise SystemExit(1)
    if not args.config_path:
        # Don't specify this as an argument default or else it will always be
        # included in the list.
        args.config_path = [DEFAULT_CONFIG_PATH]
    if not args.salt_path:
        args.salt_path = DEFAULT_SALT_PATH
    return args


def _info(subparsers, common):
    """CLI adaptor for the info command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    info = lazy_import("edupsyadmin.info").info
    parser = subparsers.add_parser(
        "info",
        parents=[common],
        description="Show app version and what paths the app uses",
        help="Get useful information for debugging",
    )
    parser.set_defaults(command=info)


def _new_client(subparsers, common):
    """CLI adaptor for the api.clients.new_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    new_client = lazy_import("edupsyadmin.api.managers").new_client
    parser = subparsers.add_parser(
        "new_client",
        parents=[common],
        help="Add a new client",
        description="Add a new client",
    )
    parser.set_defaults(
        command=new_client,
    )
    parser.add_argument(
        "--csv",
        help=(
            "An untis tab separated values file. If you pass no csv path, you can "
            "interactively enter the data."
        ),
    )
    parser.add_argument(
        "--name",
        help=(
            "Only relevant if --csv is set."
            "Name of the client from the name column of the csv."
        ),
    )
    parser.add_argument(
        "--school",
        help=(
            "Only relevant if --csv is set. The label of the school as you "
            "use it in the config file. If no label is passed, the first "
            "school from the config will be used."
        ),
    )
    parser.add_argument(
        "--keepfile",
        action="store_true",
        help=(
            "Only relevant if --csv is set."
            "Don't delete the csv after adding it to the db."
        ),
    )


def _set_client(subparsers, common):
    """CLI adaptor for the api.clients.set_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    set_client = lazy_import("edupsyadmin.api.managers").set_client
    parser = subparsers.add_parser(
        "set_client",
        parents=[common],
        help="Change values for a client",
        description="Change values for a client",
    )
    parser.set_defaults(
        command=set_client,
    )
    parser.add_argument("client_id", type=int)
    parser.add_argument(
        "key_value_pairs",
        type=str,
        nargs="+",
        help="key-value pairs in the format key=value",
    )


def _delete_client(subparsers, common):
    """CLI adaptor for the api.managers.delete_client command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    delete_client = lazy_import("edupsyadmin.api.managers").delete_client
    # TODO: Write test
    parser = subparsers.add_parser(
        "delete_client", parents=[common], help="Delete a client in the database"
    )
    parser.set_defaults(
        command=delete_client,
    )
    parser.add_argument("client_id", type=int, help="id of the client to delete")


def _get_clients(subparsers, common):
    """CLI adaptor for the api.clients.get_na_ns command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    get_clients = lazy_import("edupsyadmin.api.managers").get_clients
    parser = subparsers.add_parser(
        "get_clients",
        parents=[common],
        help="Show clients overview or single client",
        description="Show clients overview or single client",
    )
    parser.set_defaults(
        command=get_clients,
    )
    parser.add_argument(
        "--nta_nos",
        action="store_true",
        help="show only students with Nachteilsausgleich or Notenschutz",
    )
    parser.add_argument("--out", help="path for an output file")
    parser.add_argument(
        "--client_id", type=int, help="id for a single client to display"
    )


def _create_documentation(subparsers, common):
    """CLI adaptor for the api.clients.create_documentation command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    create_documentation = lazy_import("edupsyadmin.api.managers").create_documentation
    parser = subparsers.add_parser(
        "create_documentation",
        parents=[common],
        help="Fill a pdf form or a text file with a liquid template",
        description="Fill a pdf form or a text file with a liquid template",
    )
    parser.set_defaults(
        command=create_documentation,
    )
    parser.add_argument("client_id", type=int)
    parser.add_argument(
        "--form_set",
        type=str,
        default=None,
        help="name of a set of file paths defined in the config file",
    )
    parser.add_argument("form_paths", nargs="*", help="form file paths")


def _mk_report(subparsers, common):
    """CLI adaptor for the api.lgvt.mk_report command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    mk_report = lazy_import("edupsyadmin.api.lgvt").mk_report
    parser = subparsers.add_parser("mk_report", parents=[common])
    parser.set_defaults(
        command=mk_report,
    )
    parser.add_argument("client_id", type=int)
    parser.add_argument("test_date", type=str, help="Testdatum (YYYY-mm-dd)")
    parser.add_argument("test_type", type=str, choices=["LGVT", "CFT", "RSTARR"])
    parser.add_argument(
        "--version", type=str, choices=["Rosenkohl", "Toechter", "Laufbursche"]
    )


def _flatten_pdfs(subparsers, common):
    # Lazy import within the function
    flatten_pdfs = lazy_import("edupsyadmin.api.flatten_pdf").flatten_pdfs
    DEFAULT_LIBRARY = lazy_import("edupsyadmin.api.flatten_pdf").DEFAULT_LIBRARY
    parser = subparsers.add_parser(
        "flatten_pdfs",
        parents=[common],
        help="Flatten pdf forms (experimental)",
        description="Flatten pdf forms (experimental)",
    )
    parser.set_defaults(
        command=flatten_pdfs,
    )
    parser.add_argument(
        "--library", type=str, default=DEFAULT_LIBRARY, choices=["pdf2image", "fillpdf"]
    )
    parser.add_argument("form_paths", nargs="+")


def _taetigkeitsbericht(subparsers, common):
    """CLI adaptor for the api.taetigkeitsbericht_from_db.taetigkeitsbericht command.

    :param subparsers: subcommand parsers
    :param common: parser for common subcommand arguments
    """
    # Lazy import within the function
    taetigkeitsbericht = lazy_import(
        "edupsyadmin.api.taetigkeitsbericht_from_db"
    ).taetigkeitsbericht
    parser = subparsers.add_parser(
        "taetigkeitsbericht",
        parents=[common],
        help="Create a PDF output for the Taetigkeitsbericht (experimental)",
    )
    parser.set_defaults(
        command=taetigkeitsbericht,
    )
    parser.add_argument(
        "wstd_psy", type=int, help="Anrechnungsstunden in Wochenstunden"
    )
    parser.add_argument(
        "nstudents",
        nargs="+",
        help=(
            "list of strings with item containing the name of the school "
            "and the number of students at that school, e.g. Schulname625"
        ),
    )
    parser.add_argument(
        "--out_basename",
        type=str,
        default="Taetigkeitsbericht_Out",
        help="base name for the output files; default is 'Taetigkeitsbericht_Out'",
    )
    parser.add_argument(
        "--min_per_ses",
        type=int,
        default=45,
        help="duration of one session in minutes; default is 45",
    )
    parser.add_argument(
        "--wstd_total",
        type=int,
        default=23,
        help="total Wochstunden (depends on your school); default is 23",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Schulpsychologie",
        help="name for the header of the pdf report",
    )


# Make the module executable.
if __name__ == "__main__":
    try:
        STATUS = main()
    except:
        logger.critical("shutting down due to fatal error")
        raise  # print stack trace
    raise SystemExit(STATUS)
