"""Add code property to Indicator

Revision ID: 918da8de2de0
Revises: 3415c1736b4d
Create Date: 2025-11-04 10:09:56.892682

"""

import sqlalchemy as sa
from alembic import op
from gn_calculatrice_monitoring import SCHEMA

# revision identifiers, used by Alembic.
revision = "918da8de2de0"
down_revision = "3415c1736b4d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "t_indicators",
        sa.Column(
            "code",
            sa.Unicode(),
            nullable=False,
            server_default="",
        ),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_column("t_indicators", "code", schema=SCHEMA)
