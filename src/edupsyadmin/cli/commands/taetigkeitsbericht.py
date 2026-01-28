import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Create a PDF output for the Taetigkeitsbericht (experimental)"
COMMAND_HELP = "Create a PDF output for the Taetigkeitsbericht (experimental)"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Example:
      # Generate a Taetigkeitsbericht PDF with 3 Anrechnugnsstunden
      edupsyadmin taetigkeitsbericht 3

      # Generate a report with custom output name and total hours
      edupsyadmin taetigkeitsbericht 10 --out_basename "MyReport" --wstd_total 28
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the api.taetigkeitsbericht_from_db.taetigkeitsbericht command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "wstd_psy", type=int, help="Anrechnungsstunden in Wochenstunden"
    )
    parser.add_argument(
        "--out_basename",
        type=str,
        default="Taetigkeitsbericht_Out",
        help="base name for the output files; default is 'Taetigkeitsbericht_Out'",
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


def execute(args: Namespace) -> None:
    """Execute the taetigkeitsbericht command."""
    taetigkeitsbericht = lazy_import(
        "edupsyadmin.api.taetigkeitsbericht_from_db"
    ).taetigkeitsbericht
    taetigkeitsbericht(
        app_username=args.app_username,
        app_uid=args.app_uid,
        database_url=args.database_url,
        salt_path=args.salt_path,
        wstd_psy=args.wstd_psy,
        out_basename=args.out_basename,
        wstd_total=args.wstd_total,
        name=args.name,
    )
