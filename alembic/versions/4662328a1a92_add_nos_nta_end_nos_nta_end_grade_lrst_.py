"""add nos_nta_end, nos_nta_end_grade, lrst_last_test

Revision ID: 4662328a1a92
Revises: 85f36c7c90b4
Create Date: 2025-04-28 12:49:49.362613

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4662328a1a92"
down_revision: Union[str, None] = "85f36c7c90b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("lrst_last_test", sa.String()))
    op.add_column("clients", sa.Column("nta_nos_end", sa.Boolean()))
    op.add_column("clients", sa.Column("nta_nos_end_grade", sa.String()))

    op.execute("""
               UPDATE clients
               SET nta_nos_end = FALSE
               """)


def downgrade() -> None:
    pass
