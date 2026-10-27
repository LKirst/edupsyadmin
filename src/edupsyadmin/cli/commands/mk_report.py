import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.core.config import config
from edupsyadmin.core.logger import logger
from edupsyadmin.utils.path_utils import normalize_path
lazy from edupsyadmin.api.cft_report import create_report
lazy from edupsyadmin.api.lgvt import mk_report

COMMAND_DESCRIPTION = "Create a report for a given test type."
COMMAND_HELP = "Create a report for a given test type."
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
    parser.add_argument(
        "--out-dir",
        type=normalize_path,
        default=None,
        help=(
            "output directory for generated report "
            "(overrides the default from the config file)"
        ),
    )


def execute(args: Namespace) -> None:
    """Execute the mk-report command."""
    logger.debug(f"args.test_type: {args.test_type}")
    out_dir = args.out_dir or config.core.output_directory
    if args.test_type == "LGVT":
        mk_report(
            args.database_url,
            args.client_id,
            args.test_date,
            version=args.version,
            directory=out_dir,
        )
    elif args.test_type == "CFT":
        create_report(
            args.database_url,
            args.client_id,
            args.test_date,
            directory=out_dir,
        )
    else:
        logger.warning("Testauswertung bisher nur für CFT und LGVT implementiert")
