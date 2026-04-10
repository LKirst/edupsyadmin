"""encrypt sensitive text fields

Revision ID: e2b4c6d8f0a1
Revises: d7e8f9a0b1c2
Create Date: 2026-03-23 10:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

import edupsyadmin.db.clients
from edupsyadmin.core.encrypt import encr

# revision identifiers, used by Alembic.
revision: str = "e2b4c6d8f0a1"
down_revision: str | None = "d7e8f9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()

    # Step 1: Add new encrypted columns
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(
            sa.Column(
                "nos_rs_ausn_faecher_encr",
                edupsyadmin.db.clients.EncryptedString(),
                nullable=True,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "nos_other_details_encr",
                edupsyadmin.db.clients.EncryptedString(),
                nullable=True,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "nta_other_details_encr",
                edupsyadmin.db.clients.EncryptedString(),
                nullable=True,
            ),
        )
        batch_op.add_column(
            sa.Column(
                "nta_nos_notes_encr",
                edupsyadmin.db.clients.EncryptedString(),
                nullable=True,
            ),
        )

    # Step 2: Fetch existing data
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("nos_rs_ausn_faecher", sa.String),
        column("nos_other_details", sa.String),
        column("nta_other_details", sa.String),
        column("nta_nos_notes", sa.String),
        column("nos_rs_ausn_faecher_encr", sa.String),
        column("nos_other_details_encr", sa.String),
        column("nta_other_details_encr", sa.String),
        column("nta_nos_notes_encr", sa.String),
    )

    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.nos_rs_ausn_faecher,
            clients_table.c.nos_other_details,
            clients_table.c.nta_other_details,
            clients_table.c.nta_nos_notes,
        ),
    ).fetchall()

    # Step 3: Migrate data with encryption (NULL -> empty string for privacy)
    for row in results:
        client_id = row[0]
        nos_rs = row[1]
        nos_other = row[2]
        nta_other = row[3]
        nta_notes = row[4]

        try:
            # Convert NULL to empty string to prevent information leakage
            encrypted_nos_rs = encr.encrypt(nos_rs or "")
            encrypted_nos_other = encr.encrypt(nos_other or "")
            encrypted_nta_other = encr.encrypt(nta_other or "")
            encrypted_nta_notes = encr.encrypt(nta_notes or "")

            # Update the row with encrypted data
            connection.execute(
                clients_table.update()
                .where(clients_table.c.client_id == client_id)
                .values(
                    nos_rs_ausn_faecher_encr=encrypted_nos_rs,
                    nos_other_details_encr=encrypted_nos_other,
                    nta_other_details_encr=encrypted_nta_other,
                    nta_nos_notes_encr=encrypted_nta_notes,
                ),
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to encrypt data for client_id {client_id}. "
                f"Migration aborted. Error: {e}",
            ) from e

    # Step 4: Drop old columns only after successful data migration
    with op.batch_alter_table("clients") as batch_op:
        batch_op.drop_column("nos_rs_ausn_faecher")
        batch_op.drop_column("nos_other_details")
        batch_op.drop_column("nta_other_details")
        batch_op.drop_column("nta_nos_notes")


def downgrade() -> None:
    connection = op.get_bind()

    # Step 1: Add back the original unencrypted columns
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(
            sa.Column("nos_rs_ausn_faecher", sa.String(), nullable=True),
        )
        batch_op.add_column(sa.Column("nos_other_details", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("nta_other_details", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("nta_nos_notes", sa.String(), nullable=True))

    # Step 2: Fetch encrypted data
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("nos_rs_ausn_faecher", sa.String),
        column("nos_other_details", sa.String),
        column("nta_other_details", sa.String),
        column("nta_nos_notes", sa.String),
        column("nos_rs_ausn_faecher_encr", sa.String),
        column("nos_other_details_encr", sa.String),
        column("nta_other_details_encr", sa.String),
        column("nta_nos_notes_encr", sa.String),
    )

    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.nos_rs_ausn_faecher_encr,
            clients_table.c.nos_other_details_encr,
            clients_table.c.nta_other_details_encr,
            clients_table.c.nta_nos_notes_encr,
        ),
    ).fetchall()

    # Step 3: Migrate data with decryption
    for row in results:
        client_id = row[0]
        nos_rs_encr = row[1]
        nos_other_encr = row[2]
        nta_other_encr = row[3]
        nta_notes_encr = row[4]

        try:
            # Decrypt values (empty string decrypts to empty string,
            # preserving original NULL->empty conversion)
            decrypted_nos_rs = (
                encr.decrypt(nos_rs_encr) if nos_rs_encr is not None else ""
            )
            decrypted_nos_other = (
                encr.decrypt(nos_other_encr) if nos_other_encr is not None else ""
            )
            decrypted_nta_other = (
                encr.decrypt(nta_other_encr) if nta_other_encr is not None else ""
            )
            decrypted_nta_notes = (
                encr.decrypt(nta_notes_encr) if nta_notes_encr is not None else ""
            )

            # Convert empty strings back to NULL for database normalization
            connection.execute(
                clients_table.update()
                .where(clients_table.c.client_id == client_id)
                .values(
                    nos_rs_ausn_faecher=decrypted_nos_rs or None,
                    nos_other_details=decrypted_nos_other or None,
                    nta_other_details=decrypted_nta_other or None,
                    nta_nos_notes=decrypted_nta_notes or None,
                ),
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to decrypt data for client_id {client_id}. "
                f"Migration rollback aborted. Error: {e}",
            ) from e

    # Step 4: Drop encrypted columns only after successful data migration
    with op.batch_alter_table("clients") as batch_op:
        batch_op.drop_column("nta_nos_notes_encr")
        batch_op.drop_column("nta_other_details_encr")
        batch_op.drop_column("nos_other_details_encr")
        batch_op.drop_column("nos_rs_ausn_faecher_encr")
