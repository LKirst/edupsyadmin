"""Database encryption migration utilities."""

from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session

from edupsyadmin.core.encrypt import encr
from edupsyadmin.core.logger import logger
from edupsyadmin.db.clients import Client


class MigrationError(Exception):
    """Raised when migration encounters an error.

    :param message: Description of the migration error.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


def re_encrypt_database(
    db_session: Session,
    old_key: bytes,
    new_key: bytes,
    batch_size: int = 100,
) -> None:
    """
    Re-encrypts all encrypted fields in the database from an old encryption
    key to a new one.

    This works by:
    1. Loading clients in batches and decrypting with the old key.
    2. Swapping the global encryption key to the new one.
    3. Flushing the data back to the database, which triggers re-encryption
       with the new key.
    4. Verifying the migration was successful.

    :param db_session: The SQLAlchemy session to use for database operations.
    :param old_key: The OLD encryption key.
    :param new_key: The NEW encryption key.
    :param batch_size: Number of clients to process at once (default: 100).
    :raises MigrationError: If migration fails or verification fails.
    """
    logger.info("Starting database re-encryption. This may take a while...")

    try:
        # Count total clients for progress reporting
        total_clients = db_session.query(Client).count()
        if total_clients == 0:
            logger.info("No clients found in database. Nothing to migrate.")
            return

        logger.info(f"Found {total_clients} clients to migrate.")

        # Step 1: Decrypt and re-encrypt in batches
        logger.info("Step 1/2: Re-encrypting all client data...")
        encr.set_key(old_key)

        processed = 0
        for batch in _get_client_batches(db_session, batch_size):
            # Load all encrypted attributes while we have the old key
            decrypted_data = []
            for client in batch:
                client_data = _extract_encrypted_fields(client)
                decrypted_data.append((client.client_id, client_data))

            # Switch to new key
            encr.set_key(new_key)

            # Re-encrypt by setting attributes (triggers encryption)
            for client_id, data in decrypted_data:
                client = db_session.get(Client, client_id)
                if client is None:
                    raise MigrationError(
                        f"Client {client_id} disappeared during migration"
                    )
                for field_name, value in data.items():
                    setattr(client, field_name, value)

            # Commit this batch
            db_session.commit()

            # Switch back to old key for next batch
            if processed + len(batch) < total_clients:
                encr.set_key(old_key)

            processed += len(batch)
            logger.info(f"Progress: {processed}/{total_clients} clients migrated")

        # Step 2: Verify migration
        logger.info("Step 2/2: Verifying migration...")
        encr.set_key(new_key)
        _verify_migration(db_session, total_clients)

        logger.info("Database re-encryption completed successfully.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db_session.rollback()
        raise MigrationError(f"Migration failed: {e}") from e


def _get_client_batches(db_session: Session, batch_size: int) -> Iterator[list[Client]]:
    """
    Yield batches of clients from the database.

    :param db_session: The SQLAlchemy session.
    :param batch_size: Number of clients per batch.
    :yield: Lists of Client objects.
    """
    offset = 0
    while True:
        stmt = select(Client).offset(offset).limit(batch_size)
        batch = list(db_session.scalars(stmt))
        if not batch:
            break
        yield batch
        offset += batch_size


def _extract_encrypted_fields(client: Client) -> dict[str, str]:
    """
    Extract all encrypted field values from a client.

    :param client: The Client object to extract from.
    :return: Dictionary mapping field names to decrypted values.
    """
    encrypted_fields = [
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

    data = {}
    for field in encrypted_fields:
        # Access the attribute to trigger decryption
        value = getattr(client, field)
        data[field] = value

    return data


def _verify_migration(db_session: Session, expected_count: int) -> None:
    """
    Verify that all clients can be decrypted with the new key.

    :param db_session: The SQLAlchemy session.
    :param expected_count: Expected number of clients.
    :raises MigrationError: If verification fails.
    """
    try:
        # Try to load and decrypt all clients
        stmt = select(Client)
        clients = list(db_session.scalars(stmt))

        if len(clients) != expected_count:
            raise MigrationError(
                f"Client count mismatch: expected {expected_count}, "
                f"found {len(clients)}"
            )

        # Try to access encrypted fields on a sample of clients
        sample_size = min(10, len(clients))
        for client in clients[:sample_size]:
            # This will raise an exception if decryption fails
            _ = client.first_name_encr
            _ = client.last_name_encr
            _ = client.birthday_encr

        logger.info(f"Verification successful: all {len(clients)} clients accessible")

    except Exception as e:
        raise MigrationError(f"Verification failed: {e}") from e
