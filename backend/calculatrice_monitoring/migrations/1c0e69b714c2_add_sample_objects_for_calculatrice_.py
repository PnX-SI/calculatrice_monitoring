"""Add sample objects for calculatrice module

Revision ID: 1c0e69b714c2
Create Date: 2025-09-30 17:10:48.132932

"""

from calculatrice_monitoring.migrations.data.install_mheo import install_all_test_sample_objects
from geonature.utils.env import db

# revision identifiers, used by Alembic.
revision = "1c0e69b714c2"
down_revision = None
branch_labels = ("calculatrice-samples-test",)
depends_on = ("3415c1736b4d",)  # add description to indicators


def upgrade():
    install_all_test_sample_objects()
    db.session.commit()


def downgrade():
    raise NotImplementedError(
        "downgrade is not implemented for the calculatrice module test samples"
    )
