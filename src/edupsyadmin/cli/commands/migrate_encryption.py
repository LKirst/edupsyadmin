import sys
import textwrap
from argparse import ArgumentParser, Namespace

from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = (
    "Re-encrypt all sensitive data with a new key. "
    "Run 'edupsyadmin edit_config' first to set your new password."
)
COMMAND_HELP = "Migrate database to new encryption system"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      edupsyadmin migrate_encryption "my_old_password"

    IMPORTANT: Make a backup before running this command!
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the migrate_encryption command."""
    parser.set_defaults(command=execute)
    parser.add_argument("old_password", help="Your old password")


def execute(args: Namespace) -> None:
    """Migrate database from password-based to key-based encryption."""
    from edupsyadmin.api.managers import ClientsManager
    from edupsyadmin.api.migration import MigrationError, re_encrypt_database
    from edupsyadmin.core.encrypt import (
        OLD_KDF_ITERATIONS,
        derive_key_from_password,
        get_key_from_keyring,
        load_or_create_salt,
    )

    logger.info("Starting encryption migration process...")

    # Derive keys
    salt = load_or_create_salt(args.salt_path)
    old_key = derive_key_from_password(args.old_password, salt, OLD_KDF_ITERATIONS)
    new_key = get_key_from_keyring(args.app_uid, args.app_username)

    if not new_key:
        raise RuntimeError(
            "New key not found in keyring. Run 'edupsyadmin edit_config' first."
        )

    # Confirm with user
    print("\nWARNING: Database encryption migration")
    print("=" * 50)
    print("- Make sure you have a backup of your database!")
    print("- Do not interrupt this process once started")
    print("- May take several minutes for large databases")
    print("=" * 50)

    response = input("\nContinue? (yes/no): ").strip().lower()
    if response not in ("yes", "y"):
        logger.info("Migration cancelled by user.")
        return

    # Perform migration
    try:
        clients_manager = ClientsManager(database_url=args.database_url)
        with clients_manager.Session() as session:
            re_encrypt_database(session, old_key, new_key)

        print("\nSUCCESS: Migration completed!")
        print("You can now use your new password for all operations.")

    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        print(f"\nERROR: {e}")
        print("Database rolled back to previous state.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during migration: {e}")
        print(f"\nCRITICAL ERROR: {e}")
        print("Please restore from backup.")
        sys.exit(1)
