import json
from io import BytesIO
from pathlib import Path
from typing import Optional

import pytest
from flask import url_for
from flask_login import logout_user
from geonature.utils.env import db
from pypnusershub.tests.utils import set_logged_user
from sqlalchemy import select
from werkzeug.datastructures import Headers

from calculatrice_monitoring.blueprint import (
    REFERENCE_TABLE_MAX_FILE_SIZE,
    REFERENCE_TABLE_MAX_VALUE_LENGTH,
)
from calculatrice_monitoring.eval import VisualizationErrorType
from calculatrice_monitoring.models import Indicator, ReferenceTable, VizBlockConfig, VizBlockType


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
    def test_get_protocol(self, client, users, flore_protocol):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(
            url_for("calculatrice.get_protocol", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 200
        assert response.json["code"] == flore_protocol.module_code

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_get_protocol_login_required_error(self, client, flore_protocol):
        logout_user()
        response = client.get(
            url_for("calculatrice.get_protocol", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol_needs_permission_error(self, client, users, flore_protocol):
        set_logged_user(client, users["public"])
        response = client.get(
            url_for("calculatrice.get_protocol", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions", "protocols")
    def test_get_protocol_not_found_error(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_protocol", protocol_id=12345))
        assert response.status_code == 404


class TestGetProtocolProperties:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol_properties(self, client, users, protocols):
        set_logged_user(client, users["gestionnaire"])
        flore_protocol = protocols["mheo_flore_test"]
        response = client.get(
            url_for("calculatrice.get_protocol_properties", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 200
        for scope in ["observation", "site", "visit"]:
            assert scope in response.json
        assert "superficie_mètres_carrés" in response.json["site"]
        assert "diffusion_mesure" in response.json["visit"]
        assert "durée_secondes" in response.json["visit"]
        assert "abondance" in response.json["observation"]
        assert "récolte" in response.json["observation"]

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_get_protocol_properties_login_required_error(self, client, protocols):
        logout_user()
        flore_protocol = protocols["mheo_flore_test"]
        response = client.get(
            url_for("calculatrice.get_protocol_properties", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol_properties_needs_permission_error(self, client, users, protocols):
        set_logged_user(client, users["public"])
        flore_protocol = protocols["mheo_flore_test"]
        response = client.get(
            url_for("calculatrice.get_protocol_properties", protocol_id=flore_protocol.id_module)
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions", "protocols")
    def test_get_protocol_properties_not_found_error(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_protocol_properties", protocol_id=12345))
        assert response.status_code == 404


def test_monitoring_objects_fixture(monitoring_objects):
    assert len(monitoring_objects["sites_groups"]) == 1
    assert len(monitoring_objects["sites"]) == 5
    assert len(monitoring_objects["visits"]) == 5
    assert len(monitoring_objects["observations"]) == 39


def test_more_monitoring_objects_fixture(more_monitoring_objects):
    assert len(more_monitoring_objects["sites_groups"]) == 2
    assert len(more_monitoring_objects["sites"]) == 8
    assert len(more_monitoring_objects["visits"]) == 8
    assert len(more_monitoring_objects["observations"]) == 21


def test_indicators_fixture(indicators):
    assert len(indicators) == 5


class TestCreateIndicator:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator(self, client, users, protocol, reference_tables):
        reftable_id = reference_tables["indices_he"].id_reference_table
        set_logged_user(client, users["admin"])
        payload = {
            "name": "New Indicator",
            "description": "A brand new indicator.",
            "protocolId": protocol.id_module,
            "referenceTableIds": [reftable_id],
        }
        response = client.post(url_for("calculatrice.create_indicator"), json=payload)
        assert response.status_code == 201
        assert response.json["name"] == "New Indicator"
        assert response.json["protocolId"] == protocol.id_module

        created = db.session.get(Indicator, response.json["id"])
        assert created is not None
        assert created.name == "New Indicator"
        assert created.description == "A brand new indicator."
        assert created.id_protocol == protocol.id_module
        assert len(created.reference_tables) == 1
        assert reftable_id in [rt.id_reference_table for rt in created.reference_tables]

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_without_description(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        payload = {"name": "No Description", "protocolId": protocol.id_module}
        response = client.post(url_for("calculatrice.create_indicator"), json=payload)
        assert response.status_code == 201
        created = db.session.get(Indicator, response.json["id"])
        assert created.description == ""

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_create_indicator_login_required_error(self, client):
        logout_user()
        response = client.post(
            url_for("calculatrice.create_indicator"), json={"name": "x", "protocolId": 1}
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_needs_create_permission_error(self, client, users, protocol):
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not C.
        set_logged_user(client, users["gestionnaire"])
        payload = {"name": "Forbidden", "protocolId": protocol.id_module}
        response = client.post(url_for("calculatrice.create_indicator"), json=payload)
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_missing_name_error(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        response = client.post(
            url_for("calculatrice.create_indicator"), json={"protocolId": protocol.id_module}
        )
        assert response.status_code == 400
        assert "name" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_missing_protocol_error(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.post(
            url_for("calculatrice.create_indicator"), json={"name": "No Protocol"}
        )
        assert response.status_code == 400
        assert "protocolId" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_unknown_protocol_error(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.post(
            url_for("calculatrice.create_indicator"),
            json={"name": "Unknown protocol", "protocolId": 12345},
        )
        assert response.status_code == 400
        assert "protocolId" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_unknown_field_error(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        payload = {
            "name": "With Code",
            "protocolId": protocol.id_module,
            "code": "some_code = 1",
        }
        response = client.post(url_for("calculatrice.create_indicator"), json=payload)
        assert response.status_code == 400
        assert "code" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_rejects_inactive_reference_table(
        self, client, users, protocol, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        with db.session.begin_nested():
            reftable.active = False
        set_logged_user(client, users["admin"])
        payload = {
            "name": "New Indicator",
            "protocolId": protocol.id_module,
            "referenceTableIds": [reftable.id_reference_table],
        }
        response = client.post(url_for("calculatrice.create_indicator"), json=payload)
        assert response.status_code == 400
        assert "referenceTableIds" in response.json
        assert db.session.execute(select(Indicator).filter_by(name="New Indicator")).first() is None


class TestEditIndicator:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator(self, client, users, protocols):
        set_logged_user(client, users["admin"])
        original_protocol = protocols["mheo_odonate_test"]
        update_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="An indicator",
                id_protocol=original_protocol.id_module,
                description="Description of the indicator",
            )
            db.session.add(indicator)

        payload = {
            "name": "Updated Indicator",
            "description": "An updated description",
            "protocolId": update_protocol.id_module,
        }
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )

        assert response.status_code == 200
        assert response.json["name"] == "Updated Indicator"
        assert response.json["description"] == "An updated description"
        assert response.json["protocolId"] == update_protocol.id_module

        assert indicator.name == "Updated Indicator"
        assert indicator.description == "An updated description"
        assert indicator.id_protocol == update_protocol.id_module

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_without_description(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        payload = {"name": "No Description", "protocolId": protocol_id}
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 200
        assert response.json["description"] == ""
        assert indicator.description == ""

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_edit_indicator_login_required_error(self, client, protocol_with_indicators):
        logout_user()
        indicator = protocol_with_indicators["indicators"][0]
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json={"name": "x", "protocolId": 1},
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_needs_update_permission_error(
        self, client, users, protocol_with_indicators
    ):
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not U.
        set_logged_user(client, users["gestionnaire"])
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        payload = {"name": "Forbidden", "protocolId": protocol_id}
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_not_found_error(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=12345),
            json={"name": "x", "protocolId": 1},
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_missing_name_error(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json={"protocolId": protocol_id},
        )
        assert response.status_code == 400
        assert "name" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_missing_protocol_error(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json={"name": "No Protocol"},
        )
        assert response.status_code == 400
        assert "protocolId" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_unknown_protocol_error(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json={"name": "Unknown protocol", "protocolId": 12345},
        )
        assert response.status_code == 400
        assert "protocolId" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_unknown_field_error(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        payload = {
            "name": "With Code",
            "protocolId": protocol_id,
            "code": "some_code = 1",
        }
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 400
        assert "code" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_rejects_newly_attached_inactive_reference_table(
        self, client, users, protocol_with_indicators, reference_tables
    ):
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        reftable = reference_tables["indices_he"]
        with db.session.begin_nested():
            reftable.active = False
        set_logged_user(client, users["admin"])
        payload = {
            "name": indicator.name,
            "protocolId": protocol_id,
            "referenceTableIds": [reftable.id_reference_table],
        }
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 400
        assert "referenceTableIds" in response.json
        db.session.refresh(indicator)
        assert indicator.reference_tables == []

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_keeps_already_attached_inactive_reference_table(
        self, client, users, protocol_with_indicators, reference_tables
    ):
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        reftable = reference_tables["indices_he"]
        with db.session.begin_nested():
            indicator.reference_tables = [reftable]
            reftable.active = False
        set_logged_user(client, users["admin"])
        payload = {
            "name": "Renamed indicator",
            "protocolId": protocol_id,
            "referenceTableIds": [reftable.id_reference_table],
        }
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 200
        db.session.refresh(indicator)
        assert [rt.id_reference_table for rt in indicator.reference_tables] == [
            reftable.id_reference_table
        ]

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_can_explicitly_remove_inactive_reference_table(
        self, client, users, protocol_with_indicators, reference_tables
    ):
        indicator = protocol_with_indicators["indicators"][0]
        protocol_id = protocol_with_indicators["protocol"].id_module
        reftable = reference_tables["indices_he"]
        with db.session.begin_nested():
            indicator.reference_tables = [reftable]
            reftable.active = False
        set_logged_user(client, users["admin"])
        payload = {
            "name": "Renamed indicator",
            "protocolId": protocol_id,
            "referenceTableIds": [],
        }
        response = client.put(
            url_for("calculatrice.edit_indicator", indicator_id=indicator.id_indicator),
            json=payload,
        )
        assert response.status_code == 200
        db.session.refresh(indicator)
        assert indicator.reference_tables == []


class TestGetIndicatorVisualization:
    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
        "i02_abondance_viz_blocks",
    )
    def test_get_indicator_visualization(self, client, users, monitoring_objects, indicators):
        i02_abondance = indicators["i02_abondance"]
        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=i02_abondance.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 2
        scalar_viz_block = viz_blocks[0]
        assert scalar_viz_block["data"]["figure"] == "6.5"
        barchart_viz_block = viz_blocks[1]
        assert barchart_viz_block["data"]["datasets"][0]["data"] == [
            "8.785714285714285714285714286",
            "7.181818181818181818181818182",
            "5.684782608695652173913043478",
            "6.5",
            "5.4",
        ]

    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
    )
    def test_get_visualization_of_dummy_indicator_to_test_visits_in_context(
        self, client, users, monitoring_objects, protocols
    ):
        flore_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="dummy indicator testing the context",
                id_protocol=flore_protocol.id_module,
                code="""
moy_durée = gn_mean(visites.durée_secondes)
                """,
            )
            db.session.add(indicator)

            scalar_block = VizBlockConfig(
                indicator=indicator,
                title="Moyenne durées visites",
                type=VizBlockType.scalar,
                params={
                    "variable": "moy_durée",
                },
            )
            db.session.add(scalar_block)

        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=indicator.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 1
        scalar_viz_block = viz_blocks[0]
        assert scalar_viz_block["data"]["figure"] == "576"

    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
    )
    def test_get_visualization_of_dummy_indicator_to_test_sites_in_context(
        self, client, users, monitoring_objects, protocols
    ):
        flore_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="dummy indicator testing sites in the context",
                id_protocol=flore_protocol.id_module,
                code="moy_superficies = gn_mean(sites.superficie_mètres_carrés)",
            )
            db.session.add(indicator)

            scalar_block = VizBlockConfig(
                indicator=indicator,
                title="Moyenne superficies",
                type=VizBlockType.scalar,
                params={
                    "variable": "moy_superficies",
                },
            )
            db.session.add(scalar_block)

        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=indicator.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 1
        scalar_viz_block = viz_blocks[0]
        assert scalar_viz_block["data"]["figure"] == "2"

    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
    )
    def test_get_visualization_of_indicator_check_error(
        self, client, users, monitoring_objects, protocols
    ):
        flore_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="dummy indicator testing custom indicator error",
                id_protocol=flore_protocol.id_module,
                code="""
nb_sites=len(sites)
if nb_sites < 20:
    raise IndicatorError(
        f"Cet indicateur nécessite au moins 20 sites. La sélection inclut {nb_sites} sites."
    )
""",
            )
            db.session.add(indicator)

        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=indicator.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        error = response.json["error"]
        assert error["type"] == VisualizationErrorType.public.value
        assert (
            error["message"]
            == "Cet indicateur nécessite au moins 20 sites. La sélection inclut 5 sites."
        )
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 0

    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
    )
    def test_get_visualization_of_indicator_internal_error(
        self, client, users, monitoring_objects, protocols
    ):
        flore_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="dummy indicator testing custom indicator error",
                id_protocol=flore_protocol.id_module,
                code="""
# This comment adds a line to check proper detection of traceback line numbers
result = 1 / 0
""",
            )
            db.session.add(indicator)

        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=indicator.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        error = response.json["error"]
        assert error["type"] == VisualizationErrorType.internal.value
        assert error["message"] == "ZeroDivisionError: division by zero at line 3"
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 0

    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "more_monitoring_objects",
    )
    def test_get_visualization_of_indicator_deep_internal_error(
        self, client, users, monitoring_objects, protocols
    ):
        flore_protocol = protocols["mheo_flore_test"]
        with db.session.begin_nested():
            indicator = Indicator(
                name="dummy indicator testing custom indicator error",
                id_protocol=flore_protocol.id_module,
                code="""
# This comment adds a line to check proper detection of traceback line numbers
def foo():
  return 1 / 0
result = foo()
""",
            )
            db.session.add(indicator)

        set_logged_user(client, users["admin"])
        sites_ids = [site.id_base_site for site in monitoring_objects["sites"]]
        response = client.post(
            url_for(
                "calculatrice.get_indicator_visualization", indicator_id=indicator.id_indicator
            ),
            data={
                "sites_ids": sites_ids,
                "campaigns": [{"start_date": "2023-01-01", "end_date": "2023-12-31"}],
                "viz_type": "campaign",
            },
        )
        assert response.status_code == 200
        error = response.json["error"]
        assert error["type"] == VisualizationErrorType.internal.value
        assert error["message"] == "ZeroDivisionError: division by zero at line 4"
        viz_blocks = response.json["vizBlocks"]
        assert len(viz_blocks) == 0


class TestEditIndicatorCode:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code(self, client, users, protocol_with_indicators):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        new_code = "moyenne = gn_mean(visites.duree_secondes)"
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            json={"code": new_code},
        )
        assert response.status_code == 204

        db.session.refresh(indicator)
        assert indicator.code == new_code

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code_handles_accented_characters(
        self, client, users, protocol_with_indicators
    ):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        new_code = "température_fraîche = True"
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            json={"code": new_code},
        )
        assert response.status_code == 204

        db.session.refresh(indicator)
        assert indicator.code == new_code

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code_handles_single_quotes(
        self, client, users, protocol_with_indicators
    ):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        new_code = "var = 'foo'"
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            json={"code": new_code},
        )
        assert response.status_code == 204

        db.session.refresh(indicator)
        assert indicator.code == new_code

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code_handles_single_quotes(
        self, client, users, protocol_with_indicators
    ):
        set_logged_user(client, users["admin"])
        indicator = protocol_with_indicators["indicators"][0]
        new_code = 'var = "bar"'
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            json={"code": new_code},
        )
        assert response.status_code == 204

        db.session.refresh(indicator)
        assert indicator.code == new_code

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code_overwrites_existing_code(
        self, client, users, protocol_with_indicators
    ):
        indicator = protocol_with_indicators["indicators"][0]
        with db.session.begin_nested():
            indicator.code = "old = 1"
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            json={"code": "new = 2"},
        )
        assert response.status_code == 204

        db.session.refresh(indicator)
        assert indicator.code == "new = 2"

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_edit_indicator_code_login_required_error(self, client, protocol_with_indicators):
        logout_user()
        indicator = protocol_with_indicators["indicators"][0]
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            data="moyenne = 1",
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_indicator_code_needs_update_permission_error(
        self, client, users, protocol_with_indicators
    ):
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not U.
        set_logged_user(client, users["gestionnaire"])
        indicator = protocol_with_indicators["indicators"][0]
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=indicator.id_indicator),
            data="moyenne = 1",
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions", "protocol_with_indicators")
    def test_edit_indicator_code_not_found_error(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for("calculatrice.edit_indicator_code", indicator_id=12345),
            data="moyenne = 1",
        )
        assert response.status_code == 404


class TestGetIndicatorDetails:
    @pytest.mark.usefixtures("calculatrice_permissions")
    @pytest.mark.usefixtures(
        "calculatrice_permissions",
        "i02_abondance_viz_blocks",
    )
    def test_get_indicator_details(self, client, users, indicators):
        i02_abondance = indicators["i02_abondance"]
        set_logged_user(client, users["gestionnaire"])
        response = client.get(
            url_for("calculatrice.get_indicator_details", indicator_id=i02_abondance.id_indicator)
        )
        assert response.status_code == 200
        data = response.json
        assert "visualizationBlockConfigs" in data
        assert len(data["visualizationBlockConfigs"]) == 2
        assert "referenceTables" in data
        assert len(data["referenceTables"]) == 2

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_get_indicator_details_login_required_error(self, client, indicators):
        logout_user()
        i02_abondance = indicators["i02_abondance"]
        response = client.get(
            url_for("calculatrice.get_indicator_details", indicator_id=i02_abondance.id_indicator)
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions", "indicators")
    def test_get_indicator_details_not_found_error(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_indicator_details", indicator_id=12345))
        assert response.status_code == 404


class TestEditIndicatorVizBlocks:
    @staticmethod
    def _create_indicator(protocol, code=""):
        with db.session.begin_nested():
            indicator = Indicator(
                name="TestIndicator",
                id_protocol=protocol.id_module,
                description="This is the test indicator description.",
                code=code,
            )
            db.session.add(indicator)
        return indicator

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        code = "moyenne = gn_mean(visites.duree_secondes)"
        indicator = self._create_indicator(protocol, code)

        response = client.put(
            url_for(
                "calculatrice.update_indicator_viz_blocks", indicator_id=indicator.id_indicator
            ),
            json=[{"title": "foobar", "type": "bar_chart"}],
        )

        assert response.status_code == 204

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks_with_overwriting(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        indicator = self._create_indicator(protocol, code="foo=42")
        with db.session.begin_nested():
            vizblock1 = VizBlockConfig(title="Test old vizblock 1", type=VizBlockType.scalar)
            indicator.viz_block_configs.append(vizblock1)
            vizblock2 = VizBlockConfig(title="Test old vizblock 2", type=VizBlockType.bar_chart)
            indicator.viz_block_configs.append(vizblock2)

        response = client.put(
            url_for(
                "calculatrice.update_indicator_viz_blocks", indicator_id=indicator.id_indicator
            ),
            json=[{"title": "New vizblock", "type": "scalar", "params": {"variable": "bar"}}],
        )

        assert response.status_code == 204
        assert len(indicator.viz_block_configs) == 1
        vizblock = indicator.viz_block_configs[0]
        assert vizblock.title == "New vizblock"
        assert vizblock.type == VizBlockType.scalar
        assert vizblock.params == {"variable": "bar"}

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_edit_vizblocks_login_required_error(self, client):
        logout_user()
        does_not_matter = 12345

        response = client.put(
            url_for("calculatrice.update_indicator_viz_blocks", indicator_id=does_not_matter),
            json=[],
        )

        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks_needs_create_permission_error(self, client, users):
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not U.
        set_logged_user(client, users["gestionnaire"])
        does_not_matter = 12345

        response = client.put(
            url_for("calculatrice.update_indicator_viz_blocks", indicator_id=does_not_matter),
            json=[],
        )

        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks_indicator_not_found_error(self, client, users):
        set_logged_user(client, users["admin"])
        does_not_exist = 12345

        response = client.put(
            url_for("calculatrice.update_indicator_viz_blocks", indicator_id=does_not_exist),
            json=[],
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks_list_expected_error(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        indicator = self._create_indicator(protocol)

        response = client.put(
            url_for(
                "calculatrice.update_indicator_viz_blocks", indicator_id=indicator.id_indicator
            ),
            json={"title": "foobar", "type": "bar_chart"},
        )

        assert response.status_code == 400

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_vizblocks_unknown_type_error(self, client, users, protocol):
        set_logged_user(client, users["admin"])
        indicator = self._create_indicator(protocol)
        unknown_type = "unknown_enum_value"

        response = client.put(
            url_for(
                "calculatrice.update_indicator_viz_blocks", indicator_id=indicator.id_indicator
            ),
            json=[{"title": "foobar", "type": unknown_type}],
        )

        assert response.status_code == 400
        assert "type" in response.json["description"]


class TestGetRerenceTables:
    @pytest.mark.usefixtures("calculatrice_permissions", "reference_tables")
    def test_get_reftables(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_reference_tables"))
        assert response.status_code == 200

        reftables_codes = [rt["code"] for rt in response.json]
        assert len(reftables_codes) == 3
        assert "indices_he" in reftables_codes
        assert "indices_ht" in reftables_codes
        assert "valeurs_abondance" in reftables_codes

        reftable_he = next(rt for rt in response.json if rt["code"] == "indices_he")
        assert (
            reftable_he["description"]
            == "Tableau de référence avec indices de référence par espèce pour HE"
        )

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_empty_reftables_list(self, client, users):
        set_logged_user(client, users["gestionnaire"])
        response = client.get(url_for("calculatrice.get_reference_tables"))
        assert response.status_code == 200
        assert response.json == []

    def test_error_endpoint_requires_login(self, client):
        logout_user()
        response = client.get(url_for("calculatrice.get_reference_tables"))
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_get_protocol_needs_permission_error(self, client, users):
        set_logged_user(client, users["public"])
        response = client.get(url_for("calculatrice.get_reference_tables"))
        assert response.status_code == 403


class TestCreateReferenceTable:
    @staticmethod
    def _get_payload(
        name: Optional[str] = "My ref table",
        description: Optional[str] = "My ref table description",
        code: Optional[str] = "my_table",
        file=None,
        encoding: Optional[str] = "utf-8",
        separator: Optional[str] = ",",
    ):
        if file is None:
            filename = Path(__file__).parent.parent / "./migrations/data/indices_he.csv"
            file = (open(filename, "rb"), "indices_he.csv")
        fields = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if code is not None:
            fields["code"] = code
        if encoding is not None:
            fields["encoding"] = encoding
        if separator is not None:
            fields["separator"] = separator
        return {
            "file": file,
            "fields": json.dumps(fields),
        }

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload()
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 201
        reftable = response.json
        assert "name" in reftable
        assert reftable["name"] == "My ref table"
        assert "description" in reftable
        assert reftable["description"] == "My ref table description"
        assert "code" in reftable
        assert reftable["code"] == "my_table"

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_without_description(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(description=None)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 201
        assert response.json["description"] is None

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_create_reftable_login_required_error(self, client):
        logout_user()
        payload = self._get_payload()
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_needs_create_permission_error(self, client, users):
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not C.
        set_logged_user(client, users["gestionnaire"])
        payload = self._get_payload()
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_indicator_missing_name_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(name=None)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "name" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_duplicate_code_error(self, client, users, reference_tables):
        existing_code = reference_tables["indices_he"].code
        set_logged_user(client, users["admin"])
        payload = self._get_payload(name="Another reftable", code=existing_code)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "code" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    @pytest.mark.parametrize(
        "invalid_code",
        [
            "1_starts_with_digit",
            "_starts_with_underscore",
            "has space",
            "has-dash",
            "has.dot",
            "",
        ],
    )
    def test_create_reftable_invalid_code_format_error(self, client, users, invalid_code):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(code=invalid_code)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "code" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_valid_code_with_digits_and_underscore(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(code="valid_code_2")
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 201

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_normalizes_semicolon_separator(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO(b"cdnom;indice_he\n81610;9\n"), "reftable.csv"), separator=";"
        )
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 201
        created = db.session.execute(select(ReferenceTable).filter_by(code="my_table")).scalar_one()
        assert created.data == "cdnom,indice_he\n81610,9\n"

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_decodes_latin1_encoding(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO("nom,valeur\nélevé,1\n".encode("iso-8859-1")), "reftable.csv"),
            encoding="latin-1",
        )
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 201
        created = db.session.execute(select(ReferenceTable).filter_by(code="my_table")).scalar_one()
        assert created.data == "nom,valeur\nélevé,1\n"

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_unable_to_decode_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO("élevé".encode("iso-8859-1")), "reftable.csv"), encoding="utf-8"
        )
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "file" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_value_too_long_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO(f"cdnom,indice_he\n{'a' * 101},9\n".encode()), "reftable.csv")
        )
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert response.json == {
            "file": [
                "Certaines valeurs sont trop longues. "
                f"La limite est de {REFERENCE_TABLE_MAX_VALUE_LENGTH} caractères."
            ]
        }

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_file_too_large_error(self, client, users):
        set_logged_user(client, users["admin"])
        placeholder = b"81610,9\n"
        times = REFERENCE_TABLE_MAX_FILE_SIZE // len(placeholder)
        oversized_content = b"cdnom,indice_he\n" + placeholder * (times + 1)
        payload = self._get_payload(file=(BytesIO(oversized_content), "reftable.csv"))
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "file" in response.json
        assert "Le fichier est trop volumineux" in response.json["file"][0]

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_missing_encoding_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(encoding=None)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "encoding" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_missing_separator_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(separator=None)
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "separator" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_create_reftable_invalid_separator_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload(file=(BytesIO(b"a,b\n1,2\n"), "reftable.csv"), separator="|")
        response = client.post(
            url_for("calculatrice.create_reference_table"),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "separator" in response.json


class TestEditReferenceTable:
    @staticmethod
    def _get_payload(
        name: Optional[str] = "Updated name",
        description: Optional[str] = "Updated description",
        code: Optional[str] = None,
        file=None,
        encoding: Optional[str] = "utf-8",
        separator: Optional[str] = ",",
    ):
        fields = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if code is not None:
            fields["code"] = code
        if encoding is not None:
            fields["encoding"] = encoding
        if separator is not None:
            fields["separator"] = separator
        payload = {"fields": json.dumps(fields)}
        if file is not None:
            payload["file"] = file
        return payload

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload()
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 200
        assert response.json["name"] == "Updated name"
        assert response.json["description"] == "Updated description"
        assert response.json["code"] == reftable.code

        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.name == "Updated name"
        assert updated.description == "Updated description"
        assert updated.code == reftable.code
        assert updated.data == reftable.data

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_keeps_description_when_not_provided(
        self, client, users, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        original_description = reftable.description
        set_logged_user(client, users["admin"])
        payload = self._get_payload(description=None)
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 200
        assert response.json["description"] == original_description
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.description == original_description

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_with_new_file(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        original_data = reftable.data
        set_logged_user(client, users["admin"])
        filename = Path(__file__).parent.parent / "./migrations/data/indices_ht.csv"
        expected_data = filename.read_text()
        datafile = open(filename, "rb")
        payload = self._get_payload(file=(datafile, "indices_ht.csv"))
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 200
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.name == "Updated name"
        assert updated.data == expected_data
        assert updated.data != original_data

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_ignores_code(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        original_code = reftable.code
        set_logged_user(client, users["admin"])
        payload = self._get_payload(code="not_allowed")
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 400
        assert "code" in response.json
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.code == original_code

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_edit_reftable_login_required_error(self, client, reference_tables):
        reftable = reference_tables["indices_he"]
        logout_user()
        payload = self._get_payload()
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_needs_update_permission_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not U.
        set_logged_user(client, users["gestionnaire"])
        payload = self._get_payload()
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_missing_name_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(name=None)
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "name" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_not_found_error(self, client, users):
        set_logged_user(client, users["admin"])
        payload = self._get_payload()
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=999999),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_normalizes_semicolon_separator(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO(b"cdnom;indice_he\n81610;9\n"), "reftable.csv"), separator=";"
        )
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )

        assert response.status_code == 200
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.data == "cdnom,indice_he\n81610,9\n"

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_wrong_encoding_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(file=(BytesIO("élevé".encode("iso-8859-1")), "reftable.csv"))
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "file" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_value_too_long_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(
            file=(BytesIO(f"cdnom,indice_he\n{'a' * 101},9\n".encode()), "reftable.csv")
        )
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert response.json == {
            "file": [
                "Certaines valeurs sont trop longues. "
                f"La limite est de {REFERENCE_TABLE_MAX_VALUE_LENGTH} caractères."
            ]
        }

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_file_too_large_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        placeholder = b"81610,9\n"
        times = REFERENCE_TABLE_MAX_FILE_SIZE // len(placeholder)
        oversized_content = b"cdnom,indice_he\n" + placeholder * (times + 1)
        payload = self._get_payload(file=(BytesIO(oversized_content), "reftable.csv"))
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "file" in response.json
        assert "Le fichier est trop volumineux" in response.json["file"][0]

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_missing_encoding_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(encoding=None)
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "encoding" in response.json

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reftable_missing_separator_error(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        payload = self._get_payload(separator=None)
        response = client.put(
            url_for("calculatrice.edit_reference_table", reftable_id=reftable.id_reference_table),
            data=payload,
            headers=Headers({"Content-Type": "multipart/form-data"}),
        )
        assert response.status_code == 400
        assert "separator" in response.json


class TestEditReferenceTableActiveStatus:
    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_deactivate_reftable(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        assert reftable.active is True
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": False},
        )
        assert response.status_code == 200
        assert response.json["active"] is False
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.active is False

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_reactivate_reftable(self, client, users, reference_tables):
        reftable = reference_tables["indices_he"]
        with db.session.begin_nested():
            reftable.active = False
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": True},
        )
        assert response.status_code == 200
        assert response.json["active"] is True
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.active is True

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reference_table_active_status_does_not_detach_indicators(
        self, client, users, reference_tables, protocol_with_indicators
    ):
        reftable = reference_tables["indices_he"]
        indicator = protocol_with_indicators["indicators"][0]
        with db.session.begin_nested():
            indicator.reference_tables = [reftable]
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": False},
        )
        assert response.status_code == 200
        db.session.refresh(indicator)
        assert [rt.id_reference_table for rt in indicator.reference_tables] == [
            reftable.id_reference_table
        ]

    @pytest.mark.usefixtures("calculatrice_permissions", "users")
    def test_edit_reference_table_active_status_login_required_error(
        self, client, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        logout_user()
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": False},
        )
        assert response.status_code == 401

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reference_table_active_status_needs_update_permission_error(
        self, client, users, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        # `gestionnaire` only has the R permission on CALC_ADMIN_INDICATOR, not U.
        set_logged_user(client, users["gestionnaire"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": False},
        )
        assert response.status_code == 403

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reference_table_active_status_not_found_error(self, client, users):
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for("calculatrice.edit_reference_table_active_status", reftable_id=999999),
            json={"active": False},
        )
        assert response.status_code == 404

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reference_table_active_status_requires_boolean(
        self, client, users, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={"active": "not-a-boolean"},
        )
        assert response.status_code == 400
        assert "active" in response.json
        updated = db.session.get(ReferenceTable, reftable.id_reference_table)
        assert updated.active is True

    @pytest.mark.usefixtures("calculatrice_permissions")
    def test_edit_reference_table_active_status_missing_field_error(
        self, client, users, reference_tables
    ):
        reftable = reference_tables["indices_he"]
        set_logged_user(client, users["admin"])
        response = client.put(
            url_for(
                "calculatrice.edit_reference_table_active_status",
                reftable_id=reftable.id_reference_table,
            ),
            json={},
        )
        assert response.status_code == 400
        assert "active" in response.json
