"""Add Indicator

Revision ID: 78ba67f597ee
Revises: b6e0860c99b8
Create Date: 2025-08-28 11:07:04.288359

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.schema import Column
from gn_calculatrice_monitoring import SCHEMA

# revision identifiers, used by Alembic.
revision = "78ba67f597ee"
down_revision = "b6e0860c99b8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "t_indicators",
        Column("id_indicator", sa.Integer(), primary_key=True),
        Column("name", sa.Unicode(100), nullable=False),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_table("t_indicators", schema=SCHEMA)
