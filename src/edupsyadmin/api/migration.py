"""Database encryption migration utilities."""

from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger
from edupsyadmin.db.clients import Client


class MigrationError(Exception):
    """Raised when migration encounters an error."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def re_encrypt_database(
    db_session: Session,
    old_key: bytes,
    new_key: bytes,
    batch_size: int = 50,
) -> None:
    """
    Re-encrypt all encrypted fields from old_key to new_key.

    Strategy:
    - Initialize encr once with [new_key, old_key]; MultiFernet decrypts with any,
      encrypts with the first (new_key).
    - For each encrypted field, read (decrypt) and assign back (re-encrypt with
      new_key).
    - Force UPDATEs via flag_modified to ensure the ciphertext is rewritten.
    """
    logger.info("Starting database re-encryption. This may take a while...")

    # Initialize once: new primary first, then old for backward decryption
    encr.set_keys([new_key, old_key])

    try:
        total_clients = db_session.query(Client).count()
        if total_clients == 0:
            logger.info("No clients found in database. Nothing to migrate.")
            return

        logger.info(f"Found {total_clients} clients to migrate.")
        logger.info("Step 1/2: Re-encrypting all client data...")

        processed = 0
        encrypted_fields = _get_encrypted_field_names()

        for batch in _get_client_batches(db_session, batch_size):
            for client in batch:
                for field_name in encrypted_fields:
                    try:
                        # Read -> decrypts using MultiFernet (old or new)
                        current_value = getattr(client, field_name)
                        # Write -> encrypts with primary (new_key)
                        setattr(client, field_name, current_value)
                        # Ensure UPDATE even if plaintext unchanged
                        flag_modified(client, field_name)
                    except ValueError as e:
                        raise MigrationError(
                            f"Validation failed for client_id={client.client_id}, "
                            f"field='{field_name}'. Details: {e}"
                        ) from e

            db_session.commit()
            db_session.expunge_all()

            processed += len(batch)
            logger.info(f"Progress: {processed}/{total_clients} clients migrated")

        # Step 2: Verify with only the new key
        logger.info("Step 2/2: Verifying migration...")
        encr.set_keys([new_key])
        _verify_migration(db_session, total_clients)

        logger.info("Database re-encryption completed successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db_session.rollback()
        raise MigrationError(f"Migration failed: {e}") from e


def re_encrypt_all_data(db_session: Session, batch_size: int = 100) -> None:
    """
    Re-encrypt all data with the current primary key.

    Assumes the global `encr` has already been initialized with MultiFernet
    (primary first, then any older keys) by CLI setup. This preserves the
    rotate_key command behavior.
    """
    if not encr.is_initialized:
        raise MigrationError("Encryption is not initialized.")

    logger.info(
        "Starting data re-encryption to rotate all fields to the primary key..."
    )

    try:
        total_clients = db_session.query(Client).count()
        if total_clients == 0:
            logger.info("No clients in the database. Nothing to re-encrypt.")
            return

        logger.info(f"Found {total_clients} clients to process.")

        processed_count = 0
        encrypted_fields = _get_encrypted_field_names()

        for batch in _get_client_batches(db_session, batch_size):
            for client in batch:
                for field_name in encrypted_fields:
                    try:
                        current_value = getattr(client, field_name)  # decrypt
                        setattr(
                            client, field_name, current_value
                        )  # re-encrypt with primary
                        # Ensure UPDATE even if plaintext unchanged
                        flag_modified(client, field_name)
                    except ValueError as e:
                        raise MigrationError(
                            "Validation failed during re-encryption for "
                            f"client_id={client.client_id}, field='{field_name}'. "
                            f"Details: {e}"
                        ) from e

            db_session.commit()
            processed_count += len(batch)
            logger.info(
                f"Progress: {processed_count}/{total_clients} clients processed."
            )

        logger.info("Verifying re-encryption...")
        _verify_migration(db_session, total_clients)

        logger.info("Data re-encryption completed successfully.")

    except Exception as e:
        logger.error(f"Data re-encryption failed: {e}")
        db_session.rollback()
        raise MigrationError(f"Data re-encryption failed: {e}") from e


def _get_client_batches(db_session: Session, batch_size: int) -> Iterator[list[Client]]:
    offset = 0
    while True:
        stmt = select(Client).offset(offset).limit(batch_size)
        batch = list(db_session.scalars(stmt))
        if not batch:
            break
        yield batch
        offset += batch_size


def _get_encrypted_field_names() -> list[str]:
    return [
        "first_name_encr",
        "last_name_encr",
        "gender_encr",
        "birthday_encr",
        "street_encr",
        "city_encr",
        "parent_encr",
        "telephone1_encr",
        "telephone2_encr",
        "email_encr",
        "notes_encr",
        "keyword_taet_encr",
        "lrst_diagnosis_encr",
        "lrst_last_test_date_encr",
        "lrst_last_test_by_encr",
    ]


def _verify_migration(db_session: Session, expected_count: int) -> None:
    try:
        stmt = select(Client)
        clients = list(db_session.scalars(stmt))

        if len(clients) != expected_count:
            raise MigrationError(
                f"Client count mismatch: expected {expected_count}, "
                f"found {len(clients)}"
            )

        sample_size = min(10, len(clients))
        for client in clients[:sample_size]:
            _ = client.first_name_encr
            _ = client.last_name_encr
            _ = client.birthday_encr

        logger.info(f"Verification successful: all {len(clients)} clients accessible")
    except Exception as e:
        raise MigrationError(f"Verification failed: {e}") from e
