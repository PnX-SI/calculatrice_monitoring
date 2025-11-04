# Those imports are required so pytest knows about those global fixtures
from uuid import uuid4

import pytest
from geonature.tests.conftest import _app, _session, app  # noqa: F401
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
)

from calculatrice_monitoring.eval import create_context, create_monitoring_collections
from calculatrice_monitoring.migrations.data.install_mheo import (
    configure_mheo_flore_test_protocol,
    get_quadrat_flore_site_type,
    get_test_protocols,
    install_i02_abondance_code,
    install_metadata,
    install_more_fake_data,
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
    return get_test_protocols()


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
def i02_abondance(indicators):
    return install_i02_abondance_code(indicators)


@pytest.fixture
def metadata():
    return install_metadata()


@pytest.fixture
def flore_site_type():
    return get_quadrat_flore_site_type()


@pytest.fixture
def flore_protocol(protocols, flore_site_type, metadata):
    return configure_mheo_flore_test_protocol(
        protocols["mheo_flore_test"], metadata["dataset"], flore_site_type
    )


@pytest.fixture
def monitoring_objects(flore_protocol, flore_site_type, users):
    return install_test_monitoring_objects(flore_protocol, flore_site_type, users)


@pytest.fixture
def more_monitoring_objects(flore_protocol, flore_site_type, users):
    return install_more_fake_data(flore_protocol, flore_site_type, users)


@pytest.fixture
def eval_context(monitoring_objects):
    collections = create_monitoring_collections(monitoring_objects["observations"])
    return create_context(collections)
