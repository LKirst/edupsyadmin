"""add_record_academic_year

Revision ID: 91edbee23274
Revises: 0f1497df963e
Create Date: 2026-09-09 10:57:46.999351

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from edupsyadmin.utils.academic_year import get_this_academic_year_string

# revision identifiers, used by Alembic.
revision: str = "91edbee23274"
down_revision: str | None = "0f1497df963e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    default_year = get_this_academic_year_string()
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "record_academic_year",
                sa.String(),
                nullable=False,
                server_default=sa.text(f"'{default_year}'"),
            ),
        )


def downgrade() -> None:
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.drop_column("record_academic_year")
