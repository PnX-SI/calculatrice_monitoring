"""Add overview_code to Indicator and scope to VizBlockConfig

Revision ID: c4e8a1d27f93
Revises: f1a2b3c4d5e6
Create Date: 2026-10-05 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = "c4e8a1d27f93"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None

SCHEMA = "gn_calculatrice"

# Pinned version of the VizBlockScope enum for the migration.
scope_enum = ENUM("campaign", "overview", name="vizblockscope", schema=SCHEMA, create_type=False)


def upgrade():
    op.add_column(
        "t_indicators",
        sa.Column("overview_code", sa.Unicode(), nullable=False, server_default=""),
        schema=SCHEMA,
    )
    scope_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "t_viz_block_configs",
        sa.Column("scope", scope_enum, nullable=False, server_default="campaign"),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_column("t_viz_block_configs", "scope", schema=SCHEMA)
    scope_enum.drop(op.get_bind(), checkfirst=True)
    op.drop_column("t_indicators", "overview_code", schema=SCHEMA)
