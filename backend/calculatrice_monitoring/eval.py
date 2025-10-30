import datetime
import statistics
import sys
from collections import defaultdict
from decimal import Decimal

from geonature.app import create_app
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import (
    TMonitoringObservations,
    TMonitoringSites,
    TMonitoringVisits,
)

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

# TODO:
# - [ok] gérer scope site pour la Moyenne
# - [ok] gérer la conversion entre l'ID d'une valeur (pour l'abondance) et la valeur numérique à utiliser pour les calculs
#   + c'est forcément qqchose qui doit pouvoir être configurable dans le code de l'indicateur !
#   + idéalement il faudrait que la définition soit partageable mais ça va être compliqué car je n'avais pas vu ce besoin arriver
# - gérer plusieurs types de valeurs pour les MonitoringObjects
# - start to look at way to report meaningful errors which happened in indicator's code
# - extraire les variables créées sans les variables du contexte original
# - faire un test de robustesse avec données manquantes (une observation sans abondance)


# architecture :
# - [ok] continuer à implémenter I02 pour voir => tableau de référence
# - aller au bout de la connexion avec l'application avant ?
#   + ajouter un autre groupe de sites et des observations
#   + filtrer observations selon groupe sélectionné
#   + ajouter une autre campagne sur étang de Botte
#   + filtrer observations selon campagne sélectionnée
#   + modéliser les blocs de visualisation
#   + préparer une fixture pour les blocs de visualisation
#   + créer les blocs avec les résultats du calcul et retourner au frontend
# - de vrais tests pytest avec fixtures
#   + réfléchir à la tête des tests et des fixtures
# - factoriser les classes => Obs, Site, Visit, ... ==> Entity
# - récupérer properties dynamiquement avec la config
#   + ne pas prendre les propriétés cachées ?
# - d'autres points d'entrée que 'observations'
# - il faudra un 2ème zone humide pour les tests (sélection des observations de la zone humide cible)


# TODO: function to emulate reference table lookup
def get_he(cd_nom):
    map = {
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
    return map[cd_nom]


def get_he_prop_collection(cd_nom_props):
    he_values = []
    for prop in cd_nom_props.values:
        he_values.append(
            PropertyValue(
                value=get_he(prop.value),
                entity=prop.entity,
            )
        )
    return PropertyCollection(values=he_values, scope=cd_nom_props.scope)


# TODO: given the protocol create object with generic and specific properties
config = get_config("mheo_flore_test")


class Root:
    pass


ROOT = Root()


class Site:
    def __init__(self, site_model_instance):
        self.id_base_site = site_model_instance.id_base_site
        self.base_site_name = site_model_instance.base_site_name
        self.id = self.id_base_site


def get_site(site_id):
    site_model_instance = db.session.scalar(
        db.select(TMonitoringSites).filter(TMonitoringSites.id_base_site == site_id)
    )
    return Site(site_model_instance)


class Visit:
    def __init__(self, visit_model_instance):
        self.id_base_visit = visit_model_instance.id_base_visit
        self.visit_date_min = visit_model_instance.visit_date_min
        self.id_base_site = visit_model_instance.id_base_site
        self.id = self.id_base_visit


def get_visit(visit_id):
    visit_model_instance = db.session.scalar(
        db.select(TMonitoringVisits).filter(TMonitoringVisits.id_base_visit == visit_id)
    )
    return Visit(visit_model_instance)


class Observation:
    def __init__(self, observation_model_instance):
        self.abondance = observation_model_instance.data["abondance"]
        self.visit = get_visit(observation_model_instance.id_base_visit)
        self.site = get_site(self.visit.id_base_site)
        self.cd_nom = observation_model_instance.cd_nom
        self.id = observation_model_instance.id_observation


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
    abondance = create_prop_collection_from_entities(
        instances=observations, scope="observation", property="abondance"
    )
    cd_nom = create_prop_collection_from_entities(
        instances=observations, scope="observation", property="cd_nom"
    )
    coll = MonitoringCollection(scope="observation")  # TODO: miss passing entities here
    coll.abondance = abondance
    coll.cd_nom = cd_nom
    return coll


# comment ajouter une propriété `abondance_perc` à toutes les observations, définie dans l'indicateur ?
# - avec la fonction ci-dessous directement dans le code de l'indicateur
# - ou en utilisant un tableau de référence !
def create_abondance_perc(observations: MonitoringCollection):
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


def fetch_prop_value(prop_collection, entity_id):
    for prop_value in prop_collection.values:
        if prop_value.entity.id == entity_id:
            return prop_value.value
    return None


def Moyenne(
    prop_collection: PropertyCollection, scope: str = "global", weights: PropertyCollection = None
):
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
    median = statistics.median([Decimal(prop_value.value) for prop_value in prop_collection.values])
    values = [
        PropertyValue(
            value=median,
            entity=ROOT,
        )
    ]
    return PropertyCollection(values=values, scope="global")


# ---------- TEST AVEC MOYENNE ABONDANCE TOUTES OBSERVATIONS -------------

code = """
moyenne = Moyenne(observations.abondance)
"""
observations = get_observation_collection()
global_context = dict()
context = dict()
context["Moyenne"] = Moyenne
context["create_abondance_perc"] = create_abondance_perc
context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert len(context["moyenne"].values) == 1
assert context["moyenne"].values[0].value == 1.4102564102564104

# ---------- TEST AVEC MOYENNE ABONDANCE POURCENTAGE TOUTES OBSERVATIONS -------------

code = """
moyenne = Moyenne(create_abondance_perc(observations))
"""
observations = get_observation_collection()
global_context = dict()
context = dict()
context["Moyenne"] = Moyenne
context["create_abondance_perc"] = create_abondance_perc
context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert len(context["moyenne"].values) == 1
assert context["moyenne"].values[0].value == 10.333333333333334

# ---------- TEST AVEC MOYENNE ABONDANCE PAR VISITE -------------

code = """
moyenne = Moyenne(observations.abondance, scope="visit")
labels = [v.entity.visit_date_min for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()


def add_to_ctx(obj):
    global_context[obj.__name__] = obj


for symbol in [
    Moyenne,
    PropertyValue,
    MonitoringCollection,
    PropertyCollection,
]:
    add_to_ctx(symbol)
global_context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert "labels" in context
labels = context["labels"]
assert [datetime.date(2023, 5, 22)] * 5 == labels
assert "values" in context
values = context["values"]
for expected_value in [
    Decimal(1.3333333333333333),
    Decimal(3),
    Decimal(1.3571428571428571),
    Decimal(1),
    Decimal(1.3571428571428571),
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")

# ---------- TEST AVEC CONVERSION ABONDANCE EN POURCENTAGE -------------

code = """
def create_abondance_perc(observations: MonitoringCollection):
    map = {
        "+": 0.5,
        "1": 3,
        "2": 15,
        "3": 37.5,
        "4": 67.5,
        "5": 87.5
    }
    values = []
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
moyenne = Moyenne(create_abondance_perc(observations), scope="visit")
labels = [v.entity.visit_date_min for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()


def add_to_ctx(obj):
    global_context[obj.__name__] = obj


for symbol in [
    Moyenne,
    PropertyValue,
    MonitoringCollection,
    PropertyCollection,
]:
    add_to_ctx(symbol)
global_context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert "labels" in context
labels = context["labels"]
assert [datetime.date(2023, 5, 22)] * 5 == labels
assert "values" in context
values = context["values"]
for expected_value in [
    Decimal('7'),
    Decimal('41.25'),
    Decimal('10.07142857142857142857142857'),
    Decimal('3'),
    Decimal('9.321428571428571428571428571'),
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")

# ---------- TEST AVEC MOYENNE ABONDANCE PAR SITE -------------

code = """
moyenne = Moyenne(observations.abondance, scope="site")
labels = [v.entity.base_site_name for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()


def add_to_ctx(obj):
    global_context[obj.__name__] = obj


for symbol in [
    Moyenne,
    PropertyValue,
    MonitoringCollection,
    PropertyCollection,
]:
    add_to_ctx(symbol)
global_context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert "labels" in context
labels = context["labels"]
for expected_label in [
    "Transect 1 Quadrat 1",
    "Transect 1 Quadrat 2",
    "Transect 1 Quadrat 3",
    "Transect 2 Quadrat 4",
    "Transect 2 Quadrat 5",
]:
    assert expected_label in labels
assert "values" in context
values = context["values"]
for expected_value in [
    Decimal('1.333333333333333333333333333'),
    Decimal('3'),
    Decimal('1.357142857142857142857142857'),
    Decimal('1'),
    Decimal('1.357142857142857142857142857'),
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")

# ---------- TEST AVEC MOYENNE HE PAR SITE -------------

code = """
valeurs_he = get_he_prop_collection(observations.cd_nom)
moyenne = Moyenne(valeurs_he, scope="site")
médiane = Médiane(moyenne)
labels = [v.entity.base_site_name for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()


def add_to_ctx(obj):
    global_context[obj.__name__] = obj


for symbol in [
    Moyenne,
    PropertyValue,
    MonitoringCollection,
    PropertyCollection,
    get_he_prop_collection,
    Médiane,
]:
    add_to_ctx(symbol)
global_context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert "médiane" in context
médiane = context["médiane"]
assert len(médiane.values) == 1
assert médiane.values[0].value == 6.5
assert "labels" in context
labels = context["labels"]
for expected_label in [
    "Transect 1 Quadrat 1",
    "Transect 1 Quadrat 2",
    "Transect 1 Quadrat 3",
    "Transect 2 Quadrat 4",
    "Transect 2 Quadrat 5",
]:
    assert expected_label in labels
assert "values" in context
values = context["values"]
for expected_value in [
    Decimal('7.833333333333333333333333333'),
    Decimal('7.5'),
    Decimal('5.769230769230769230769230769'),
    Decimal('6.5'),
    Decimal('6'),
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")

# ---------- TEST AVEC MOYENNE HE PONDÉRÉE AVEC ABONDANCE PAR SITE -------------

code = """
valeurs_he = get_he_prop_collection(observations.cd_nom)
abondance_perc = create_abondance_perc(observations)
moyenne = Moyenne(valeurs_he, scope="site", weights=abondance_perc)
médiane = Médiane(moyenne)
labels = [v.entity.base_site_name for v in moyenne.values]
values = [v.value for v in moyenne.values]
"""
observations = get_observation_collection()
global_context = dict()
context = dict()


def add_to_ctx(obj):
    global_context[obj.__name__] = obj


for symbol in [
    Moyenne,
    PropertyValue,
    MonitoringCollection,
    PropertyCollection,
    get_he_prop_collection,
    create_abondance_perc,
    Médiane,
]:
    add_to_ctx(symbol)
global_context["observations"] = observations

exec(code, global_context, context)

assert "moyenne" in context
assert "médiane" in context
médiane = context["médiane"]
assert len(médiane.values) == 1


def almostEqual(value, expected):
    return abs(value - expected) < sys.float_info.epsilon


assert médiane.values[0].value == Decimal('6.5')
assert "labels" in context
labels = context["labels"]
for expected_label in [
    "Transect 1 Quadrat 1",
    "Transect 1 Quadrat 2",
    "Transect 1 Quadrat 3",
    "Transect 2 Quadrat 4",
    "Transect 2 Quadrat 5",
]:
    assert expected_label in labels
assert "values" in context
values = context["values"]
for expected_value in [
    Decimal('8.785714285714285714285714286'),
    Decimal('7.181818181818181818181818182'),
    Decimal('5.684782608695652173913043478'),
    Decimal('6.5'),
    Decimal('5.4'),
]:
    for value in values:
        if abs(value - expected_value) < sys.float_info.epsilon:
            break
    else:
        raise AssertionError(f"{expected_value} not found in {values}")
