"""add case_active column to clients

Revision ID: 635a9d68fbe8
Revises: 4087c43f0c7c
Create Date: 2026-03-02 12:22:07.136023

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "635a9d68fbe8"
down_revision: str | None = "4087c43f0c7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("case_active", sa.Boolean(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("clients", "case_active")
