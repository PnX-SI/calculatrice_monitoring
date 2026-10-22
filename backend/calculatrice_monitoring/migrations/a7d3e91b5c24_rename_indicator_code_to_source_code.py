"""Rename Indicator code to source_code

Revision ID: a7d3e91b5c24
Revises: c4e8a1d27f93
Create Date: 2026-10-21 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7d3e91b5c24"
down_revision = "c4e8a1d27f93"
branch_labels = None
depends_on = None

SCHEMA = "gn_calculatrice"


def upgrade():
    op.alter_column("t_indicators", "code", new_column_name="source_code", schema=SCHEMA)


def downgrade():
    op.alter_column("t_indicators", "source_code", new_column_name="code", schema=SCHEMA)
