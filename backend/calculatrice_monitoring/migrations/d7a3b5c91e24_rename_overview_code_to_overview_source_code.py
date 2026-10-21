"""Rename overview_code to overview_source_code on Indicator

Revision ID: d7a3b5c91e24
Revises: c4e8a1d27f93
Create Date: 2026-10-21 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d7a3b5c91e24"
down_revision = "a7d3e91b5c24"
branch_labels = None
depends_on = None

SCHEMA = "gn_calculatrice"


def upgrade():
    op.alter_column(
        "t_indicators",
        "overview_code",
        new_column_name="overview_source_code",
        schema=SCHEMA,
    )


def downgrade():
    op.alter_column(
        "t_indicators",
        "overview_source_code",
        new_column_name="overview_code",
        schema=SCHEMA,
    )
