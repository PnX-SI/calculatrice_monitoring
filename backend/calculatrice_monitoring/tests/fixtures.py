from uuid import uuid4

import pytest
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
)
from sqlalchemy import select

from calculatrice_monitoring.eval import create_context, create_monitoring_collections
from calculatrice_monitoring.migrations.data.install_mheo import (
    install_test_indicators,
    install_test_monitoring_objects,
    install_test_permissions,
    install_test_users,
)
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
        indicators = []
        for name in indicator_names:
            indicator = Indicator(
                name=name,
                id_protocol=protocol.id_module,
                description=f"This is the {name} indicator description.",
            )
            indicators.append(indicator)
            db.session.add(indicator)

    return {
        "protocol": protocol,
        "indicators": indicators,
    }


@pytest.fixture()
def protocols():
    # Protocols are installed in test database beforehand (see the documentation)
    return db.session.scalars(select(TMonitoringModules)).all()


@pytest.fixture(scope="session")
@pytest.mark.usefixtures("app")
def users():
    return install_test_users()


@pytest.fixture()
def calculatrice_permissions(protocols, users):
    install_test_permissions(protocols, users)


@pytest.fixture
def indicators(protocols):
    return install_test_indicators(protocols)


@pytest.fixture
def monitoring_objects(protocols, users):
    return install_test_monitoring_objects(protocols, users)


@pytest.fixture
def eval_context(monitoring_objects):
    collections = create_monitoring_collections(monitoring_objects["observations"])
    return create_context(collections)
