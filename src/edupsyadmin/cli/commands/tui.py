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
"""
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
        "--school", nargs="*", type=str, default=None, help="filter by school name"
    )
    parser.add_argument("--columns", default=None, nargs="*", help="columns to show")


def execute(args: Namespace) -> None:
    """Entry point for the TUI."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    edupsyadmin_tui_cls = lazy_import("edupsyadmin.tui.edupsyadmintui").EdupsyadminTui

    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    app = edupsyadmin_tui_cls(
        manager=clients_manager,
        nta_nos=args.nta_nos,
        schools=args.school,
        columns=args.columns,
    )
    app.run()
