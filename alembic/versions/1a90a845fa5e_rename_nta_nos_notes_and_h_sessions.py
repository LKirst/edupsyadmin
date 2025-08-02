"""rename nta_nos_notes and h_sessions

Revision ID: 1a90a845fa5e
Revises: 388539dd442b
Create Date: 2025-07-30 16:10:21.408790

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a90a845fa5e"
down_revision: str | None = "388539dd442b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename columns
    with op.batch_alter_table("clients") as batch_op:
        batch_op.alter_column(
            "nta_notes",
            new_column_name="nta_nos_notes",
            existing_type=sa.String(),
            existing_nullable=True,
        )

        batch_op.alter_column(
            "n_sessions",
            new_column_name="h_sessions",
            existing_type=sa.Float(),
            existing_nullable=False,
        )
