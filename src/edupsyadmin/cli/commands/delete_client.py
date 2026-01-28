import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.cli.utils import lazy_import

COMMAND_DESCRIPTION = "Delete a client in the database"
COMMAND_HELP = "Delete a client in the database"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Example:
      # Delete client with ID 1
      edupsyadmin delete_client 1
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the delete_client command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_id", type=int, help="id of the client to delete")


def execute(args: Namespace) -> None:
    """Execute the delete_client command."""
    clients_manager_cls = lazy_import("edupsyadmin.api.managers").ClientsManager
    clients_manager = clients_manager_cls(
        database_url=args.database_url,
    )
    clients_manager.delete_client(args.client_id)
