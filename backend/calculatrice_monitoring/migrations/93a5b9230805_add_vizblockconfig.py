"""Add VizBlockConfig

Revision ID: 93a5b9230805
Revises: 918da8de2de0
Create Date: 2025-11-04 11:23:41.341548

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.schema import Column

# revision identifiers, used by Alembic.
revision = "93a5b9230805"
down_revision = "918da8de2de0"
branch_labels = None
depends_on = None


# Pinned version of the ViBlockType enum for the migration.
class VizBlockType(enum.Enum):
    scalar = "scalaire"
    bar_chart = "barChart"


def upgrade():
    op.create_table(
        "t_viz_block_configs",
        Column("id_viz_block_config", sa.Integer, primary_key=True),
        Column(
            "id_indicator",
            sa.Integer,
            sa.ForeignKey("gn_calculatrice.t_indicators.id_indicator"),
            nullable=False,
        ),
        Column("title", sa.Unicode(100), nullable=False),
        Column("info", sa.Unicode, nullable=False, default=""),
        Column("description", sa.Unicode, nullable=False, default=""),
        Column("type", Enum(VizBlockType)),
        Column("params", JSONB),
        schema="gn_calculatrice",
    )


def downgrade():
    op.drop_table("t_viz_block_configs", schema="gn_calculatrice")
    op.execute("DROP TYPE vizblocktype")
