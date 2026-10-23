"""Add statistical_tests_source_code to Indicator and statistical_tests VizBlockScope

Revision ID: e9b4c7d2a615
Revises: d7a3b5c91e24
Create Date: 2026-10-21 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e9b4c7d2a615"
down_revision = "d7a3b5c91e24"
branch_labels = None
depends_on = None

SCHEMA = "gn_calculatrice"


def upgrade():
    op.add_column(
        "t_indicators",
        sa.Column("statistical_tests_source_code", sa.Unicode(), nullable=False, server_default=""),
        schema=SCHEMA,
    )
    # `ALTER TYPE ... ADD VALUE` cannot run inside a transaction block.
    with op.get_context().autocommit_block():
        op.execute(f"ALTER TYPE {SCHEMA}.vizblockscope ADD VALUE IF NOT EXISTS 'statistical_tests'")


def downgrade():
    # PostgreSQL cannot drop a value from an enum type: `statistical_tests` stays in the
    # `vizblockscope` type.
    op.execute(f"DELETE FROM {SCHEMA}.t_viz_block_configs WHERE scope = 'statistical_tests'")
    op.drop_column("t_indicators", "statistical_tests_source_code", schema=SCHEMA)
