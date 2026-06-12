"""Add ReferenceTable model

Revision ID: 5f25a58005f2
Revises: 93a5b9230805
Create Date: 2026-06-12 08:59:05.759006

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column

# revision identifiers, used by Alembic.
revision = "5f25a58005f2"
down_revision = "93a5b9230805"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "t_reference_tables",
        Column("id_reference_table", sa.Integer, primary_key=True),
        Column("name", sa.Unicode(64), nullable=False),
        Column("description", sa.Unicode),
        Column("code", sa.Unicode(32), nullable=False, unique=True),
        Column("data", sa.Text, nullable=False),
        schema="gn_calculatrice",
    )
    op.create_table(
        "cor_indicator_reference_table",
        Column(
            "id_indicator",
            sa.Integer,
            sa.ForeignKey("gn_calculatrice.t_indicators.id_indicator"),
            primary_key=True,
        ),
        Column(
            "id_reference_table",
            sa.Integer,
            sa.ForeignKey("gn_calculatrice.t_reference_tables.id_reference_table"),
            primary_key=True,
        ),
        schema="gn_calculatrice",
    )


def downgrade():
    op.drop_table("cor_indicator_reference_table", schema="gn_calculatrice")
    op.drop_table("t_reference_tables", schema="gn_calculatrice")
