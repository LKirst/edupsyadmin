import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Show clients overview or single client"
COMMAND_HELP = "Show clients overview or single client"
COMMAND_EPILOG = textwrap.dedent(
    r"""        Examples:
          # Show an overview of all clients
          edupsyadmin get_clients

          # Show an overview in an interactive TUI
          edupsyadmin get_clients --tui

          # Show clients from 'TutorialSchule' who have 'NTA' or 'NOS'
          edupsyadmin get_clients --nta_nos --school TutorialSchule

          # Show all details for client with ID 2
          edupsyadmin get_clients --client_id 2

          # Show all clients, and display the columns keyword_taet_encr and notes_encr
          edupsyadmin get_clients --tui --columns keyword_taet_encr notes_encr
          """
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the get_clients command."""
    parser.set_defaults(command=execute)
    parser.add_argument(
        "--nta_nos",
        action="store_true",
        help="show only students with Nachteilsausgleich or Notenschutz",
    )
    parser.add_argument(
        "--school", nargs="*", type=str, default=[], help="filter by school name"
    )
    parser.add_argument("--out", help="path for an output file")
    parser.add_argument(
        "--client_id", type=int, help="id for a single client to display"
    )
    parser.add_argument("--columns", default=[], nargs="*", help="columns to show")
    parser.add_argument(
        "--tui",
        action="store_true",
        help="show the results in a tui instead of plain text",
    )


def execute(args: Namespace) -> None:
    """Execute the get_clients command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    if args.tui:
        clients_overview_app_cls = lazy_import(
            "edupsyadmin.tui.clients_overview_app"
        ).ClientsOverviewApp
        clients_overview_app_cls(
            clients_manager=clients_manager,
            nta_nos=args.nta_nos,
            schools=args.school,
            columns=args.columns,
        ).run()
    else:
        display_client_details = lazy_import(
            "edupsyadmin.api.display_client_details"
        ).display_client_details
        pd = lazy_import("pandas")

        if args.client_id:
            client_data = clients_manager.get_decrypted_client(args.client_id)
            display_client_details(client_data)
            df = pd.DataFrame([client_data]).T
        else:
            df = clients_manager.get_clients_overview(
                nta_nos=args.nta_nos,
                schools=args.school,
                columns=args.columns,
            )

            original_df = df.sort_values(["school", "last_name_encr"])
            df = original_df.set_index("client_id")

            with pd.option_context(
                "display.max_columns",
                None,
                "display.width",
                None,
                "display.max_colwidth",
                None,
                "display.expand_frame_repr",
                False,
            ):
                print(df)

        if args.out:
            df.to_csv(args.out)
