import csv
import textwrap
from argparse import ArgumentParser, Namespace
from pathlib import Path

from rich.console import Console
from rich.table import Table

from edupsyadmin.cli.utils import lazy_import
from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = "Show clients overview or single client"
COMMAND_HELP = "Show clients overview or single client"
COMMAND_EPILOG = textwrap.dedent(
    r"""        Examples:
          # Show an overview of all clients
          edupsyadmin get-clients

          # Show an overview in an interactive TUI
          edupsyadmin get-clients --tui

          # Show clients from 'TutorialSchule' who have 'NTA' or 'NOS'
          edupsyadmin get-clients --nta_nos --school TutorialSchule

          # Show all details for client with ID 2
          edupsyadmin get-clients --client_id 2

          # Show all clients, and display the columns keyword_taet_encr and notes_encr
          edupsyadmin get-clients --tui --columns keyword_taet_encr notes_encr
          """,
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the get-clients command."""
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
        default=[],
        help="filter by school name",
    )
    parser.add_argument("--out", help="path for an output file", type=Path)
    parser.add_argument(
        "--client_id",
        type=int,
        help="id for a single client to display",
    )
    parser.add_argument("--columns", default=[], nargs="*", help="columns to show")
    parser.add_argument(
        "--tui",
        action="store_true",
        help="show the results in a tui instead of plain text",
    )


def execute(args: Namespace) -> None:
    """Execute the get-clients command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    total = clients_manager.get_total_count()
    logger.info(f"Database contains {total} entries.")

    if args.tui:
        clients_overview_app_cls = lazy_import(
            "edupsyadmin.tui.clients_overview_app",
        ).ClientsOverviewApp
        clients_overview_app_cls(
            clients_manager=clients_manager,
            nta_nos=args.nta_nos,
            schools=args.school,
            columns=args.columns,
        ).run()
    else:
        display_client_details = lazy_import(
            "edupsyadmin.api.display_client_details",
        ).display_client_details

        if args.client_id:
            client_data = clients_manager.get_decrypted_client(args.client_id)
            display_client_details(client_data)
            data_to_export = [client_data.model_dump()]
        else:
            data = clients_manager.get_clients_overview(
                nta_nos=args.nta_nos,
                schools=args.school,
                columns=args.columns,
            )
            # Sort manually
            data.sort(key=lambda x: (x.get("school", ""), x.get("last_name_encr", "")))
            data_to_export = data

            if data:
                table = Table(title="Clients Overview")
                # Use keys from first dict as columns
                cols = [c for c in data[0] if c != "case_active"]
                for col in cols:
                    table.add_column(col, no_wrap=True)

                for row in data:
                    table.add_row(*(str(row.get(c, "")) for c in cols))

                Console().print(table)
            else:
                print("No clients found.")

        if args.out and data_to_export:
            with args.out.open(mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data_to_export[0].keys())
                writer.writeheader()
                writer.writerows(data_to_export)
