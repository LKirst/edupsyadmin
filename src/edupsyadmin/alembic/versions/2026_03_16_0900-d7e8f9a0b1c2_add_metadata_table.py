"""add metadata table and migrate salt

Revision ID: d7e8f9a0b1c2
Revises: 515a72d06f10
Create Date: 2026-03-16 09:00:00.000000

"""

import os
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from edupsyadmin.core.paths import DEFAULT_SALT_PATH

# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: str | None = "515a72d06f10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create system_metadata table
    op.create_table(
        "system_metadata",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    # 2. Migrate existing salt
    salt = None
    if DEFAULT_SALT_PATH.exists():
        salt = DEFAULT_SALT_PATH.read_bytes()
    else:
        salt = os.urandom(16)

    # Insert into the new table
    op.execute(
        sa.text(
            "INSERT INTO system_metadata (key, value) VALUES ('salt', :salt_hex)"
        ).bindparams(salt_hex=salt.hex())
    )


def downgrade() -> None:
    op.drop_table("system_metadata")
