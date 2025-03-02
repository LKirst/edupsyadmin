"""add types of nachteilsausgleich

Revision ID: a92978ff4798
Revises:
Create Date: 2025-03-02 09:51:04.720811

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a92978ff4798"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = [
        ("nta_font", sa.Boolean, False),
        ("nta_aufgabentypen", sa.Boolean, False),
        ("nta_strukturierungshilfen", sa.Boolean, False),
        ("nta_arbeitsmittel", sa.Boolean, False),
        ("nta_ersatz_gewichtung", sa.Boolean, False),
        ("nta_vorlesen", sa.Boolean, False),
        ("nta_other_details", sa.UnicodeText, None),
    ]
    for column_name, column_type, default_value in columns:
        op.add_column(
            "clients", sa.Column(column_name, column_type, default=default_value)
        )

        # If the default value is not None and the column type is Boolean,
        # update existing rows to set the new column to its default value
        if default_value is not None and column_type is sa.Boolean:
            default_value = 1 if default_value is True else 0
            op.execute(f"UPDATE clients SET {column_name} = {default_value}")


def downgrade() -> None:
    columns = [
        "nta_font",
        "nta_aufgabentypen",
        "nta_strukturierungshilfen",
        "nta_arbeitsmittel",
        "nta_ersatz_gewichtung",
        "nta_vorlesen",
        "nta_other_details",
    ]
    for column_name in columns:
        op.drop_column("clients", column_name)
