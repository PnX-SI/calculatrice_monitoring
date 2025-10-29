from collections import defaultdict

from geonature.app import create_app
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import TMonitoringObservations, TMonitoringSites, TMonitoringVisits

app = create_app()

from geonature.utils.env import db

ctx = app.app_context()
ctx.push()


# given:
# - sites IDs
# - indicator ID
# - campaigns
# - visualization type
# - tableau de référence
# - code indicateur

# étapes
# - préparer le contexte
# - exécuter un code python
# - retourner les infos ?

# indicateur :
# - dummy indicateur (nb d'observations)
# - I02 sans abondance
# - I02 (avec abondance si temps)


# TODO: function to emulate reference table lookup
def getHE(cd_nom):
    pass


# TODO: given the protocol create object with generic and specific properties
config = get_config("mheo_flore_test")


# class Site:
#     def __init__(self, site_model_instance):
#         self.id_base_site = site_model_instance.id_base_site
#         self.base_site_name = site_model_instance.base_site_name
#
#
# def get_site(site_id):
#     site_model_instance = db.session.scalar(db.select(TMonitoringSites).filter(TMonitoringSites.id_base_site == site_id))
#     return Site(site_model_instance)


class Visit:
    def __init__(self, visit_model_instance):
        self.id_base_visit = visit_model_instance.id_base_visit
        self.visit_date_min = visit_model_instance.visit_date_min


def get_visit(visit_id):
    visit_model_instance = db.session.scalar(db.select(TMonitoringVisits).filter(TMonitoringVisits.id_base_visit == visit_id))
    return Visit(visit_model_instance)


class Observation:
    def __init__(self, observation_model_instance):
        self.abondance = observation_model_instance.data["abondance"]
        self.visit = get_visit(observation_model_instance.id_base_visit)


class PropertyCollection:

    def __init__(self, values, scope):
        self.values = values
        self.scope = scope


class PropertyValue:

    def __init__(self, value, entity):
        self.value = value
        self.entity = entity


class MonitoringCollection:
    def __init__(self, scope):
        self.scope = scope


def create_prop_collection_from_entities(instances, scope, property):
    values = []
    for instance in instances:
        values.append(
            PropertyValue(
                value=getattr(instance, property),
                entity=instance,
            )
        )
    return PropertyCollection(values=values, scope=scope)


def get_observations():
    query = db.select(TMonitoringObservations)
    tmos = db.session.scalars(query).all()
    observations = []
    for tmo in tmos:
        observations.append(Observation(tmo))
    return observations


def get_observation_collection():
    observations = get_observations()
    abondance = create_prop_collection_from_entities(instances=observations, scope="observation", property="abondance")
    coll = MonitoringCollection(scope="observation")  # TODO: miss passing entities here
    coll.abondance = abondance
    return coll


# TODO: ajouter un scope="site" !
def Moyenne(prop_collection, scope_visit=False):
    if not scope_visit:
        sum = 0
        for prop_value in prop_collection.values:
            sum += int(prop_value.value)
        moyenne = sum / len(prop_collection.values)
        return PropertyCollection(
            values=[
                PropertyValue(value=moyenne, entity="globale")
            ],
            scope="global"
        )
    else:
        # init sum_dict with site id as key
        sum = defaultdict(lambda: 0)
        # init length_dict with site id as key
        length = defaultdict(lambda: 0)
        visits = {}
        # foreach propvalue:
        for prop_value in prop_collection.values:
            visit = prop_value.entity.visit
            visit_id = visit.id_base_visit # TODO : link an observation's site
            visits[visit_id] = visit
            sum[visit_id] += int(prop_value.value)
            length[visit_id] += 1
        return PropertyCollection(
            values=[
                PropertyValue(
                    value=sum[visit_id] / length[visit_id],
                    entity=visit,
                ) for visit_id, visit in visits.items()
            ],
            scope="visit"
        )


observations_collection = get_observation_collection()


result = Moyenne(
    observations_collection.abondance, scope_visit=True
)


code = """
moyenne = Moyenne(observations.abondance)
"""
observations = get_observation_collection()
global_context = dict()
context = dict()
context["Moyenne"] = Moyenne
context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert len(context["moyenne"].values) == 1
assert context["moyenne"].values[0].value == 1.4102564102564104

# TODO:
# - Moyenne prend en compte le scope
# - valeur moyenne est une PropertyCollection
# - les PropertyValues ont les attributs value et site

code = """
moyenne = Moyenne(observations.abondance, scope_visit=True)
labels = [v.entity.visit_date_min for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()
context["Moyenne"] = Moyenne
context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
# moyenne is a collection
# attrs :
# - value
# - site ID

assert "labels" in context
labels = context["labels"]
# for expected_label in [
#     "Transect 1 Quadrat 1",
#     "Transect 1 Quadrat 2",
#     "Transect 1 Quadrat 3",
#     "Transect 2 Quadrat 4",
#     "Transect 2 Quadrat 5",
# ]:
#     assert expected_label in labels
import datetime
assert [datetime.date(2023, 5, 22)] * 5 == labels
assert "values" in context
values = context["values"]
# from
# select tbs.base_site_name, avg((data->>'abondance')::int)
# from
#     gn_monitoring.t_observation_complements obs
#     join gn_monitoring.t_observations t on obs.id_observation = t.id_observation
#     join gn_monitoring.t_base_visits tbv on t.id_base_visit = tbv.id_base_visit
#     join gn_monitoring.t_base_sites tbs on tbv.id_base_site = tbs.id_base_site
# group by tbs.base_site_name;
import sys
for expected_value in [
    1.3333333333333333,
    3,
    1.3571428571428571,
    1,
    1.3571428571428571,
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")
