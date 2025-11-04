# ruff: noqa: N802  # (N802=Function name should be lowercase)
# ruff: noqa: PLC2401  # (PLC2401=Function name contains a non-ASCII character)

import statistics
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import (
    TMonitoringObservations,
    TMonitoringSites,
    TMonitoringVisits,
)

from calculatrice_monitoring.models import Indicator


class Entity:
    pass


class Root(Entity):
    pass


# ROOT is a placeholder value for the entity of PropertyValue at the "global" scope.
ROOT = Root()


class Site(Entity):
    id: Any
    id_base_site: int
    base_site_name: str

    def __init__(self, site_model_instance):
        self.id_base_site = site_model_instance.id_base_site
        self.base_site_name = site_model_instance.base_site_name
        self.id = self.id_base_site


def get_site(site_id) -> Site:
    site_model_instance = db.session.scalar(
        db.select(TMonitoringSites).filter(TMonitoringSites.id_base_site == site_id)
    )
    return Site(site_model_instance)


class Visit(Entity):
    id: Any
    id_base_visit: int
    id_base_site: int
    visit_date_min: date

    def __init__(self, visit_model_instance):
        self.id_base_visit = visit_model_instance.id_base_visit
        self.visit_date_min = visit_model_instance.visit_date_min
        self.id_base_site = visit_model_instance.id_base_site
        self.id = self.id_base_visit


def get_visit(visit_id) -> Visit:
    visit_model_instance = db.session.scalar(
        db.select(TMonitoringVisits).filter(TMonitoringVisits.id_base_visit == visit_id)
    )
    return Visit(visit_model_instance)


class Observation(Entity):
    id: Any
    visit: Entity
    site: Entity
    abondance: str
    cd_nom: int

    def __init__(self, observation_model_instance):
        self.id = observation_model_instance.id_observation
        self.visit = get_visit(observation_model_instance.id_base_visit)
        self.site = get_site(self.visit.id_base_site)
        self.abondance = observation_model_instance.data["abondance"]
        self.cd_nom = observation_model_instance.cd_nom


class PropertyValue:
    value: Any
    entity: Entity

    def __init__(self, value, entity):
        self.value = value
        self.entity = entity


class PropertyCollection:
    values: list[PropertyValue]
    scope: str

    def __init__(self, values, scope):
        self.values = values
        self.scope = scope


class MonitoringCollection:
    """MonitoringCollection instances are the entry points to data for indicator codes. The
    following MonitoringCollections will be available:

    - observations
    - visits (not implemented yet)
    - sites (not implemented yet)
    - (groups)

    A MonitoringCollection instance bears a scope and the corresponding PropertyCollections. For
    instance 'abondance' and 'cd_nom' for the scope "observations".
    """

    scope: str

    def __init__(self, scope):
        self.scope = scope
        # property collections are added in create function.


def create_observation_collection(
    observations: list[TMonitoringObservations],
) -> MonitoringCollection:
    """Given a list of observation model instances it returns the corresponding
    MonitoringCollection object.

    For now the MonitoringCollection observations exposes the following PropertyCollection:

    - abondance
    - cd_nom

    This is temporary as PropertyCollections creation should be dynamic, depending on generic and
    protocol-specific properties of monitoring objects.
    """

    def create_prop_collection_from_entities(instances, scope, propname):
        values = []
        for instance in instances:
            values.append(
                PropertyValue(
                    value=getattr(instance, propname),
                    entity=instance,
                )
            )
        return PropertyCollection(values=values, scope=scope)

    observation_entities = []
    for obs in observations:
        observation_entities.append(Observation(obs))

    abondance = create_prop_collection_from_entities(
        instances=observation_entities, scope="observation", propname="abondance"
    )
    cd_nom = create_prop_collection_from_entities(
        instances=observation_entities, scope="observation", propname="cd_nom"
    )

    coll = MonitoringCollection(scope="observation")
    coll.abondance = abondance
    coll.cd_nom = cd_nom
    return coll


# --- UTILITY FUNCTIONS INJECTED IN EVAL CONTEXT ---


def get_he_prop_collection(cd_nom_props: PropertyCollection) -> PropertyCollection:
    """Given a PropertyCollection of cd_nom numbers it returns a new PropertyCollection
    of the corresponding HE values.

    Temporary dev function to be replaced with the Reference Table system.
    """
    map_he = {
        81610: 9,
        89200: 5,
        92501: 5,
        95463: 6,
        96271: 6,
        98910: 7,
        99373: 5,
        100310: 6,
        100387: 9,
        102900: 5,
        104173: 7,
        105431: 10,
        105966: 4,
        106581: 5,
        106918: 7,
        107038: 8,
        107117: 7,
        112741: None,
        112975: 7,
        113260: 8,
        115156: 5,
        116759: 6,
        119097: 5,
        119585: 7,
        119915: 8,
        119948: 6,
        119977: 5,
        191232: None,
    }
    he_values = []
    for prop in cd_nom_props.values:
        he_values.append(
            PropertyValue(
                value=map_he[prop.value],
                entity=prop.entity,
            )
        )
    return PropertyCollection(values=he_values, scope=cd_nom_props.scope)


def create_abondance_perc(observations: MonitoringCollection) -> PropertyCollection:
    """Given an observations MonitoringCollection it returns a PropertyCollection with
    percentage values for the abondance property.

    This is a temporary dev function which will be replaced with the Reference Table system or
    a generic transformation function (like "TransformPropertyWithMap")."""
    map = {"+": 0.5, "1": 3, "2": 15, "3": 37.5, "4": 67.5, "5": 87.5}
    values: list[PropertyValue] = []
    for abondance in observations.abondance.values:  # PropertyCollection
        values.append(
            PropertyValue(
                value=map[abondance.value],
                entity=abondance.entity,
            )
        )
    return PropertyCollection(
        values=values,
        scope="observation",
    )


def fetch_prop_value(prop_collection: PropertyCollection, entity_id: Any) -> Any:
    """Look into the PropertyCollection for the PropertyValue corresponding to the entity ID.

    :return: the value of the PropertyValue if found else None
    """
    for prop_value in prop_collection.values:
        if prop_value.entity.id == entity_id:
            return prop_value.value
    return None


def Moyenne(  # noqa: N802  # (N802 Function name `Moyenne` should be lowercase)
    prop_collection: PropertyCollection, scope: str = "global", weights: PropertyCollection = None
) -> PropertyCollection:
    """Returns a property collection with mean values of the given property at the given scope.

    If a property collection is provided for the weights the function returns the weighted mean
    values. If the input property has values without their corresponding weight those input values
    are silently discarded.
    """
    if scope == "global":
        sums = 0
        for prop_value in prop_collection.values:
            sums += int(prop_value.value)
        moyenne = sums / len(prop_collection.values)
        return PropertyCollection(
            values=[PropertyValue(value=moyenne, entity=ROOT)], scope="global"
        )
    else:
        sums = defaultdict(lambda: Decimal(0))
        weights_sums = defaultdict(lambda: Decimal(0))
        scope_entities = {}
        for prop_value in prop_collection.values:
            if prop_value.value is None:
                # FIXME: missing value => we should fail properly here
                continue  # for now we just skip it
            scope_entity = getattr(prop_value.entity, scope)
            scope_entities[scope_entity.id] = scope_entity
            if weights:
                weight = fetch_prop_value(weights, prop_value.entity.id)
                if weight is None:
                    continue
                dweight = Decimal(weight) / Decimal(100)
                sums[scope_entity.id] += Decimal(prop_value.value) * dweight
                weights_sums[scope_entity.id] += dweight
            else:
                sums[scope_entity.id] += Decimal(prop_value.value)
                weights_sums[scope_entity.id] += Decimal(1)
        return PropertyCollection(
            values=[
                PropertyValue(
                    value=sums[scope_entity_id] / weights_sums[scope_entity_id],
                    entity=scope_entity,
                )
                for scope_entity_id, scope_entity in scope_entities.items()
            ],
            scope=scope,
        )


def Médiane(prop_collection: PropertyCollection) -> PropertyCollection:
    """Returns the median value for the given property collection (for now the only implemented
    scope is "global")."""
    median = statistics.median([Decimal(prop_value.value) for prop_value in prop_collection.values])
    values = [
        PropertyValue(
            value=median,
            entity=ROOT,
        )
    ]
    return PropertyCollection(values=values, scope="global")


# --- VISUALIZE FUNCTION AND SUB-FUNCTIONS ---


def create_monitoring_collections(
    observations: list[TMonitoringObservations],
) -> dict[str, MonitoringCollection]:
    return {"observations": create_observation_collection(observations)}


def create_context(collections: dict[str, MonitoringCollection]) -> dict:
    context = {}
    context["Moyenne"] = Moyenne
    context["create_abondance_perc"] = create_abondance_perc
    context["observations"] = collections["observations"]
    context["get_he_prop_collection"] = get_he_prop_collection
    context["Médiane"] = Médiane
    return context


def evaluate(code, context):
    global_context = context
    local_context = {}
    exec(code, global_context, local_context)
    return local_context


def build_viz_blocks(variables):
    viz_config = [
        {
            "type": "scalaire",
            "variable": "médiane",
            "title": "Médiane HE",
            "info": """???""",
            "description": """???""",
        },
        {
            "type": "barChart",
            "variable": "moyenne",
            "title": "Moyenne HE (pondérée par abondance)",
            "info": """???""",
            "description": """???""",
        },
    ]
    viz_blocks = []
    for viz_conf_item in viz_config:
        vizblock_type = viz_conf_item["type"]
        data = None
        if vizblock_type == "scalaire":
            varname = viz_conf_item["variable"]
            data = {"figure": variables[varname].values[0].value}
        elif vizblock_type == "barChart":
            varname = viz_conf_item["variable"]
            prop_values = variables[varname].values
            values = [prop.value for prop in prop_values]
            data = {
                "labels": [prop.entity.base_site_name for prop in prop_values],
                "datasets": [{"data": values, "label": "Moyenne HE par quadrat"}],
            }
        else:
            raise Exception(f"not implemented viz block type {vizblock_type}")
        viz_blocks.append(
            {
                "type": viz_conf_item["type"],
                "title": viz_conf_item["title"],
                "info": viz_conf_item["info"],
                "description": viz_conf_item["description"],
                "data": data,
            }
        )
    return viz_blocks


def visualize(
    indicator_id,
    sites_ids,
    campaigns,
    viz_type,  # noqa: ARG001
):
    campaign = campaigns[0]
    indicator = db.session.scalar(
        db.select(Indicator).filter(Indicator.id_indicator == indicator_id)
    )
    code = indicator.code
    visits_query = (
        db.select(TMonitoringVisits)
        .filter(TMonitoringVisits.id_base_site.in_(sites_ids))
        .filter(TMonitoringVisits.visit_date_min >= campaign["start_date"])
        .filter(TMonitoringVisits.visit_date_min <= campaign["end_date"])
    )
    visits = db.session.scalars(visits_query).unique().all()

    observations_query = db.select(TMonitoringObservations).filter(
        TMonitoringObservations.id_base_visit.in_([visit.id_base_visit for visit in visits])
    )
    observations = db.session.scalars(observations_query).all()

    collections = create_monitoring_collections(observations)
    context = create_context(collections)
    variables = evaluate(code, context)
    return build_viz_blocks(variables)
