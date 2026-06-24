import datetime

from gn_module_monitoring.monitoring.models import TMonitoringVisits

from calculatrice_monitoring.eval import (
    Observation,
    Scope,
    Site,
    Visit,
    create_monitoring_collection,
)


class TestObservationCollection:
    def test_context(self, indicators, monitoring_objects):
        # à partir d'observations et d'un protocole test
        protocol = indicators[0].protocol
        observations = [Observation(protocol, obj) for obj in monitoring_objects["observations"]]
        obs_collections = create_monitoring_collection(
            protocol, observations, scope=Scope.OBSERVATION
        )
        # tester que le PropCollection sont bien créées
        abondance = obs_collections.abondance
        assert abondance is not None
        scope = abondance.scope
        assert scope == Scope.OBSERVATION
        prop_values = abondance.values
        assert len(prop_values) == 39
        prop_value = prop_values[0]
        assert prop_value.value == "1"
        assert prop_value.entity.cd_nom == 95463
        recolte = obs_collections.récolte
        assert recolte is not None
        scope = recolte.scope
        assert scope == Scope.OBSERVATION
        assert len(recolte.values) == 39
        recolte_value = recolte.values[0]
        assert recolte_value.value == "1"
        assert recolte_value.entity.cd_nom == 95463

    def test_context_visit(self, indicators, monitoring_objects):
        # à partir d'observations et d'un protocole test
        protocol = indicators[0].protocol
        visits = [Visit(protocol, obj) for obj in monitoring_objects["visits"]]
        visit_collection = create_monitoring_collection(protocol, visits, scope=Scope.VISIT)

        # tester que le PropCollection sont bien créées
        visit_date = visit_collection.visit_date_min
        assert visit_date is not None
        scope = visit_date.scope
        assert scope == Scope.VISIT
        prop_values = visit_date.values
        assert len(prop_values) == 5
        prop_value = prop_values[0]
        assert prop_value.value == datetime.date(2023, 5, 22)

        # Test property 'diffusion_mesure'
        diffusion_mesure = visit_collection.diffusion_mesure
        assert diffusion_mesure is not None
        scope = diffusion_mesure.scope
        assert scope == Scope.VISIT
        prop_values = diffusion_mesure.values
        assert len(prop_values) == 5
        prop_value = prop_values[0]
        assert prop_value.value == "Oui"
        assert prop_value.entity.visit_date_min == datetime.date(2023, 5, 22)

        # Test property 'durée_secondes'
        duree_secondes = visit_collection.durée_secondes
        assert duree_secondes is not None
        scope = duree_secondes.scope
        assert scope == Scope.VISIT
        prop_values = duree_secondes.values
        assert len(prop_values) == 5
        prop_value = prop_values[0]
        assert prop_value.value == 360
        assert prop_value.entity.visit_date_min == datetime.date(2023, 5, 22)

    def test_context_with_sites(self, indicators, monitoring_objects):
        protocol = indicators[0].protocol
        sites = [Site(protocol, obj) for obj in monitoring_objects["sites"]]
        site_collection = create_monitoring_collection(protocol, sites, scope=Scope.SITE)

        site_superficies = site_collection.superficie_mètres_carrés
        assert site_superficies is not None
        scope = site_superficies.scope
        assert scope == Scope.SITE
        prop_values = site_superficies.values
        assert len(prop_values) == 5
        prop_value = prop_values[0]
        assert prop_value.value == 1

    def test_can_create_entity_from_monitoring_object_with_missing_data(self, flore_protocol):
        # Create a monitoring visit without values for specific properties
        monitoring_visit = TMonitoringVisits(visit_date_min=datetime.datetime(2025, 1, 1))

        visit = Visit(flore_protocol, monitoring_visit)

        assert visit.visit_date_min == datetime.datetime(2025, 1, 1)
        assert hasattr(visit, "durée_secondes")
        assert visit.durée_secondes is None
        assert hasattr(visit, "diffusion_mesure")
        assert visit.diffusion_mesure is None
