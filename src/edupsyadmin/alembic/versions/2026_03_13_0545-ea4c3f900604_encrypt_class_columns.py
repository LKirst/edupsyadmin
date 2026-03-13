"""encrypt class name and class int columns

Revision ID: ea4c3f900604
Revises: 635a9d68fbe8
Create Date: 2026-03-13 05:45:21.953267

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

import edupsyadmin.db.clients
from edupsyadmin.core.encrypt import encr

# revision identifiers, used by Alembic.
revision: str = "ea4c3f900604"
down_revision: str | None = "635a9d68fbe8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Define the table structure for data access
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("class_name", sa.String),
        column("class_int", sa.Integer),
    )

    # 2. Fetch all existing data before schema changes
    connection = op.get_bind()
    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.class_name,
            clients_table.c.class_int,
        )
    ).fetchall()

    # 3. Use batch_alter_table for SQLite compatibility
    # This handles dropping old columns and adding new ones correctly
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(
            sa.Column(
                "class_name_encr",
                edupsyadmin.db.clients.EncryptedString(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "class_int_encr",
                edupsyadmin.db.clients.EncryptedInteger(),
                nullable=True,
            )
        )
        batch_op.drop_column("class_int")
        batch_op.drop_column("class_name")

    # 4. Perform data migration (Encryption)
    new_clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("class_name_encr", sa.String),
        column("class_int_encr", sa.String),
    )

    for client_id, class_name, class_int in results:
        encrypted_name = encr.encrypt(class_name) if class_name is not None else None
        encrypted_int = encr.encrypt(str(class_int)) if class_int is not None else None

        connection.execute(
            new_clients_table.update()
            .where(new_clients_table.c.client_id == client_id)
            .values(class_name_encr=encrypted_name, class_int_encr=encrypted_int)
        )


def downgrade() -> None:
    # 1. Define the new table structure
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("class_name_encr", sa.String),
        column("class_int_encr", sa.String),
    )

    # 2. Fetch all encrypted data
    connection = op.get_bind()
    results = connection.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.class_name_encr,
            clients_table.c.class_int_encr,
        )
    ).fetchall()

    # 3. Revert schema changes
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(sa.Column("class_name", sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column("class_int", sa.INTEGER(), nullable=True))
        batch_op.drop_column("class_int_encr")
        batch_op.drop_column("class_name_encr")

    # 4. Perform data migration (Decryption)
    old_clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("class_name", sa.String),
        column("class_int", sa.Integer),
    )

    for client_id, class_name_encr, class_int_encr in results:
        decrypted_name = (
            encr.decrypt(class_name_encr) if class_name_encr is not None else None
        )
        decrypted_int_str = (
            encr.decrypt(class_int_encr) if class_int_encr is not None else None
        )

        decrypted_int = (
            int(decrypted_int_str) if decrypted_int_str is not None else None
        )

        connection.execute(
            old_clients_table.update()
            .where(old_clients_table.c.client_id == client_id)
            .values(class_name=decrypted_name, class_int=decrypted_int)
        )
