from geonature.app import create_app
from gn_module_monitoring.config.repositories import get_config
from gn_module_monitoring.monitoring.models import TMonitoringObservations

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


global_context = dict()
context = dict()

# TODO: given the protocol create object with generic and specific properties
config = get_config("mheo_flore_test")


class Observation:
    def __init__(self, observation_model_instance):
        self.abondance = observation_model_instance.data["abondance"]


class PropertyCollection:
    def __init__(self, instances, property):
        self._instances = instances
        self._property = property

    @property
    def values(self):
        return [getattr(instance, self._property) for instance in self._instances]


class MonitoringCollection:
    def __init__(self, scope):
        self.scope = scope


def get_observations():
    query = db.select(TMonitoringObservations)
    tmos = db.session.scalars(query).all()
    observations = []
    for tmo in tmos:
        observations.append(Observation(tmo))
    return observations


def get_observation_collection():
    observations = get_observations()
    abondance = PropertyCollection(observations, "abondance")
    coll = MonitoringCollection(scope="observation")
    coll.abondance = abondance
    return coll


# TODO: ajouter un scope="site" !
def Moyenne(property):
    sum = 0
    for value in property.values:
        sum += int(value)
    return sum / len(property.values)


observations = get_observation_collection()
context["Moyenne"] = Moyenne
context["observations"] = observations

code = """
moyenne = Moyenne(observations.abondance)
"""

exec(code, global_context, context)

assert "moyenne" in context
assert context["moyenne"] == 1.4102564102564104
