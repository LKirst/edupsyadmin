import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Change values for one or more clients"
COMMAND_HELP = "Change values for one or more clients"
COMMAND_EPILOG = textwrap.dedent(
    """
    Examples:
      # Edit a client with ID 2 interactively in the TUI
      edupsyadmin set-client 2

      # Set 'nta_font' to '1' (true) and 'nta_zeitv_vieltext' to '20' for
      # clients with ID 1 and 2
      edupsyadmin set-client 1 2 --key_value_pairs "nta_font=1" \
        "nta_zeitv_vieltext=20"
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the set-client command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_id", type=int, nargs="+")
    parser.add_argument(
        "--key_value_pairs",
        type=str,
        nargs="*",
        default=[],
        help=(
            "key-value pairs in the format key=value; "
            "if no key-value pairs are passed, the TUI will be used to collect "
            "values."
        ),
    )


def execute(args: Namespace) -> None:
    """
    Set the value for a key given one or multiple client_ids
    """
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )

    if args.key_value_pairs:
        key_value_pairs_dict = dict(pair.split("=", 1) for pair in args.key_value_pairs)
        clients_manager.edit_client(
            client_ids=args.client_id, new_data=key_value_pairs_dict
        )
    else:
        edit_client_app_cls = lazy_import(
            "edupsyadmin.tui.edit_client_app"
        ).EditClientApp
        for cid in args.client_id:
            edit_client_app_cls(clients_manager=clients_manager, client_id=cid).run()
