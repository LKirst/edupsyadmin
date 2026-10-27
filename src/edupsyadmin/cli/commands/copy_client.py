import textwrap
from argparse import ArgumentParser, Namespace

from rich.console import Console

from edupsyadmin.core.logger import logger
lazy from edupsyadmin.api.managers import ClientsManager
lazy from edupsyadmin.utils.academic_year import get_this_academic_year_string

COMMAND_DESCRIPTION = "Copy a client to an academic year"
COMMAND_HELP = "Copy a client to an academic year"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Examples:
      # Copy client with ID 1 to academic year 2026/27
      edupsyadmin copy-client 1 --to-academic-year 2026/27

      # Copy client with ID 1 to the current academic year, keeping sessions
      edupsyadmin copy-client 1 --keep-sessions
""",
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the copy-client command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_id", type=int, help="id of the client to copy")
    parser.add_argument(
        "--to-academic-year",
        type=str,
        default=None,
        help="target academic year (default: current academic year)",
    )
    parser.add_argument(
        "--keep-sessions",
        action="store_true",
        help="keep session counts instead of resetting them to 0",
    )


def execute(args: Namespace) -> None:
    """Execute the copy-client command."""
    clients_manager = ClientsManager(
        database_url=args.database_url,
    )

    to_academic_year = args.to_academic_year
    if to_academic_year is None:
        to_academic_year = get_this_academic_year_string()

    new_id = clients_manager.copy_client(
        client_id=args.client_id,
        target_academic_year=to_academic_year,
        reset_sessions=not args.keep_sessions,
    )
    msg = (
        f"Client {args.client_id} successfully copied to client "
        f"{new_id} for academic year {to_academic_year}."
    )
    logger.info(msg)
    Console().print(f"[bold green]{msg}[/bold green]")
