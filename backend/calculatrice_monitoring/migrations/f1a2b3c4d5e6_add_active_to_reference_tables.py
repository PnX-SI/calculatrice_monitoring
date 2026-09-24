"""Add active to reference tables

Revision ID: f1a2b3c4d5e6
Revises: 5f25a58005f2
Create Date: 2026-09-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "5f25a58005f2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "t_reference_tables",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        schema="gn_calculatrice",
    )


def downgrade():
    op.drop_column("t_reference_tables", "active", schema="gn_calculatrice")
