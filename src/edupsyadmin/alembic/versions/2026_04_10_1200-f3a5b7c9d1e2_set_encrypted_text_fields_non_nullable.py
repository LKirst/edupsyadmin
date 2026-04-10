"""set encrypted text fields non-nullable

Revision ID: f3a5b7c9d1e2
Revises: e2b4c6d8f0a1
Create Date: 2026-04-10 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

import edupsyadmin.db.clients

# revision identifiers, used by Alembic.
revision: str = "f3a5b7c9d1e2"
down_revision: str | None = "e2b4c6d8f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Set existing nullable encrypted string columns to NOT NULL.
    # Data migration (NULL -> "") was already handled in e2b4c6d8f0a1.
    with op.batch_alter_table("clients") as batch_op:
        batch_op.alter_column(
            "nos_rs_ausn_faecher_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=False,
        )
        batch_op.alter_column(
            "nos_other_details_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=False,
        )
        batch_op.alter_column(
            "nta_other_details_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=False,
        )
        batch_op.alter_column(
            "nta_nos_notes_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("clients") as batch_op:
        batch_op.alter_column(
            "nta_nos_notes_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=True,
        )
        batch_op.alter_column(
            "nta_other_details_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=True,
        )
        batch_op.alter_column(
            "nos_other_details_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=True,
        )
        batch_op.alter_column(
            "nos_rs_ausn_faecher_encr",
            type_=edupsyadmin.db.clients.EncryptedString(),
            nullable=True,
        )
