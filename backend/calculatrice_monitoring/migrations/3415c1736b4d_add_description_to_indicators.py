"""Add description to indicators

Revision ID: 3415c1736b4d
Revises: c78bdb395042
Create Date: 2025-09-25 11:59:35.122267

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3415c1736b4d"
down_revision = "c78bdb395042"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "t_indicators",
        sa.Column(
            "description",
            sa.Unicode(),
        ),
        schema="gn_calculatrice",
    )


def downgrade():
    op.drop_column("t_indicators", "description", schema="gn_calculatrice")
