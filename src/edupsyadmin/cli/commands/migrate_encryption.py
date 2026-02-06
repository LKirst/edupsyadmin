import gc
import sys
import textwrap
from argparse import ArgumentParser, Namespace
from getpass import getpass

from edupsyadmin.core.logger import logger

COMMAND_DESCRIPTION = (
    "Re-encrypt all sensitive data with a new key. "
    "Run 'edupsyadmin edit-config' first to set your new password."
)
COMMAND_HELP = "Migrate database to new encryption system"
COMMAND_EPILOG = textwrap.dedent(
    """
    Example:
      edupsyadmin migrate-encryption

    IMPORTANT: Make a backup before running this command!
"""
)


def add_arguments(parser: ArgumentParser) -> None:
    """CLI adaptor for the migrate-encryption command."""
    parser.set_defaults(command=execute)


def execute(args: Namespace) -> None:
    """Migrate database from password-based to key-based encryption."""
    from cryptography.fernet import Fernet, InvalidToken
    from sqlalchemy import text

    from edupsyadmin.api.managers import ClientsManager
    from edupsyadmin.api.migration import MigrationError, re_encrypt_database
    from edupsyadmin.core.encrypt import (
        OLD_KDF_ITERATIONS,
        derive_key_from_password,
        get_keys_from_keyring,
        load_or_create_salt,
    )

    logger.info("Starting encryption migration process...")

    # Prompt for password securely (not echoed to terminal)
    old_password = getpass("Enter your old password: ")

    if not old_password:
        logger.error("Password cannot be empty.")
        sys.exit(1)

    # Derive old key
    salt = load_or_create_salt(args.salt_path)
    old_key = derive_key_from_password(old_password, salt, OLD_KDF_ITERATIONS)

    del old_password  # clear the reference
    gc.collect()  # encourage immediate GC (not guaranteed)

    # Get new keys from keyring (now returns a list)
    new_keys = get_keys_from_keyring(args.app_uid, args.app_username)

    if not new_keys:
        raise RuntimeError(
            "New keys not found in keyring. Run 'edupsyadmin edit-config' "
            "first, but before you do make sure you know your old password "
            "because that will be overwritten, and you need it for the migration."
        )

    # Use the primary (first) key for re-encryption
    new_primary_key = new_keys[0]

    logger.info(
        f"Found {len(new_keys)} key(s) in keyring. Using primary key for migration."
    )

    # Verify old password is correct before proceeding
    print("\nVerifying old password...")
    verification_successful = False

    try:
        clients_manager = ClientsManager(database_url=args.database_url)
        with clients_manager.Session() as session:
            table = "clients"
            column = "first_name_encr"
            try:
                test_query = f"""
                    SELECT {column} FROM {table}
                    WHERE {column} IS NOT NULL
                    LIMIT 1
                """
                logger.debug(f"Trying query: {test_query}")
                result = session.execute(text(test_query)).first()

                if result and result[0]:
                    encrypted_value = result[0]
                    logger.debug(
                        f"Found encrypted value in {table}.{column} "
                        f"(length={len(encrypted_value)})"
                    )

                    test_fernet = Fernet(old_key)
                    _ = test_fernet.decrypt(encrypted_value.encode("utf-8"))

                    logger.info(
                        f"Old password verified successfully using {table}.{column}"
                    )
                    print(
                        f"Old password verified successfully "
                        f"(tested on {table}.{column})"
                    )
                    verification_successful = True
                else:
                    logger.debug(f"No data found in {table}.{column}")

            except Exception as query_error:
                logger.debug(
                    f"Query failed for {table}.{column}: "
                    f"{type(query_error).__name__}: {query_error}"
                )

            if not verification_successful:
                logger.warning("Could not find any encrypted data to verify against.")
                print("Warning: Could not find any encrypted data to verify password.")

    except InvalidToken:
        logger.error("Old password is incorrect!")
        print("\nERROR: The old password you entered is incorrect.")
        print("The encrypted data could not be decrypted with the provided password.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Verification failed with unexpected error: {e}")
        logger.debug(f"Exception type: {type(e).__name__}")
        import traceback

        logger.debug(traceback.format_exc())

        print(f"\nWARNING: Verification failed: {type(e).__name__}: {e}")

    if not verification_successful:
        response = input("\nContinue anyway? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            logger.info("Migration cancelled by user.")
            sys.exit(1)

    # Confirm with user
    print("\n" + "=" * 50)
    print("WARNING: Database encryption migration")
    print("=" * 50)
    print("- Make sure you have a backup of your database!")
    print("- Do not interrupt this process once started")
    print("- May take several minutes for large databases")
    print("=" * 50)

    response = input("\nContinue with migration? (yes/no): ").strip().lower()
    if response not in ("yes", "y"):
        logger.info("Migration cancelled by user.")
        return

    # Perform migration
    try:
        logger.info("Starting database re-encryption...")
        print("\nMigrating database encryption...")

        clients_manager = ClientsManager(database_url=args.database_url)
        with clients_manager.Session() as session:
            re_encrypt_database(session, old_key, new_primary_key)

        logger.info("Migration completed successfully.")
        print("\n" + "=" * 50)
        print("SUCCESS: Migration completed!")
        print("=" * 50)
        print("You can now use your new password for all operations.")
        print("The old password is no longer valid.")

    except MigrationError as e:
        logger.error(f"Migration failed: {e}")
        print(f"\nERROR: {e}")
        print("Database has been rolled back to previous state.")
        print("Your data is still encrypted with the old password.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during migration: {e}")
        print(f"\nCRITICAL ERROR: {e}")
        print("Please restore from backup.")
        sys.exit(1)
