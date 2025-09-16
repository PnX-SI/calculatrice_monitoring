# ruff: noqa: F811  # ruff complains about pytest dependency injection of fixtures
import pytest
from flask import url_for
from flask_login import logout_user
from pypnusershub.tests.utils import set_logged_user

from .fixtures import (
    calculatrice_permissions,  # noqa: F401  # We need to import fixtures so pytest can use them
    protocol,  # noqa: F401  # We need to import fixtures so pytest can use them  # noqa: F401  # We need to import fixtures so pytest can use them
    protocol_with_indicators,  # noqa: F401  # We need to import fixtures so pytest can use them  # noqa: F401  # We need to import fixtures so pytest can use them
    protocols,  # noqa: F401  # We need to import fixtures so pytest can use them  # noqa: F401  # We need to import fixtures so pytest can use them
    users,  # noqa: F401  # We need to import fixtures so pytest can use them
)


class TestGetIndicators:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_indicators(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["gestionnaire"])
        id_protocol = protocol_with_indicators.id_module
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
        set_logged_user(client, users["noright_user"])
        id_protocol = protocol_with_indicators.id_module
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
        expected_labels = ["Amphibiens", "Flore"]
        assert [protocol["label"] for protocol in response.json] == expected_labels

    @pytest.mark.usefixtures("protocols", "calculatrice_permissions")
    def test_get_protocols_as_admin(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.get(url_for("calculatrice.get_protocols"))
        assert response.status_code == 200
        expected_labels = ["Amphibiens", "Flore", "Odonates", "Pedologie", "Piezometrie"]
        assert [protocol["label"] for protocol in response.json] == expected_labels

    def test_get_empty_protocol_list(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.get(url_for("calculatrice.get_protocols"))
        assert response.status_code == 200
        assert response.json == []
