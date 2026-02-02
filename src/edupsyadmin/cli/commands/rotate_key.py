import sys
import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.api.managers import ClientsManager
from edupsyadmin.api.migration import MigrationError, re_encrypt_all_data
from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = textwrap.dedent(
    """
    Re-encrypt all data with the newest encryption key.

    This command is used to "rotate" the encryption on all sensitive data fields
    in the database so that they are all encrypted with the current primary key.
    This is a good security practice to perform after changing your password
    (which generates a new primary key).
    """
)
COMMAND_HELP = "Re-encrypt all data with the current primary key"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      edupsyadmin rotate-key

    IMPORTANT: Make a backup of your database before running this command!
    This operation can take a long time for large databases. Do not interrupt it.
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the rotate_key command."""
    parser.set_defaults(command=execute)


def execute(args: Namespace) -> None:
    """Execute the data re-encryption process."""
    # The `_setup_encryption` function in cli/__init__.py has already loaded
    # all available keys into the global `encr` instance.

    print("\nWARNING: Database-wide re-encryption")
    print("=" * 50)
    print("This will re-encrypt all sensitive data with your newest key.")
    print("- Make sure you have a backup of your database!")
    print("- This process can take several minutes for large databases.")
    print("- Do NOT interrupt this process once it has started.")
    print("=" * 50)

    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if response not in ("yes", "y"):
        logger.info("Re-encryption cancelled by user.")
        return

    try:
        clients_manager = ClientsManager(database_url=args.database_url)
        with clients_manager.Session() as session:
            re_encrypt_all_data(session)

        print("\nSUCCESS: All data has been re-encrypted with the primary key.")

    except MigrationError as e:
        logger.error(f"Re-encryption failed: {e}")
        print(f"\nERROR: {e}")
        print("The database has been rolled back to its previous state.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred during re-encryption: {e}")
        print(f"\nCRITICAL ERROR: {e}")
        print("Please restore your database from a backup.")
        sys.exit(1)
