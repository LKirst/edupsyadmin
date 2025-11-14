"""move from h_sessions to min_sessions and add n_sessions

Revision ID: 90ec66e24754
Revises: 9c90e26b8e29
Create Date: 2025-10-02 13:46:51.610563

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "90ec66e24754"
down_revision: str | None = "9c90e26b8e29"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Add new columns as nullable to allow for data migration.
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("min_sessions", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("n_sessions", sa.Integer(), nullable=True))

    # Step 2: Transform and move existing data from `h_sessions`.
    # We read the old hour values, convert them to minutes, and write them
    # to the new columns along with a default value for `n_sessions`.
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("h_sessions", sa.Float),
        # Define the new columns for the update operation
        column("min_sessions", sa.Integer),
        column("n_sessions", sa.Integer),
    )

    old_data = conn.execute(
        sa.select(clients_table.c.client_id, clients_table.c.h_sessions)
    ).fetchall()

    updates = []
    if old_data:
        for row in old_data:
            # If h_sessions exists, convert hours to minutes and round.
            # Set n_sessions to 1 as a sensible default for existing data.
            # If h_sessions is NULL or 0, set both new values to 0.
            if row.h_sessions is not None and row.h_sessions > 0:
                minutes_value = round(row.h_sessions * 60)
                n_sessions_value = 1
            else:
                minutes_value = 0
                n_sessions_value = 0

            updates.append(
                {
                    "b_client_id": row.client_id,
                    "min_sessions": minutes_value,
                    "n_sessions": n_sessions_value,
                }
            )

    # Perform a bulk update for all records.
    if updates:
        stmt = (
            sa.update(clients_table)
            .where(clients_table.c.client_id == sa.bindparam("b_client_id"))
            .values(
                {
                    "min_sessions": sa.bindparam("min_sessions"),
                    "n_sessions": sa.bindparam("n_sessions"),
                }
            )
        )
        conn.execute(stmt, updates)

    # Step 3: Finalize schema changes
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.alter_column(
            "min_sessions", existing_type=sa.Integer(), nullable=False
        )
        batch_op.alter_column("n_sessions", existing_type=sa.Integer(), nullable=False)

        # Drop the old `h_sessions` column.
        batch_op.drop_column("h_sessions")
