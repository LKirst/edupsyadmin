"""add nos_rs

Revision ID: 85f36c7c90b4
Revises: 0a0afffd396f
Create Date: 2025-04-08 04:32:02.774662

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "85f36c7c90b4"
down_revision: Union[str, None] = "0a0afffd396f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("nos_rs", sa.Boolean()))
    op.execute(
        """
        UPDATE clients
        SET nos_rs = notenschutz
        """
    )


def downgrade() -> None:
    pass
