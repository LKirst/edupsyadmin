"""add new lrst_diagnosis_by column, rename some columns, use date type for dates

Revision ID: 388539dd442b
Revises: 4662328a1a92
Create Date: 2025-07-02 11:58:39.709561

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "388539dd442b"
down_revision: Union[str, None] = "4662328a1a92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("clients", recreate="always") as batch:
        # Add temporary columns with the correct type
        batch.add_column(sa.Column("entry_date_tmp", sa.Date(), nullable=True))
        batch.add_column(
            sa.Column("document_shredding_date_tmp", sa.Date(), nullable=True)
        )
        batch.add_column(
            sa.Column("estimated_graduation_date_tmp", sa.Date(), nullable=True)
        )
        batch.add_column(sa.Column("lrst_last_test_date_tmp", sa.Date(), nullable=True))

    # Update the temporary columns with correctly converted date values
    op.execute("""
        UPDATE clients
        SET
            entry_date_tmp = DATE(entry_date),
            document_shredding_date_tmp = DATE(document_shredding_date),
            estimated_graduation_date_tmp = DATE(estimated_date_of_graduation),
            lrst_last_test_date_tmp = DATE(lrst_last_test)
    """)

    with op.batch_alter_table("clients", recreate="always") as batch:
        # Drop original columns
        batch.drop_column("entry_date")
        batch.drop_column("document_shredding_date")
        batch.drop_column("estimated_date_of_graduation")
        batch.drop_column("lrst_last_test")

        # Rename temporary columns to original names
        batch.alter_column("entry_date_tmp", new_column_name="entry_date")
        batch.alter_column(
            "document_shredding_date_tmp", new_column_name="document_shredding_date"
        )
        batch.alter_column(
            "estimated_graduation_date_tmp", new_column_name="estimated_graduation_date"
        )
        batch.alter_column(
            "lrst_last_test_date_tmp", new_column_name="lrst_last_test_date"
        )

        # Add new columns
        batch.add_column(sa.Column("lrst_last_test_by", sa.String(), nullable=True))
        batch.add_column(
            sa.Column(
                "nos_other",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),  # bool in SQLite is int 0/1
            )
        )
        batch.add_column(sa.Column("nos_other_details", sa.String(), nullable=True))

    # Remove the temporary default again
    with op.batch_alter_table("clients", recreate="always") as batch:
        batch.alter_column(
            "nos_other",
            server_default=None,
            existing_type=sa.Boolean(),
            existing_nullable=False,
        )
