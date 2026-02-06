import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import
from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = "Create a report for a given test type. (experimental)"
COMMAND_HELP = "Create a report for a given test type. (experimental)"
COMMAND_EPILOG = textwrap.dedent("""\
    Example:
      # Create a CFT report for client with ID 1
      edupsyadmin mk-report 1 2023-10-26 CFT
      """)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the api.lgvt.mk_report command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_id", type=int)
    parser.add_argument("test_date", type=str, help="Testdatum (YYYY-mm-dd)")
    parser.add_argument("test_type", type=str, choices=["LGVT", "CFT", "RSTARR"])
    parser.add_argument(
        "--version",
        type=str,
        choices=["Rosenkohl", "Toechter", "Laufbursche"],
        default=None,
    )


def execute(args: Namespace) -> None:
    """Execute the mk-report command."""
    logger.debug(f"args.test_type: {args.test_type}")
    if args.test_type == "LGVT":
        mk_report = lazy_import("edupsyadmin.api.lgvt").mk_report
        mk_report(
            args.database_url,
            args.client_id,
            args.test_date,
            version=args.version,
        )
    elif args.test_type == "CFT":
        create_report = lazy_import("edupsyadmin.api.cft_report").create_report
        create_report(
            args.database_url,
            args.client_id,
            args.test_date,
        )
    else:
        logger.warning("Testauswertung bisher nur für CFT und LGVT implementiert")
