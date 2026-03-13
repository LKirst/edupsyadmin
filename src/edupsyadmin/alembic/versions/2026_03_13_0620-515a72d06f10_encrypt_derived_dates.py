"""encrypt dates

Revision ID: 515a72d06f10
Revises: ea4c3f900604
Create Date: 2026-03-13 06:20:48.356874

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

import edupsyadmin.db.clients
from edupsyadmin.core.encrypt import encr

# revision identifiers, used by Alembic.
revision: str = "515a72d06f10"
down_revision: str | None = "ea4c3f900604"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Define the table structure for data access
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("entry_date", sa.Date),
        column("estimated_graduation_date", sa.Date),
        column("document_shredding_date", sa.Date),
    )

    # 2. Fetch all existing data before schema changes
    connection = op.get_bind()
    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.entry_date,
            clients_table.c.estimated_graduation_date,
            clients_table.c.document_shredding_date,
        )
    ).fetchall()

    # 3. Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(
            sa.Column(
                "entry_date_encr",
                edupsyadmin.db.clients.EncryptedDate(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "estimated_graduation_date_encr",
                edupsyadmin.db.clients.EncryptedDate(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "document_shredding_date_encr",
                edupsyadmin.db.clients.EncryptedDate(),
                nullable=True,
            )
        )
        batch_op.drop_column("entry_date")
        batch_op.drop_column("estimated_graduation_date")
        batch_op.drop_column("document_shredding_date")

    # 4. Perform data migration (Encryption)
    new_clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("entry_date_encr", sa.String),
        column("estimated_graduation_date_encr", sa.String),
        column("document_shredding_date_encr", sa.String),
    )

    for client_id, entry_date, grad_date, shred_date in results:
        encrypted_entry = (
            encr.encrypt(entry_date.isoformat()) if entry_date is not None else None
        )
        encrypted_grad = (
            encr.encrypt(grad_date.isoformat()) if grad_date is not None else None
        )
        encrypted_shred = (
            encr.encrypt(shred_date.isoformat()) if shred_date is not None else None
        )

        connection.execute(
            new_clients_table.update()
            .where(new_clients_table.c.client_id == client_id)
            .values(
                entry_date_encr=encrypted_entry,
                estimated_graduation_date_encr=encrypted_grad,
                document_shredding_date_encr=encrypted_shred,
            )
        )


def downgrade() -> None:
    # 1. Define the new table structure
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("entry_date_encr", sa.String),
        column("estimated_graduation_date_encr", sa.String),
        column("document_shredding_date_encr", sa.String),
    )

    # 2. Fetch all encrypted data
    connection = op.get_bind()
    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.entry_date_encr,
            clients_table.c.estimated_graduation_date_encr,
            clients_table.c.document_shredding_date_encr,
        )
    ).fetchall()

    # 3. Revert schema changes
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(sa.Column("entry_date", sa.DATE(), nullable=True))
        batch_op.add_column(
            sa.Column("estimated_graduation_date", sa.DATE(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("document_shredding_date", sa.DATE(), nullable=True)
        )
        batch_op.drop_column("document_shredding_date_encr")
        batch_op.drop_column("estimated_graduation_date_encr")
        batch_op.drop_column("entry_date_encr")

    # 4. Perform data migration (Decryption)
    old_clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("entry_date", sa.Date),
        column("estimated_graduation_date", sa.Date),
        column("document_shredding_date", sa.Date),
    )

    for client_id, entry_encr, grad_encr, shred_encr in results:
        decrypted_entry_str = (
            encr.decrypt(entry_encr) if entry_encr is not None else None
        )
        decrypted_grad_str = encr.decrypt(grad_encr) if grad_encr is not None else None
        decrypted_shred_str = (
            encr.decrypt(shred_encr) if shred_encr is not None else None
        )

        decrypted_entry = (
            edupsyadmin.db.clients.to_date_or_none(decrypted_entry_str)
            if decrypted_entry_str
            else None
        )
        decrypted_grad = (
            edupsyadmin.db.clients.to_date_or_none(decrypted_grad_str)
            if decrypted_grad_str
            else None
        )
        decrypted_shred = (
            edupsyadmin.db.clients.to_date_or_none(decrypted_shred_str)
            if decrypted_shred_str
            else None
        )

        connection.execute(
            old_clients_table.update()
            .where(old_clients_table.c.client_id == client_id)
            .values(
                entry_date=decrypted_entry,
                estimated_graduation_date=decrypted_grad,
                document_shredding_date=decrypted_shred,
            )
        )
