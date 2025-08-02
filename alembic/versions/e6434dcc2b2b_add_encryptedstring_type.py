"""add EncryptedString type

Revision ID: e6434dcc2b2b
Revises: 1a90a845fa5e
Create Date: 2025-08-02 20:12:01.005422

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6434dcc2b2b"
down_revision: str | None = "1a90a845fa5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # 1. collect every column that ends in "_encr"
    encr_cols = [
        col["name"]
        for col in insp.get_columns("clients")
        if col["name"].endswith("_encr")
    ]

    # 2. convert BLOB values in those columns to TEXT
    for col in encr_cols:
        conn.execute(
            sa.text(
                f"""
                UPDATE clients
                   SET {col} = CAST({col} AS TEXT)
                 WHERE typeof({col}) = 'blob';
                """
            )
        )
