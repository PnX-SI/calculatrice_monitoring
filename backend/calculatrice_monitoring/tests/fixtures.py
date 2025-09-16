from uuid import uuid4

import pytest
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_permissions.models import PermAction, Permission, PermObject
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringModules
from pypnusershub.db.models import Organisme, User
from sqlalchemy import select

from calculatrice_monitoring.models import Indicator


@pytest.fixture()
def protocol():
    with db.session.begin_nested():
        protocol = TMonitoringModules(
            module_code="TESTPROTOCOL",
            uuid_module_complement=uuid4(),
            module_label="Test Protocol",
            active_frontend=True,
            active_backend=True,
            b_synthese=False,
            module_path="test_protocol",
        )
        db.session.add(protocol)
    return protocol


@pytest.fixture()
def protocol_with_indicators(protocol):
    with db.session.begin_nested():
        indicator_names = ["Test Indicator", "Another Test Indicator", "Yet Another Test Indicator"]
        for name in indicator_names:
            indicator = Indicator(
                name=name,
                id_protocol=protocol.id_module,
                description=f"This is the {name} indicator description.",
            )
            db.session.add(indicator)

    return protocol


@pytest.fixture()
def protocols():
    protocols = []
    with db.session.begin_nested():
        # FIXME: for now protocol names without accented characters are used because of a bug
        # in the pre-populated database used for the CI. Names can be fixed on upgrading
        # to the next pre-populated db docker image.
        # protocol_labels = ["Odonates", "Piézométrie", "Amphibiens", "Flore", "Pédologie"]
        # See: https://github.com/PnX-SI/geonature_db/issues/4
        protocol_labels = ["Odonates", "Piezometrie", "Amphibiens", "Flore", "Pedologie"]
        for label in protocol_labels:
            protocol = TMonitoringModules(
                module_code=label.replace(" ", "").upper(),
                uuid_module_complement=uuid4(),
                module_label=label,
                active_frontend=True,
                active_backend=True,
                b_synthese=False,
                module_path=label.replace(" ", "_").lower(),
            )
            protocols.append(protocol)
            db.session.add(protocol)
    return protocols


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app")
def users():
    def create_user(username, organisme=None):
        with db.session.begin_nested():
            user = User(groupe=False, active=True, identifiant=username, password=username)
            db.session.add(user)
            user.organisme = organisme
        return user

    users = {}
    organisme = Organisme(nom_organisme="organisme test")
    db.session.add(organisme)
    users_to_create = [
        "noright_user",
        "gestionnaire",
        "admin",
    ]
    for username in users_to_create:
        users[username] = create_user(username, organisme)

    return users


@pytest.fixture()
def calculatrice_permissions(protocols, users):
    def add_permission(role, module_code, code_action, code_object, scope):
        perm_object = db.session.execute(
            select(PermObject).filter_by(code_object=code_object)
        ).scalar_one()
        perm_action = db.session.execute(
            select(PermAction).filter_by(code_action=code_action)
        ).scalar_one()
        module = db.session.execute(
            select(TModules).filter_by(module_code=module_code)
        ).scalar_one()
        db.session.add(
            Permission(
                role=role,
                action=perm_action,
                module=module,
                object=perm_object,
                scope_value=scope,
            )
        )

    with db.session.begin_nested():
        add_permission(
            users["gestionnaire"], "CALCULATRICE", "R", "CALCULATRICE_INDICATOR", scope=2
        )
        add_permission(users["gestionnaire"], "AMPHIBIENS", "R", "MONITORINGS_MODULES", scope=2)
        add_permission(users["gestionnaire"], "FLORE", "R", "MONITORINGS_MODULES", scope=2)
        for protocol in protocols:
            add_permission(
                users["admin"], protocol.module_code, "R", "MONITORINGS_MODULES", scope=None
            )
