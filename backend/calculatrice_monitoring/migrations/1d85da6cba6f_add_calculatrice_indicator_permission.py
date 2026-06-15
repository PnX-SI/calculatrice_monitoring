"""Add calculatrice indicator permission

Revision ID: 1d85da6cba6f
Revises: 1e2926e0b603
Create Date: 2025-09-05 11:20:57.901943

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1d85da6cba6f"
down_revision = "1e2926e0b603"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO gn_permissions.t_objects(code_object,
                                             description_object)
        VALUES ('CALC_ADMIN_INDICATOR', 'Objet Indicateur du module calculatrice monitoring')
        """
    )
    op.execute(
        """
        INSERT INTO gn_permissions.cor_object_module
            (
                id_object,
                id_module
            )
        SELECT
            _to.id_object,
            (SELECT id_module FROM gn_commons.t_modules WHERE module_code = 'CALCULATRICE')
        FROM
            (VALUES ('CALC_ADMIN_INDICATOR')) AS o (object_code)
            JOIN gn_permissions.t_objects _to
                ON _to.code_object = o.object_code
        """
    )
    op.execute(
        """
        INSERT INTO gn_permissions.t_permissions_available (id_module,
                                                            id_object,
                                                            id_action,
                                                            label,
                                                            scope_filter)
        SELECT m.id_module,
               o.id_object,
               a.id_action,
               v.label,
               v.scope_filter
        FROM (VALUES ('CALCULATRICE', 'CALC_ADMIN_INDICATOR', 'C', False,
                      'Créer des indicateurs pour la calculatrice'),
                     ('CALCULATRICE', 'CALC_ADMIN_INDICATOR', 'R', False,
                      'Accéder aux indicateurs de la calculatrice'),
                     ('CALCULATRICE', 'CALC_ADMIN_INDICATOR', 'U', False,
                      'Modifier des indicateurs de la calculatrice'),
                     ('CALCULATRICE', 'CALC_ADMIN_INDICATOR', 'D', False,
                      'Supprimer des indicateurs de la calculatrice'))
                 AS v (module_code, object_code, action_code, scope_filter, label)
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
        DELETE
        FROM gn_permissions.t_permissions_available pa
        WHERE id_module = (SELECT id_module
                           FROM gn_commons.t_modules
                           WHERE module_code = 'CALCULATRICE')
          AND pa.id_object = (SELECT id_object
                              FROM gn_permissions.t_objects
                              WHERE code_object = 'CALC_ADMIN_INDICATOR')
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
          AND o.code_object = 'CALC_ADMIN_INDICATOR'
          AND p.id_action = a.id_action
          AND a.code_action IN ('C', 'R', 'U', 'D')
          AND p.id_module = m.id_module
          AND m.module_code = 'CALCULATRICE';
        """
    )

    op.execute(
        """
        -- Remove (CALCULATRICE, CALC_ADMIN_INDICATOR) from cor_object_module
        DELETE FROM gn_permissions.cor_object_module
        WHERE id_module = (
            SELECT id_module
            FROM gn_commons.t_modules
            WHERE module_code = 'CALCULATRICE')
        AND id_object = (
            SELECT id_object
            FROM gn_permissions.t_objects
            WHERE code_object = 'CALC_ADMIN_INDICATOR');
        """
    )

    op.execute(
        """
        DELETE
        FROM gn_permissions.t_objects
        WHERE code_object = 'CALC_ADMIN_INDICATOR';
        """
    )
