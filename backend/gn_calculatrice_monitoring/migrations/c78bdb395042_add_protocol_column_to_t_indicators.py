"""Add protocol column to t_indicators

Revision ID: c78bdb395042
Revises: 01b24ef06ba0
Create Date: 2025-09-18 09:54:05.209300

"""

import sqlalchemy as sa
from alembic import op
from gn_calculatrice_monitoring import SCHEMA

# revision identifiers, used by Alembic.
revision = "c78bdb395042"
down_revision = "01b24ef06ba0"
branch_labels = None
depends_on = ("362cf9d504ec",)  # monitorings: creation of gn_monitoring.t_module_complements


def upgrade():
    op.add_column(
        "t_indicators",
        sa.Column(
            "id_protocol",
            sa.Integer(),
            sa.ForeignKey("gn_monitoring.t_module_complements.id_module"),
            nullable=False,
        ),
        schema=SCHEMA,
    )


def downgrade():
    op.drop_column("t_indicators", "id_protocol", schema=SCHEMA)
