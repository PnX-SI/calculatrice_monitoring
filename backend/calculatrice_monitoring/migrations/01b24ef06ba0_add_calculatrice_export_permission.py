"""Add calculatrice export permission

Revision ID: 01b24ef06ba0
Revises: 1d85da6cba6f
Create Date: 2025-09-05 11:51:36.009433

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "01b24ef06ba0"
down_revision = "1d85da6cba6f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO
            gn_permissions.t_permissions_available (
                id_module,
                id_object,
                id_action,
                label,
                scope_filter
            )
        SELECT
            m.id_module,
            o.id_object,
            a.id_action,
            v.label,
            v.scope_filter
        FROM
            (
                VALUES
                    ('CALCULATRICE', 'ALL', 'E', False,
                    'Exporter les résultats d''un indicateur ainsi que les tableaux de référence')
            ) AS v (module_code, object_code, action_code, scope_filter, label)
        JOIN
            gn_commons.t_modules m ON m.module_code = v.module_code
        JOIN
            gn_permissions.t_objects o ON o.code_object = v.object_code
        JOIN
            gn_permissions.bib_actions a ON a.code_action = v.action_code
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM gn_permissions.t_permissions_available pa
        USING gn_commons.t_modules m, gn_permissions.t_objects o, gn_permissions.bib_actions a
        WHERE pa.id_object = o.id_object
          AND o.code_object = 'ALL'
          AND pa.id_action = a.id_action
          AND a.code_action = 'E'
          AND pa.id_module = m.id_module
          AND m.module_code = 'CALCULATRICE';
        """
    )
    # We also remove effective user permissions created from the available permissions
    # of this migration
    op.execute(
        """
        DELETE
        FROM gn_permissions.t_permissions p
        USING gn_commons.t_modules m, gn_permissions.t_objects o, gn_permissions.bib_actions a
        WHERE p.id_object = o.id_object
          AND o.code_object = 'ALL'
          AND p.id_action = a.id_action
          AND a.code_action = 'E'
          AND p.id_module = m.id_module
          AND m.module_code = 'CALCULATRICE';
        """
    )
