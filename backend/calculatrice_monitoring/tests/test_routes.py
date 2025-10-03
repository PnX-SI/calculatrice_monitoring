import pytest
from flask import url_for
from flask_login import logout_user
from pypnusershub.tests.utils import set_logged_user

from .fixtures import (
    calculatrice_permissions,
    indicators,
    monitoring_objects,
    protocol,
    protocol_with_indicators,
    protocols,
    users,
)


class TestGetIndicators:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_indicators(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["gestionnaire"])
        id_protocol = protocol_with_indicators["protocol"].id_module
        response = client.get(url_for("calculatrice.get_indicators", id_protocol=id_protocol))
        assert response.status_code == 200
        expected_names = ["Another Test Indicator", "Test Indicator", "Yet Another Test Indicator"]
        assert [indic["name"] for indic in response.json] == expected_names
        assert "description" in response.json[0]["description"]

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_empty_indicator_list(self, client, users, protocol):
        set_logged_user(client, users["gestionnaire"])
        id_protocol = protocol.id_module
        response = client.get(url_for("calculatrice.get_indicators", id_protocol=id_protocol))
        assert response.status_code == 200
        assert response.json == []

    def test_error_endpoint_requires_login(self, client):
        logout_user()
        response = client.get(url_for("calculatrice.get_indicators"))
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_error_endpoint_needs_read_permission(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["public"])
        id_protocol = protocol_with_indicators["protocol"].id_module
        response = client.get(url_for("calculatrice.get_indicators", id_protocol=id_protocol))
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_error_protocol_param_is_required(self, users, client):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_indicators"))
        assert response.status_code == 400

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_error_protocol_param_must_cast_to_integer(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_indicators", id_protocol="foo"))
        assert response.status_code == 400

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_error_target_protocol_must_exist(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_indicators", id_protocol="12345"))
        assert response.status_code == 404


class TestGetIndicator:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_indicator(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["gestionnaire"])
        indicator = protocol_with_indicators["indicators"][0]
        response = client.get(
            url_for("calculatrice.get_indicator", indicator_id=indicator.id_indicator)
        )
        assert response.status_code == 200
        assert response.json["name"] == indicator.name

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_get_indicator_login_required_error(self, client, protocol_with_indicators):
        logout_user()
        indicator = protocol_with_indicators["indicators"][0]
        response = client.get(
            url_for("calculatrice.get_indicator", indicator_id=indicator.id_indicator)
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_indicator_needs_permission_error(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["public"])
        indicator = protocol_with_indicators["indicators"][0]
        response = client.get(
            url_for("calculatrice.get_indicator", indicator_id=indicator.id_indicator)
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions", "protocol_with_indicators")
    def test_get_indicator_not_found_error(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_indicator", indicator_id=12345))
        assert response.status_code == 404


class TestGetProtocols:
    def test_error_endpoint_requires_login(self, client):
        logout_user()
        response = client.get(url_for("calculatrice.get_protocols"))
        assert response.status_code == 401

    @pytest.mark.usefixtures("protocols", "calculatrice_permissions")
    def test_get_protocols(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_protocols"))
        assert response.status_code == 200
        expected_labels = [
            "MhéO Amphibiens (test)",
            "MhéO Flore (test)",
            "MhéO Odonate (test)",
        ]
        assert [protocol["label"] for protocol in response.json] == expected_labels

    @pytest.mark.usefixtures("indicators", "calculatrice_permissions")
    def test_get_protocols_with_indicators_only(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_protocols", with_indicators_only=True))
        assert response.status_code == 200
        expected_labels = ["MhéO Flore (test)", "MhéO Odonate (test)"]
        assert [protocol["label"] for protocol in response.json] == expected_labels

    @pytest.mark.usefixtures("protocols", "calculatrice_permissions")
    def test_get_protocols_as_admin(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.get(url_for("calculatrice.get_protocols"))
        assert response.status_code == 200
        # FIXME: for now protocol name "Pedologie" without accented characters because of a bug
        # in the pre-populated database used for the CI. Names can be fixed on upgrading
        # to the next pre-populated db docker image.
        # See: https://github.com/PnX-SI/geonature_db/issues/4
        expected_labels = [
            "MhéO Amphibiens (test)",
            "MhéO Flore (test)",
            "MhéO Odonate (test)",
            "MhéO Pedologie (test)",
            "MhéO Piézométrie (test)",
        ]
        assert [protocol["label"] for protocol in response.json] == expected_labels


class TestGetProtocol:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol(self, client, users, protocols):
        set_logged_user(client, users["gestionnaire"])
        protocol = list(filter(lambda p: p.module_code == "mheo_flore_test", protocols))[0]
        response = client.get(url_for("calculatrice.get_protocol", protocol_id=protocol.id_module))
        assert response.status_code == 200
        assert response.json["code"] == protocol.module_code

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_get_protocol_login_required_error(self, client, protocols):
        logout_user()
        protocol = list(filter(lambda p: p.module_code == "mheo_flore_test", protocols))[0]
        response = client.get(url_for("calculatrice.get_protocol", protocol_id=protocol.id_module))
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol_needs_permission_error(self, client, users, protocols):
        set_logged_user(client, users["public"])
        protocol = list(filter(lambda p: p.module_code == "mheo_flore_test", protocols))[0]
        response = client.get(url_for("calculatrice.get_protocol", protocol_id=protocol.id_module))
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions", "protocols")
    def test_get_protocol_not_found_error(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_protocol", protocol_id=12345))
        assert response.status_code == 404


def test_monitoring_objects_fixture(monitoring_objects):
    assert len(monitoring_objects["sites"]) == 5
    assert len(monitoring_objects["visits"]) == 5
    assert len(monitoring_objects["observations"]) == 39


def test_indicators_fixture(indicators):
    assert len(indicators) == 5
