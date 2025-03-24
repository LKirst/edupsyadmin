"""add new nta columns and rename some existing

Revision ID: 0a0afffd396f
Revises: a92978ff4798
Create Date: 2025-03-23 13:12:22.314044

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a0afffd396f"
down_revision: Union[str, None] = "a92978ff4798"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    new_cols_bool = ["nos_rs_ausn", "nos_les", "nta_zeitv", "nta_other"]
    for var in new_cols_bool:
        op.add_column("clients", sa.Column(var, sa.Boolean()))
    op.add_column(
        "clients", sa.Column("nos_rs_ausn_faecher", sa.String(), nullable=True)
    )

    # Fill existing boolean columns where NULL
    cols_not_nullable = [
        "notenschutz",
        "nachteilsausgleich",
        "nta_font",
        "nta_vorlesen",
    ]
    for var in cols_not_nullable:
        op.execute(
            f"""
            UPDATE clients
            SET {var} = FALSE
            WHERE {var} IS NULL
            """
        )
    op.execute(
        """
        UPDATE clients
        SET nta_zeitv = nachteilsausgleich
        """
    )

    # Rename columns
    rename_vars = [
        ("nta_arbeitsmittel", "nta_arbeitsm"),
        ("nta_strukturierungshilfen", "nta_struktur"),
        ("nta_sprachen", "nta_zeitv_vieltext"),
        ("nta_mathephys", "nta_zeitv_wenigtext"),
        ("nta_aufgabentypen", "nta_aufg"),
        ("nta_ersatz_gewichtung", "nta_ersgew"),
    ]
    for var_old, var_new in rename_vars:
        op.alter_column("clients", var_old, new_column_name=var_new)
