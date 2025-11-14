"""encrypt lrst_diagnose_encr and keyword_taet_encr and update for v7

Revision ID: 9c90e26b8e29
Revises: e6434dcc2b2b
Create Date: 2025-10-02 09:17:51.523628

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.sql import column, table

from alembic import op
from edupsyadmin.cli import (
    APP_UID,
    DEFAULT_CONFIG_PATH,
    DEFAULT_SALT_PATH,
)
from edupsyadmin.core.config import config
from edupsyadmin.core.encrypt import encr

# revision identifiers, used by Alembic.
revision: str = "9c90e26b8e29"
down_revision: str | None = "e6434dcc2b2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Initialize fernet
    config.load(DEFAULT_CONFIG_PATH)
    try:
        encr.set_fernet(
            username=config.core.app_username, salt_path=DEFAULT_SALT_PATH, uid=APP_UID
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize encryption for migration. "
            f"Please ensure that the variables for set_fernet "
            f"are correctly set in the Alembic script. "
            f"Original error: {e}"
        )

    conn = op.get_bind()

    # Data migration: Add new columns as nullable
    # (to allow me to fill them step by step)
    with op.batch_alter_table("clients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("keyword_taet_encr", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("lrst_diagnosis_encr", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("lrst_last_test_date_encr", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("lrst_last_test_by_encr", sa.String(), nullable=True)
        )

    # Data migration: Encrypt existing data
    clients_table = table(
        "clients",
        column("client_id", sa.Integer),
        column("keyword_taetigkeitsbericht", sa.String),
        column("lrst_diagnosis", sa.String),
        column("lrst_last_test_date", sa.Date),
        column("lrst_last_test_by", sa.String),
        # Define the new columns
        column("keyword_taet_encr", sa.String),
        column("lrst_diagnosis_encr", sa.String),
        column("lrst_last_test_date_encr", sa.String),
        column("lrst_last_test_by_encr", sa.String),
    )

    # Retrieve all existing data from the old columns
    old_data = conn.execute(
        sa.select(
            clients_table.c.client_id,
            clients_table.c.keyword_taetigkeitsbericht,
            clients_table.c.lrst_diagnosis,
            clients_table.c.lrst_last_test_date,
            clients_table.c.lrst_last_test_by,
        )
    ).fetchall()

    updates = []
    for row in old_data:
        # Convert `None` to "" and dates to strings before encryption
        keyword_val = row.keyword_taetigkeitsbericht or ""
        lrst_diag_val = row.lrst_diagnosis or ""
        lrst_date_val = (
            row.lrst_last_test_date.isoformat() if row.lrst_last_test_date else ""
        )
        lrst_by_val = row.lrst_last_test_by or ""

        updates.append(
            {
                "b_client_id": row.client_id,
                "keyword_taet_encr": encr.encrypt(keyword_val),
                "lrst_diagnosis_encr": encr.encrypt(lrst_diag_val),
                "lrst_last_test_date_encr": encr.encrypt(lrst_date_val),
                "lrst_last_test_by_encr": encr.encrypt(lrst_by_val),
            }
        )

    # bulk update existing data
    if updates:
        stmt = (
            sa.update(clients_table)
            .where(clients_table.c.client_id == sa.bindparam("b_client_id"))
            .values(
                {
                    "keyword_taet_encr": sa.bindparam("keyword_taet_encr"),
                    "lrst_diagnosis_encr": sa.bindparam("lrst_diagnosis_encr"),
                    "lrst_last_test_date_encr": sa.bindparam(
                        "lrst_last_test_date_encr"
                    ),
                    "lrst_last_test_by_encr": sa.bindparam("lrst_last_test_by_encr"),
                }
            )
        )
        conn.execute(stmt, updates)

    # Use the default values for rows with NULL in NOT NULL columns
    op.execute("""
        UPDATE clients
        SET
            notenschutz = COALESCE(notenschutz, 0),
            nos_rs = COALESCE(nos_rs, 0),
            nos_rs_ausn = COALESCE(nos_rs_ausn, 0),
            nos_les = COALESCE(nos_les, 0),
            nachteilsausgleich = COALESCE(nachteilsausgleich, 0),
            nta_zeitv = COALESCE(nta_zeitv, 0),
            nta_font = COALESCE(nta_font, 0),
            nta_aufg = COALESCE(nta_aufg, 0),
            nta_struktur = COALESCE(nta_struktur, 0),
            nta_arbeitsm = COALESCE(nta_arbeitsm, 0),
            nta_ersgew = COALESCE(nta_ersgew, 0),
            nta_vorlesen = COALESCE(nta_vorlesen, 0),
            nta_other = COALESCE(nta_other, 0),
            nta_nos_end = COALESCE(nta_nos_end, 0),
            h_sessions = COALESCE(h_sessions, 1.0)
    """)

    # Schema migration: Apply all schema changes
    with op.batch_alter_table("clients", schema=None) as batch_op:
        # Set the new columns to non-nullable after all data has been added
        batch_op.alter_column("keyword_taet_encr", nullable=False)
        batch_op.alter_column("lrst_diagnosis_encr", nullable=False)
        batch_op.alter_column("lrst_last_test_date_encr", nullable=False)
        batch_op.alter_column("lrst_last_test_by_encr", nullable=False)

        # Delete the old columns
        batch_op.drop_column("keyword_taetigkeitsbericht")
        batch_op.drop_column("lrst_last_test_date")
        batch_op.drop_column("lrst_diagnosis")
        batch_op.drop_column("lrst_last_test_by")

        # All remaining schema changes
        batch_op.alter_column(
            "first_name_encr", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column(
            "last_name_encr", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column("gender_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column(
            "birthday_encr", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column("street_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("city_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("parent_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column(
            "telephone1_encr", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column(
            "telephone2_encr", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column("email_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("notes_encr", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column("school", existing_type=sa.VARCHAR(), nullable=False)
        batch_op.alter_column(
            "datetime_created", existing_type=sa.DATETIME(), nullable=False
        )
        batch_op.alter_column(
            "datetime_lastmodified", existing_type=sa.DATETIME(), nullable=False
        )
        batch_op.alter_column("notenschutz", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("nos_rs", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("nos_rs_ausn", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("nos_les", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "nachteilsausgleich", existing_type=sa.BOOLEAN(), nullable=False
        )
        batch_op.alter_column("nta_zeitv", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("nta_font", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column("nta_aufg", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "nta_struktur", existing_type=sa.BOOLEAN(), nullable=False
        )
        batch_op.alter_column(
            "nta_arbeitsm", existing_type=sa.BOOLEAN(), nullable=False
        )
        batch_op.alter_column("nta_ersgew", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "nta_vorlesen", existing_type=sa.BOOLEAN(), nullable=False
        )
        batch_op.alter_column("nta_other", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "nta_other_details",
            existing_type=sa.TEXT(),
            type_=sa.String(),
            existing_nullable=True,
        )
        batch_op.alter_column("nta_nos_end", existing_type=sa.BOOLEAN(), nullable=False)
        batch_op.alter_column(
            "nta_nos_end_grade",
            existing_type=sa.VARCHAR(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column("h_sessions", existing_type=sa.FLOAT(), nullable=False)
