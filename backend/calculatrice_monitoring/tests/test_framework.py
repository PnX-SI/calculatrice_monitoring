from datetime import date

from calculatrice_monitoring.eval import (
    Entity,
    Group,
    Scope,
    Site,
    create_monitoring_collection_impl,
)

from ..eval import Visit


def _get_test_entities():
    group = Group.from_attr(id_sites_group=1, sites_group_name="group 1")
    site = Site.from_attr(id_base_site=1, base_site_name="site 1", group=group)
    visit1 = Visit.from_attr(
        id_base_visit=1,
        visit_date_min=date(2023, 5, 1),
        specifics={
            "duration_1": 15,
            "duration_2": 45,
        },
        site=site,
    )
    visit2 = Visit.from_attr(
        id_base_visit=2,
        visit_date_min=date(2023, 5, 1),
        specifics={
            "duration_1": 20,
            "duration_2": 45,
        },
        site=site,
    )
    visit3 = Visit.from_attr(
        id_base_visit=3,
        visit_date_min=date(2023, 5, 1),
        specifics={
            "duration_1": 10,
            "duration_2": 35,
        },
        site=site,
    )
    return {"group": group, "site": site, "visits": [visit1, visit2, visit3]}


class TestCreateMonitoringCollection:
    def test_create_monitoring_collection(self):
        visit_specific_props = {
            "duration_1": {},
            "duration_2": {},
        }
        entities = _get_test_entities()
        visits = entities["visits"]

        collection_visites = create_monitoring_collection_impl(
            visit_specific_props, entities=visits, scope=Scope.VISIT
        )

        assert collection_visites.scope is Scope.VISIT
        assert getattr(collection_visites, "duration_1", None) is not None
        collection_durations_1 = collection_visites.duration_1
        assert getattr(collection_visites, "duration_2", None) is not None
        assert collection_durations_1.scope is Scope.VISIT
        assert len(collection_durations_1.values) == 3
        assert [v.value for v in collection_durations_1.values] == [15, 20, 10]
        first_value_entity = collection_durations_1.values[0].entity
        assert first_value_entity is visits[0]

    def test_it_handles_missing_values(self):
        visit_specific_props = {
            "duration_1": {},
            "duration_2": {},
        }
        entities = _get_test_entities()
        visits = entities["visits"]
        delattr(visits[1], "duration_1")
        delattr(visits[2], "duration_2")

        collection_visites = create_monitoring_collection_impl(
            visit_specific_props, entities=visits, scope=Scope.VISIT
        )

        assert getattr(collection_visites, "duration_1", None) is not None
        collection_durations_1 = collection_visites.duration_1
        assert len(collection_durations_1.values) == 3
        assert [v.value for v in collection_durations_1.values] == [15, None, 10]

        assert getattr(collection_visites, "duration_2", None) is not None
        collection_durations_2 = collection_visites.duration_2
        assert len(collection_durations_2.values) == 3
        assert [v.value for v in collection_durations_2.values] == [45, 45, None]
