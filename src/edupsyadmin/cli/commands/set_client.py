import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import, parse_key_value_pairs

COMMAND_DESCRIPTION = "Change values for one or more clients"
COMMAND_HELP = "Change values for one or more clients"
COMMAND_EPILOG = textwrap.dedent(
    """
    Examples:
      # Edit a client with ID 2 interactively in the TUI
      edupsyadmin set-client 2

      # Set 'nta_font' to '1' (true) and 'nta_zeitv_vieltext' to '20' for
      # clients with ID 1 and 2
      edupsyadmin set-client 1 2 --key-value-pairs "nta_font=1" \
        "nta_zeitv_vieltext=20"
""",
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the set-client command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_ids", type=int, nargs="+")
    parser.add_argument(
        "--key-value-pairs",
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
        key_value_pairs_dict = parse_key_value_pairs(
            args.key_value_pairs,
            option_name="--key-value-pairs",
        )
        clients_manager.edit_client(
            client_ids=args.client_ids,
            new_data=key_value_pairs_dict,
        )
    else:
        edit_client_app_cls = lazy_import(
            "edupsyadmin.tui.edit_client_app",
        ).EditClientApp
        for cid in args.client_ids:
            edit_client_app_cls(clients_manager=clients_manager, client_id=cid).run()
