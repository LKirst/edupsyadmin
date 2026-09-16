import logging
import sys
import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Start the TUI"
COMMAND_HELP = "Start the TUI"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Example:
      # Start the TUI
      edupsyadmin tui

      # Filter by school name
      edupsyadmin --school MySchool

      # Show columns min_session and n_sessions
      edupsyadmin --columns min_sessions n_sessions
""",
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the tui command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--nta_nos",
        action="store_true",
        help="show only students with Nachteilsausgleich or Notenschutz",
    )
    parser.add_argument(
        "--school",
        nargs="*",
        type=str,
        default=None,
        help="filter by school name",
    )
    parser.add_argument("--columns", default=None, nargs="*", help="columns to show")
    parser.add_argument(
        "--academic_year",
        "--academic_years",
        "--academic-year",
        "--academic-years",
        dest="academic_years",
        nargs="*",
        type=str,
        default=None,
        help="filter by academic year(s) (default: current academic year)",
    )
    parser.add_argument(
        "--all_academic_years",
        "--all-academic-years",
        action="store_true",
        help="show entries from all academic years (overrides default filtering)",
    )


def _suppress_console_logging() -> None:
    """Remove all console handlers to prevent TUI flickering."""
    # Get all relevant loggers
    root_logger = logging.getLogger()
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")

    # Remove all console handlers (stdout/stderr)
    for logger_obj in (root_logger, sqlalchemy_logger):
        for handler in logger_obj.handlers.copy():
            if isinstance(handler, logging.StreamHandler) and (
                handler.stream in (sys.stdout, sys.stderr)
            ):
                logger_obj.removeHandler(handler)


def execute(args: Namespace) -> None:
    """Entry point for the TUI."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )
    logger = lazy_import("edupsyadmin.core.logger").logger
    total = clients_manager.get_total_count()
    logger.info(f"Database contains {total} entries.")

    # Suppress console logging BEFORE creating managers or starting TUI
    _suppress_console_logging()

    academic_years: list[str] | None
    if args.all_academic_years or (
        args.academic_years and "all" in args.academic_years
    ):
        academic_years = None
    elif args.academic_years is not None:
        academic_years = args.academic_years
    else:
        get_this_academic_year_string = lazy_import(
            "edupsyadmin.utils.academic_year",
        ).get_this_academic_year_string
        academic_years = [get_this_academic_year_string()]

    edupsyadmin_tui_cls = lazy_import("edupsyadmin.tui.edupsyadmintui").EdupsyadminTui

    app = edupsyadmin_tui_cls(
        manager=clients_manager,
        nta_nos=args.nta_nos,
        schools=args.school,
        columns=args.columns,
        academic_years=academic_years,
    )
    app.run()
