import textwrap
from argparse import ArgumentParser, Namespace

lazy from edupsyadmin.api.managers import ClientsManager

COMMAND_DESCRIPTION = "Delete a client in the database"
COMMAND_HELP = "Delete a client in the database"
COMMAND_EPILOG = textwrap.dedent(
    """\
    Example:
      # Delete client with ID 1
      edupsyadmin delete-client 1
""",
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the delete_client command."""
    parser.set_defaults(command=execute)
    parser.add_argument("client_id", type=int, help="id of the client to delete")


def execute(args: Namespace) -> None:
    """Execute the delete_client command."""
    clients_manager = ClientsManager(
        database_url=args.database_url,
    )
    clients_manager.delete_client(args.client_id)
