import csv
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from calculatrice_monitoring.models import (
    Indicator,
    ReferenceTable,
    VizBlockConfig,
    VizBlockScope,
    VizBlockType,
)
from geoalchemy2.shape import from_shape
from geonature.core.gn_commons.models import TModules
from geonature.core.gn_meta.models import TAcquisitionFramework, TDatasets
from geonature.core.gn_monitoring.models import BibTypeSite
from geonature.core.gn_permissions.models import PermAction, Permission, PermObject
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import (
    TMonitoringModules,
    TMonitoringObservations,
    TMonitoringSites,
    TMonitoringSitesGroups,
    TMonitoringVisits,
)
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures
from pypnusershub.db.models import Organisme, User
from shapely import Point
from sqlalchemy import select


def get_test_protocols():
    # Protocols are installed in test database beforehand (see the documentation)
    protocols = db.session.scalars(select(TMonitoringModules)).all()
    result = {}
    for module_code in [
        "mheo_amphibiens_test",
        "mheo_flore_test",
        "mheo_odonate_test",
        "mheo_pedologie_test",
        "mheo_piezometrie_test",
    ]:
        found_protocols = list(
            filter(lambda protocol: protocol.module_code == module_code, protocols)
        )
        if len(found_protocols) != 1:
            raise Exception(
                f"{module_code} protocol should be installed before runninng this fixture"
            )
        result[module_code] = found_protocols[0]
    return result


def get_quadrat_flore_site_type():
    site_quadrat_flore_type = db.session.scalar(
        select(BibTypeSite)
        .join(TNomenclatures)
        .join(BibNomenclaturesTypes)
        .where(BibNomenclaturesTypes.mnemonique == "TYPE_SITE")
        .where(TNomenclatures.cd_nomenclature == "MHEO_QUADRAT_FLORE_TEST")
    )

    if not site_quadrat_flore_type:
        raise Exception(
            "MhéO test protocols should be installed before running this sample "
            + "installation script (see the doc)"
        )

    return site_quadrat_flore_type


def install_test_users():
    def create_user(username, organisme=None):
        with db.session.begin_nested():
            user = User(groupe=False, active=True, identifiant=username, password=username)
            db.session.add(user)
            user.organisme = organisme
        return user

    users = {}
    organisme = Organisme(nom_organisme="organisme test")
    db.session.add(organisme)
    users_to_create = [
        "public",
        "gestionnaire",
    ]
    for username in users_to_create:
        users[username] = create_user(username, organisme)
    # user 'admin' is already created by default migrations
    users["admin"] = db.session.scalar(select(User).where(User.identifiant == "admin"))
    return users


def install_test_permissions(protocols, users):
    def add_permission(role, module_code, code_action, code_object, scope):
        perm_object = db.session.execute(
            select(PermObject).filter_by(code_object=code_object)
        ).scalar_one()
        perm_action = db.session.execute(
            select(PermAction).filter_by(code_action=code_action)
        ).scalar_one()
        module = db.session.execute(
            select(TModules).filter_by(module_code=module_code)
        ).scalar_one()
        db.session.add(
            Permission(
                role=role,
                action=perm_action,
                module=module,
                object=perm_object,
                scope_value=scope,
            )
        )

    with db.session.begin_nested():
        add_permission(users["gestionnaire"], "CALCULATRICE", "R", "ALL", scope=2)
        add_permission(users["gestionnaire"], "CALCULATRICE", "E", "ALL", scope=2)
        add_permission(users["admin"], "CALCULATRICE", "R", "ALL", scope=None)
        add_permission(users["admin"], "CALCULATRICE", "E", "ALL", scope=None)
        add_permission(users["admin"], "CALCULATRICE", "C", "CALC_ADMIN_INDICATOR", scope=None)
        add_permission(users["admin"], "CALCULATRICE", "R", "CALC_ADMIN_INDICATOR", scope=None)
        add_permission(users["admin"], "CALCULATRICE", "U", "CALC_ADMIN_INDICATOR", scope=None)
        add_permission(users["admin"], "CALCULATRICE", "D", "CALC_ADMIN_INDICATOR", scope=None)
        for gestionnaire_protocol in [
            "mheo_amphibiens_test",
            "mheo_flore_test",
            "mheo_odonate_test",
        ]:
            add_permission(
                users["gestionnaire"], gestionnaire_protocol, "R", "MONITORINGS_MODULES", scope=2
            )
            add_permission(
                users["gestionnaire"], gestionnaire_protocol, "R", "MONITORINGS_GRP_SITES", scope=2
            )
            add_permission(
                users["gestionnaire"], gestionnaire_protocol, "R", "MONITORINGS_SITES", scope=2
            )
        for admin_protocol in protocols.values():
            add_permission(
                users["admin"], admin_protocol.module_code, "R", "MONITORINGS_MODULES", scope=None
            )
            add_permission(
                users["admin"], admin_protocol.module_code, "R", "MONITORINGS_GRP_SITES", scope=None
            )
            add_permission(
                users["admin"], admin_protocol.module_code, "R", "MONITORINGS_SITES", scope=None
            )


def import_data_from_csv(csv_filename):
    """Reads the CSV data file and returns a list of site data."""
    filename = os.path.join(Path(__file__).parent, f"./{csv_filename}")
    datafile = open(filename, newline="")
    data = csv.DictReader(datafile, delimiter=";")

    def get_group(row):
        return {
            "name": row["group_name"],
            "sites": {},
        }

    def get_site(row, group):
        return {
            "name": row["site_name"],
            "longitude": row["site_long"],
            "latitude": row["site_lat"],
            "superficie_mètres_carrés": int(row["superficie_mètres_carrés"]),
            "visits": {},
            "group": group,
        }

    def get_visit(row, site):
        return {
            "date": datetime.strptime(row["date"], "%d/%m/%Y").date(),
            "observations": [],
            "site": site,
            "diffusion_mesure": row["diffusion_mesure"],
            "durée_secondes": int(row["durée_secondes"]),
        }

    def get_observation(row, visit):
        return {
            "cd_nom": int(row["cd_nom"]),
            "abondance": row["abondance"],
            "récolte": row["récolte"],
            "visit": visit,
        }

    groups = {}
    for row in data:
        group_name = row["group_name"]
        if group_name not in groups:
            groups[group_name] = get_group(row)
        group = groups[group_name]
        site_name = row["site_name"]
        if site_name not in group["sites"]:
            group["sites"][site_name] = get_site(row, group)
        site = group["sites"][site_name]
        visit_date = row["date"]
        if visit_date not in site["visits"]:
            site["visits"][visit_date] = get_visit(row, site)
        visit = site["visits"][visit_date]
        visit["observations"].append(get_observation(row, visit))

    # Convert groups, sites and visits dicts to lists
    objects_data = defaultdict(list)
    objects_data["groups"] = list(groups.values())

    groups_data = objects_data["groups"]
    for group in groups_data:
        group["sites"] = list(group["sites"].values())
        objects_data["sites"].extend(group["sites"])
        for site in group["sites"]:
            site["visits"] = list(site["visits"].values())
            objects_data["visits"].extend(site["visits"])
            for visit in site["visits"]:
                objects_data["observations"].extend(visit["observations"])

    return objects_data


def install_metadata():
    with db.session.begin_nested():
        af = TAcquisitionFramework(
            acquisition_framework_name="Données d'observation des protocoles MhéO",
            acquisition_framework_desc="Données d'observation des protocoles MhéO",
            acquisition_framework_start_date=date(2025, 9, 30),
        )
        db.session.add(af)

    with db.session.begin_nested():
        ds = TDatasets(
            acquisition_framework=af,
            dataset_name="Jeu de données MhéO Flore",
            dataset_shortname="Jeu de données MhéO Flore",
            dataset_desc="Description du jeu de données MhéO Flore",
            marine_domain=False,
            terrestrial_domain=True,
        )
        db.session.add(ds)

    return {
        "acquisition_framework": af,
        "dataset": ds,
    }


def configure_mheo_flore_test_protocol(flore_protocol, dataset, flore_site_type):
    with db.session.begin_nested():
        flore_protocol.types_site = [flore_site_type]
        flore_protocol.datasets = [dataset]
        flore_protocol.taxonomy_display_field_name = "nom_vern,lb_nom"
        db.session.add(flore_protocol)

    return flore_protocol


def install_test_monitoring_objects_from_csv(csv_filename, flore_protocol, flore_site_type, users):
    objects_data = import_data_from_csv(csv_filename)

    with db.session.begin_nested():
        existing_groupnames = db.session.scalars(
            db.select(TMonitoringSitesGroups.sites_group_name)
        ).all()
        for group_data in objects_data["groups"]:
            if group_data["name"] not in existing_groupnames:
                group = TMonitoringSitesGroups(
                    sites_group_name=group_data["name"],
                    sites_group_code=group_data["name"].replace(" ", "-").lower(),
                )
                group.modules = [flore_protocol]
                db.session.add(group)
            else:
                group = db.session.scalar(
                    db.select(TMonitoringSitesGroups).filter(
                        TMonitoringSitesGroups.sites_group_name == group_data["name"]
                    )
                )
            group_data["model"] = group

    with db.session.begin_nested():
        existing_sitenames = db.session.scalars(db.select(TMonitoringSites.base_site_name)).all()
        for site_data in objects_data["sites"]:
            if site_data["name"] not in existing_sitenames:
                geom_4326 = from_shape(
                    Point(site_data["longitude"], site_data["latitude"]), srid=4326
                )
                site = TMonitoringSites(
                    base_site_name=site_data["name"],
                    base_site_code=site_data["name"].replace(" ", "-").lower(),
                    geom=geom_4326,
                    types_site=[flore_site_type],
                    data={
                        "superficie_mètres_carrés": site_data["superficie_mètres_carrés"],
                    },
                )
                db.session.add(site)
            else:
                site = db.session.scalar(
                    db.select(TMonitoringSites)
                    .filter(
                        TMonitoringSites.id_sites_group
                        == site_data["group"]["model"].id_sites_group
                    )
                    .filter(TMonitoringSites.base_site_name == site_data["name"])
                )
            site_data["model"] = site

    with db.session.begin_nested():
        for group_data in objects_data["groups"]:
            group = group_data["model"]
            sites = [site_data["model"] for site_data in group_data["sites"]]
            group.sites = sites
            db.session.add(group)

    with db.session.begin_nested():
        for visit_data in objects_data["visits"]:
            existing_visit_dates = db.session.scalars(
                db.select(TMonitoringVisits.visit_date_min).filter(
                    TMonitoringVisits.id_base_site == visit_data["site"]["model"].id_base_site
                )
            ).all()
            if visit_data["date"] not in existing_visit_dates:
                site = visit_data["site"]["model"]
                visit = TMonitoringVisits(
                    id_base_site=site.id_base_site,
                    dataset=flore_protocol.datasets[0],
                    module=flore_protocol,
                    visit_date_min=visit_data["date"],
                    data={
                        "diffusion_mesure": visit_data["diffusion_mesure"],
                        "durée_secondes": visit_data["durée_secondes"],
                    },
                )
                db.session.add(visit)
            else:
                visit = db.session.scalar(
                    db.select(TMonitoringVisits)
                    .filter(
                        TMonitoringVisits.id_base_site == visit_data["site"]["model"].id_base_site
                    )
                    .filter(TMonitoringVisits.visit_date_min == visit_data["date"])
                )
            visit_data["model"] = visit

    with db.session.begin_nested():
        for obs_data in objects_data["observations"]:
            visit = obs_data["visit"]["model"]
            observation = TMonitoringObservations(
                id_base_visit=visit.id_base_visit,
                cd_nom=obs_data["cd_nom"],
                digitiser=users["gestionnaire"],
                data={
                    "abondance": obs_data["abondance"],
                    "récolte": obs_data["récolte"],
                },
            )
            obs_data["model"] = observation
            db.session.add(observation)

    return {
        "sites_groups": [group_data["model"] for group_data in objects_data["groups"]],
        "sites": [site_data["model"] for site_data in objects_data["sites"]],
        "visits": [visit_data["model"] for visit_data in objects_data["visits"]],
        "observations": [
            observation_data["model"] for observation_data in objects_data["observations"]
        ],
    }


def install_test_monitoring_objects(flore_protocol, flore_site_type, users):
    return install_test_monitoring_objects_from_csv(
        "mheo_data.csv", flore_protocol, flore_site_type, users
    )


def install_more_fake_data(flore_protocol, flore_site_type, users):
    return install_test_monitoring_objects_from_csv(
        "more_fake_data.csv", flore_protocol, flore_site_type, users
    )


def install_reference_table_from_csv(csv_filename, name, description, code):
    filename = os.path.join(Path(__file__).parent, f"./{csv_filename}")
    with open(filename, newline="") as datafile:
        data = datafile.read()
        ref_table = ReferenceTable(
            name=name,
            description=description,
            code=code,
            data=data,
        )
    return ref_table


def install_reference_tables():
    with db.session.begin_nested():
        ref_table_he = install_reference_table_from_csv(
            "indices_he.csv",
            name="Indices espèce pour HE",
            description="Tableau de référence avec indices de référence par espèce pour HE",
            code="indices_he",
        )
        db.session.add(ref_table_he)
        ref_table_ht = install_reference_table_from_csv(
            "indices_ht.csv",
            name="Indices espèce pour HT",
            description="Tableau de référence avec indices de référence par espèce pour HT",
            code="indices_ht",
        )
        db.session.add(ref_table_ht)
        ref_table_abondance = install_reference_table_from_csv(
            "valeurs_abondance.csv",
            name="Valeurs abondance",
            description="Tableau de référence avec la correspondance "
            + "libellés => valeurs pour l'abondance",
            code="valeurs_abondance",
        )
        db.session.add(ref_table_abondance)

    return {
        "indices_he": ref_table_he,
        "indices_ht": ref_table_ht,
        "valeurs_abondance": ref_table_abondance,
    }


I02_DESCRIPTION = """Cet indicateur permet de suivre le niveau d’engorgement d’une zone humide à
partir de la végétation présente. Il s’appuie sur les préférences écologiques des espèces vis-à-vis
de l’humidité, sans tenir compte de leur abondance ou de leur recouvrement : chaque espèce présente
contribue de manière identique au calcul."""

I02_CODE = """valeurs_he = gn_extract(
    ref_table=indices_he,
    origin_field="cdnom",
    target_field="indice_he",
    properties=observations.cd_nom)
moyenne = gn_mean(valeurs_he, scope=Scope.SITE)
médiane = gn_median(moyenne)
moyenne_viz_data = {
    "datasets": [
        {
            "label": "Moyenne HE par quadrat",
            "data": [prop.value for prop in moyenne.values]
        }
    ],
    "labels": [prop.entity.base_site_name for prop in moyenne.values]
}
"""

I02_OVERVIEW_CODE = """labels = []
data = []
for campaign in campaigns:
  labels.append(campaign.start_date)
  data.append(campaign.vars.médiane.values[0].value)
datasets = [
  {
    "label": "I02 (médiane)",
    "data": data,
  }
]
évolution = {
  "datasets": datasets,
  "labels": labels
}

labels = ["I02 (médiane)"]
datasets = []
for campaign in campaigns:
	datasets.append(
		{
			"label": campaign.start_date,
			"data": [prop.value for prop in campaign.vars.médiane.values],
		}
	)
tableau_médianes = {
	"datasets": datasets,
	"labels": labels,
}
"""

I02_ABONDANCE_DESCRIPTION = """Cet indicateur permet de suivre le niveau d’engorgement d’une zone
humide à partir de la végétation présente. Il s’appuie sur les préférences écologiques des espèces
vis-à-vis de l’humidité et tient compte de leur abondance ou de leur recouvrement."""

I02_ABONDANCE_CODE = """valeurs_he = gn_extract(
    ref_table=indices_he,
    origin_field="cdnom",
    target_field="indice_he",
    properties=observations.cd_nom)
abondance_perc = gn_extract(
    ref_table=valeurs_abondance,
    origin_field="libellé_abondance",
    target_field="valeur_abondance",
    properties=observations.abondance,
)
moyenne = gn_mean(valeurs_he, scope=Scope.SITE, weights=abondance_perc)
médiane = gn_median(moyenne)
moyenne_viz_data = {
    "datasets": [
        {
            "label": "Moyenne HE par quadrat",
            "data": [prop.value for prop in moyenne.values]
        }
    ],
    "labels": [prop.entity.base_site_name for prop in moyenne.values]
}
"""

I02_ABONDANCE_OVERVIEW_CODE = """labels = []
data = []
for campaign in campaigns:
  labels.append(campaign.start_date)
  data.append(campaign.vars.médiane.values[0].value)
datasets = [
  {
    "label": "I02 (médiane)",
    "data": data,
  }
]
évolution = {
  "datasets": datasets,
  "labels": labels
}

labels = ["I02 (médiane)"]
datasets = []
for campaign in campaigns:
	datasets.append(
		{
			"label": campaign.start_date,
			"data": [prop.value for prop in campaign.vars.médiane.values],
		}
	)
tableau_médianes = {
	"datasets": datasets,
	"labels": labels,
}
"""

I02_ABONDANCE_STATISTICAL_TESTS_CODE = """médiane0 = campaigns[0].vars.médiane.values[0].value
médiane1 = campaigns[1].vars.médiane.values[0].value
écart = abs(médiane1 - médiane0)

#########################
# Calculer le V de Cramer
#########################

# Valeurs HE de chaque campagne
he_0 = [pv.value for pv in campaigns[0].vars.valeurs_he.values if pv.value is not None]
he_1 = [pv.value for pv in campaigns[1].vars.valeurs_he.values if pv.value is not None]

# Décomptes des occurences par classe et par campagne
he_counts_0 = collections.Counter(he_0)
he_counts_1 = collections.Counter(he_1)

def get_variables_for_cramer_v(counts0, counts1):
    # Nombre de classes pour les valeurs HE
    nb_classes = 9

    # Apparie les nombres d'occurences par classe de chaque campagne
    variables = []
    for i in range(1, nb_classes - 1):
        value0 = counts0.get(str(i), 0)
        value1 = counts1.get(str(i), 0)
        if value0 != 0 or value1 != 0:
            variables.append([value0, value1])

    # Fusionne les classes avec moins de 5 occurences au total
    # avec la classe adjacente.
    i = 0
    while i < len(variables):
        if len(variables) == 1:
            break
        value0, value1 = variables[i]
        if value0 + value1 < 5:
            is_last = i == len(variables) - 1
            if not is_last:
                # merge forward
                next0, next1 = variables[i + 1]
                variables[i + 1] = [next0 + value0, next1 + value1]
                variables.pop(i)
            else:
                # merge backward
                prev0, prev1 = variables[i - 1]
                variables[i - 1] = [prev0 + value0, prev1 + value1]
                variables.pop(i)
        else:
            i += 1

    if len(variables) == 1:
        value0, value1 = variables[0]
        if value0 + value1 < 5:
            raise IndicatorError("Il n'y a pas assez de données pour réaliser le test V de Cramer")

    return variables

cramer_v_variables = get_variables_for_cramer_v(he_counts_0, he_counts_1)
cramer_v = scipy.stats.contingency.association(cramer_v_variables, method="cramer")

##################
# Test de Wilcoxon
##################

he0 = [float(v.value) for v in campaigns[0].vars.moyenne.values]
he1 = [float(v.value) for v in campaigns[1].vars.moyenne.values]
wilcoxon = scipy.stats.wilcoxon(he0, he1, zero_method="zsplit").statistic
"""

I06_DESCRIPTION = """Cet indicateur permet de suivre le niveau de fertilité du sol d’une zone humide
à partir de la végétation présente. Il renseigne indirectement sur la disponibilité en nutriments,
principalement l’azote et le phosphore, sans tenir compte de l’abondance ou du recouvrement des
espèces : chaque espèce présente contribue de manière identique au calcul."""

I06_CODE = """valeurs_ht = gn_extract(
    ref_table=indices_ht,
    origin_field="cdnom",
    target_field="indice_ht",
    properties=observations.cd_nom)
moyenne = gn_mean(valeurs_ht, scope=Scope.SITE)
médiane = gn_median(moyenne)
moyenne_viz_data = {
    "datasets": [
        {
            "label": "Moyenne HT par quadrat",
            "data": [prop.value for prop in moyenne.values]
        }
    ],
    "labels": [prop.entity.base_site_name for prop in moyenne.values]
}
"""

I06_OVERVIEW_CODE = """labels = []
data = []
for campaign in campaigns:
  labels.append(campaign.start_date)
  data.append(campaign.vars.médiane.values[0].value)
datasets = [
  {
    "label": "I06 (médiane)",
    "data": data,
  }
]
évolution = {
  "datasets": datasets,
  "labels": labels
}

labels = ["I06 (médiane)"]
datasets = []
for campaign in campaigns:
	datasets.append(
		{
			"label": campaign.start_date,
			"data": [prop.value for prop in campaign.vars.médiane.values],
		}
	)
tableau_médianes = {
	"datasets": datasets,
	"labels": labels,
}
"""

I06_ABONDANCE_DESCRIPTION = """Cet indicateur permet de suivre le niveau de fertilité du sol d’une
zone humide à partir de la végétation présente. Il renseigne indirectement sur la disponibilité en
nutriments, principalement l’azote et le phosphore, en tenant compte de l’abondance ou du
recouvrement des espèces."""

I06_ABONDANCE_CODE = """valeurs_ht = gn_extract(
    ref_table=indices_ht,
    origin_field="cdnom",
    target_field="indice_ht",
    properties=observations.cd_nom)
abondance_perc = gn_extract(
    ref_table=valeurs_abondance,
    origin_field="libellé_abondance",
    target_field="valeur_abondance",
    properties=observations.abondance,
)
moyenne = gn_mean(valeurs_ht, scope=Scope.SITE, weights=abondance_perc)
médiane = gn_median(moyenne)
moyenne_viz_data = {
    "datasets": [
        {
            "label": "Moyenne HT par quadrat",
            "data": [prop.value for prop in moyenne.values]
        }
    ],
    "labels": [prop.entity.base_site_name for prop in moyenne.values]
}
"""

I06_ABONDANCE_OVERVIEW_CODE = """labels = []
data = []
for campaign in campaigns:
  labels.append(campaign.start_date)
  data.append(campaign.vars.médiane.values[0].value)
datasets = [
  {
    "label": "I06 (médiane)",
    "data": data,
  }
]
évolution = {
  "datasets": datasets,
  "labels": labels
}

labels = ["I06 (médiane)"]
datasets = []
for campaign in campaigns:
	datasets.append(
		{
			"label": campaign.start_date,
			"data": [prop.value for prop in campaign.vars.médiane.values],
		}
	)
tableau_médianes = {
	"datasets": datasets,
	"labels": labels,
}
"""


def install_test_indicators(protocols, reference_tables):
    indicators = {}

    def create_indicators(indicators_data, protocol):
        with db.session.begin_nested():
            for data in indicators_data:
                ref_tables = []
                if "reference_table_codes" in data:
                    ref_tables = [
                        reference_tables[rt_code] for rt_code in data["reference_table_codes"]
                    ]
                    del data["reference_table_codes"]
                ref = data.pop("ref")
                data["protocol"] = protocol
                if "description" not in data:
                    data["description"] = f"This is the {data['name']} indicator description."
                indicator = Indicator(**data)
                for rt in ref_tables:
                    indicator.reference_tables.append(rt)
                indicators[ref] = indicator
                db.session.add(indicator)

    test_flore_indicators_data = [
        {
            "name": "I02 - indice floristique d'engorgement",
            "reference_table_codes": ["indices_he"],
            "source_code": I02_CODE,
            "overview_source_code": I02_OVERVIEW_CODE,
            "ref": "i02",
            "description": I02_DESCRIPTION,
        },
        {
            "name": "I02 - indice floristique d'engorgement (avec abondance)",
            "reference_table_codes": ["indices_he", "valeurs_abondance"],
            "source_code": I02_ABONDANCE_CODE,
            "overview_source_code": I02_ABONDANCE_OVERVIEW_CODE,
            "statistical_tests_source_code": I02_ABONDANCE_STATISTICAL_TESTS_CODE,
            "ref": "i02_abondance",
            "description": I02_ABONDANCE_DESCRIPTION,
        },
        {
            "name": "I06 - indice floristique de fertilité du sol",
            "reference_table_codes": ["indices_ht"],
            "source_code": I06_CODE,
            "overview_source_code": I06_OVERVIEW_CODE,
            "ref": "i06",
            "description": I06_DESCRIPTION,
        },
        {
            "name": "I06 - indice floristique de fertilité du sol (avec abondance)",
            "reference_table_codes": ["indices_ht", "valeurs_abondance"],
            "source_code": I06_ABONDANCE_CODE,
            "overview_source_code": I06_ABONDANCE_OVERVIEW_CODE,
            "ref": "i06_abondance",
            "description": I06_ABONDANCE_DESCRIPTION,
        },
    ]
    flore_protocol = protocols["mheo_flore_test"]
    create_indicators(test_flore_indicators_data, flore_protocol)

    odonate_protocol = protocols["mheo_odonate_test"]
    create_indicators(
        indicators_data=[
            {
                "name": "I10 - intégrité du peuplement d’odonates",
                "ref": "i10",
            }
        ],
        protocol=odonate_protocol,
    )

    return indicators


I02_ABONDANCE_MEDIANE_INFO = """La médiane des valeurs HE calculées pour l’ensemble des quadrats
correspond à la note de l’indicateur à l’échelle du site en tenant compte de l’abondance des
espèces.<br>
Elle correspond à la valeur qui partage les quadrats en deux groupes de même effectif : 50 %
présentent une valeur HE inférieure ou égale à la médiane et 50 % une valeur supérieure ou
égale.<br>
Elle permet de caractériser la tendance globale du niveau d’engorgement du site.
Son évolution entre plusieurs campagnes de suivi permet d’apprécier l’évolution des conditions
d’engorgement."""

I02_ABONDANCE_MEDIANE_DESCRIPTION = """Note de l’indicateur à l’échelle du site, calculée à partir
de la médiane des valeurs HE des quadrats."""

I02_ABONDANCE_BARCHART_INFO = """Pour chaque quadrat, une valeur HE est calculée à partir des
valeurs indicatrices d’humidité des espèces végétales présentes, pondérées par leur abondance ou
leur recouvrement.<br><br>

He= Σ (rij * xi) / Σ (rij)<br>
<em><strong>rij</strong> est l’abondance (ou recouvrement) de l’espèce i dans le relevé j </em><br>
<em><strong>xi</strong> est la valeur indicatrice de l’espèce i </em><br><br>

Les espèces les plus abondantes contribuent ainsi davantage au calcul que les espèces peu
représentées. Il varie pour les habitats de zones humides, de 2,5 (habitats mésophiles) à 9
(habitats subaquatiques). <br><br>

L’histogramme représente la valeur HE obtenue pour chaque quadrat. Il permet de comparer les
quadrats entre eux et de visualiser la variabilité des conditions d’engorgement au sein du site."""

I02_ABONDANCE_BARCHART_DESCRIPTION = """Valeur d’engorgement floristique calculée pour chaque
quadrat en tenant compte de l’abondance des espèces."""

I02_ABONDANCE_LINECHART_INFO = """Cette représentation reprend les valeurs HE calculées pour chaque
quadrat et présentées dans l’histogramme ci-dessus. La courbe offre une autre visualisation de la
variabilité des valeurs entre les différents quadrats du site."""

I02_ABONDANCE_LINECHART_DESCRIPTION = """Courbe permettant la visualisation des valeurs HE par
quadrats pour 1 année."""

I02_ABONDANCE_TABLE_INFO = """Ce tableau reprend les valeurs HE calculées pour chaque quadrat et
permet de consulter précisément la valeur obtenue pour chacun d’entre eux."""

I02_ABONDANCE_TABLE_DESCRIPTION = """Tableau permettant la visualisation des valeurs HE par quadrats
pour 1 année."""


def install_i02_abondance_visualization_config(indicators):
    i02_abondance = indicators["i02_abondance"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Médiane HE",
            info=I02_ABONDANCE_MEDIANE_INFO,
            description=I02_ABONDANCE_MEDIANE_DESCRIPTION,
            type=VizBlockType.scalar,
            params={
                "variable": "médiane",
            },
        )
        db.session.add(scalar_block)
        barchart_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Moyenne HE (pondérée par abondance)",
            info=I02_ABONDANCE_BARCHART_INFO,
            description=I02_ABONDANCE_BARCHART_DESCRIPTION,
            type=VizBlockType.bar_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(barchart_block)
        linechart_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Moyenne HE par quadrat (pondérée par abondance)",
            info=I02_ABONDANCE_LINECHART_INFO,
            description=I02_ABONDANCE_LINECHART_DESCRIPTION,
            type=VizBlockType.line_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(linechart_block)
        table_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Moyenne HE par quadrat (pondérée par abondance)",
            info=I02_ABONDANCE_TABLE_INFO,
            description=I02_ABONDANCE_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(table_block)

    return scalar_block, barchart_block, table_block, linechart_block


I02_ABONDANCE_OVERVIEW_TABLE_INFO = """Pour analyser une tendance, il faut
disposer d’au moins trois campagnes de suivi. L’évolution observée peut alors indiquer une tendance
à la hausse, à la baisse ou une relative stabilité de l’indicateur.<br><br>

Une différence entre deux campagnes ne traduit cependant pas nécessairement un changement
significatif du fonctionnement de la zone humide. Les résultats des tests statistiques présentés
plus bas dans la calculatrice doivent être consultés afin d’évaluer la significativité des
différences observées.<br><br>

L’indicateur I02 de MhéO constitue un outil de suivi et d’alerte : il permet de mettre en évidence
une évolution, mais ne permet pas, à lui seul, d’en déterminer la cause. En cas de changement,
l’interprétation doit être complétée par une analyse du contexte de la zone humide et de son
évolution.<br>
De nombreux facteurs peuvent être à l’origine des changements observés : modifications de
l’occupation du sol ou du tissu urbain, drainage agricole, prélèvements ou pompages d’eau,
travaux de gestion, évolution climatique, conditions particulières lors des différentes campagnes
de terrain, etc. Cette liste n’est pas exhaustive : d’autres facteurs, propres au contexte local
et au fonctionnement de chaque zone humide, peuvent également expliquer l’évolution de
l’indicateur.<br>
Ces éléments permettent de rechercher les facteurs susceptibles d’expliquer l’évolution observée
et d’orienter, si nécessaire, des analyses complémentaires ou la potentielle nécessité de
réaliser des travaux."""

I02_ABONDANCE_OVERVIEW_TABLE_DESCRIPTION = """Tableau synthèse de l’évolution de l’indicateur au
cours du temps.<br>
Ce bloc présente la note de l’indicateur obtenue à chaque campagne de suivi, correspondant à la
médiane des valeurs calculées pour l’ensemble des quadrats (en tenant compte de l’abondance des
espèces)."""

I02_ABONDANCE_OVERVIEW_EVOLUTION_INFO = """Le graphique permet de visualiser l’évolution de
l’indicateur au cours du temps."""

I02_ABONDANCE_OVERVIEW_EVOLUTION_DESCRIPTION = """Courbe d’évolution de l’indicateur au cours du
temps."""


def install_i02_abondance_overview_visualization_config(indicators):
    i02_abondance = indicators["i02_abondance"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Médiane des valeurs HE des quadrats par année",
            info=I02_ABONDANCE_OVERVIEW_TABLE_INFO,
            description=I02_ABONDANCE_OVERVIEW_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            scope=VizBlockScope.overview,
            params={
                "variable": "tableau_médianes",
            },
        )
        db.session.add(scalar_block)
        line_chart_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Évolution de la valeur de l'indicateur",
            info=I02_ABONDANCE_OVERVIEW_EVOLUTION_INFO,
            description=I02_ABONDANCE_OVERVIEW_EVOLUTION_DESCRIPTION,
            type=VizBlockType.line_chart,
            scope=VizBlockScope.overview,
            params={
                "variable": "évolution",
            },
        )
        db.session.add(line_chart_block)

    return scalar_block, line_chart_block


def install_i02_abondance_statistical_tests_visualization_config(indicators):
    i02_abondance = indicators["i02_abondance"]
    with db.session.begin_nested():
        description = (
            "Si l’écart est inférieur à 0,3 alors le test n’est pas validé. "
            "Si deux des trois tests statistiques ne sont pas validés alors "
            "il n’y a pas d’évolution significative entre les deux dates. "
            "L’indicateur est stable."
        )
        scalar_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Écart des médianes",
            info="???",
            description=description,
            type=VizBlockType.scalar,
            scope=VizBlockScope.statistical_tests,
            params={
                "variable": "écart",
            },
        )
        description_v_cramer = """Le coefficient V de Cramer (entre 0 et 1) mesure si les
distributions diffèrent.<br>
• Association forte si V > 0.5<br>
• Association modérée si V compris entre 0.3 et 0.5<br>
• Association faible si V compris entre 0.1 et 0.3<br>
• Pas d’association si V < 0.1<br>
Si le V de Cramer est inférieur à 0,1 alors le test n’est pas validé.
"""
        db.session.add(scalar_block)
        cramer_v_scalar_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Test V de Cramer",
            info="???",
            description=description_v_cramer,
            type=VizBlockType.scalar,
            scope=VizBlockScope.statistical_tests,
            params={
                "variable": "cramer_v",
            },
        )
        db.session.add(cramer_v_scalar_block)
        description_wilcoxon = """<table border="1" cellpadding="10" cellspacing="0"
    style="border-collapse: collapse; font-family: Arial, sans-serif;">
    <thead>
    <tr style="background-color: #4a9b8e; color: white;">
        <th rowspan="0">N</th>
        <th colspan="3" style="text-align: center;">Niveau de signification, test unilatéral</th>
    </tr>
    <tr style="background-color: #4a9b8e; color: white;">
        <th>0,025</th>
        <th>0,01</th>
        <th>0,005</th>
    </tr>
    <tr>
        <th colspan="3" style="text-align: center;">Niveau de signification, test bilatéral</th>
    </tr>
    <tr style="background-color: #4a9b8e; color: white;">
        <th>0,05</th>
        <th>0,02</th>
        <th>0,01</th>
    </tr>
    </thead>
    <tbody>
    <tr style="background-color: #f5f5f5;">
        <td>6</td>
        <td>0</td>
        <td></td>
        <td></td>
    </tr>
    <tr>
        <td>7</td>
        <td>2</td>
        <td>0</td>
        <td></td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>8</td>
        <td>4</td>
        <td>2</td>
        <td>0</td>
    </tr>
    <tr>
        <td>9</td>
        <td>6</td>
        <td>3</td>
        <td>2</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>10</td>
        <td>8</td>
        <td>5</td>
        <td>3</td>
    </tr>
    <tr>
        <td>11</td>
        <td>11</td>
        <td>7</td>
        <td>5</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>12</td>
        <td>14</td>
        <td>10</td>
        <td>7</td>
    </tr>
    <tr>
        <td>13</td>
        <td>17</td>
        <td>13</td>
        <td>10</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>14</td>
        <td>21</td>
        <td>16</td>
        <td>13</td>
    </tr>
    <tr>
        <td>15</td>
        <td>25</td>
        <td>20</td>
        <td>16</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>16</td>
        <td>30</td>
        <td>24</td>
        <td>20</td>
    </tr>
    <tr>
        <td>17</td>
        <td>35</td>
        <td>28</td>
        <td>23</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>18</td>
        <td>40</td>
        <td>33</td>
        <td>28</td>
    </tr>
    <tr>
        <td>19</td>
        <td>46</td>
        <td>38</td>
        <td>32</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>20</td>
        <td>52</td>
        <td>43</td>
        <td>38</td>
    </tr>
    <tr>
        <td>21</td>
        <td>59</td>
        <td>49</td>
        <td>43</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>22</td>
        <td>66</td>
        <td>56</td>
        <td>49</td>
    </tr>
    <tr>
        <td>23</td>
        <td>73</td>
        <td>62</td>
        <td>55</td>
    </tr>
    <tr style="background-color: #f5f5f5;">
        <td>24</td>
        <td>81</td>
        <td>69</td>
        <td>61</td>
    </tr>
    <tr>
        <td>25</td>
        <td>89</td>
        <td>77</td>
        <td>68</td>
    </tr>
    </tbody>
</table>

N = le nombre de quadrats<br>
Il faut regarder la ligne correspondant au nombre de quadrats réalisés sur la zone humide.<br>
Si les deux valeurs (rang positif et rang négatif) sont supérieures à toutes les limites alors
la différence entre les deux années n’est pas significative, l’indicateur est stable.<br>
Si une des valeurs (rang positif ou rang négatif) est inférieur à une des limites alors la
différence entre les deux années est significative. L’indicateur montre une évolution."""
        wilcoxon_scalar_block = VizBlockConfig(
            id_indicator=i02_abondance.id_indicator,
            title="Test de Wilcoxon",
            info="???",
            description=description_wilcoxon,
            type=VizBlockType.scalar,
            scope=VizBlockScope.statistical_tests,
            params={
                "variable": "wilcoxon",
            },
        )
        db.session.add(wilcoxon_scalar_block)

    return scalar_block, cramer_v_scalar_block, wilcoxon_scalar_block


I02_MEDIANE_INFO = """La médiane des valeurs HE calculées pour l’ensemble des quadrats correspond à
la note de l’indicateur à l’échelle du site, sans tenir compte de l’abondance des espèces.
Elle correspond à la valeur qui partage les quadrats en deux groupes de même effectif : 50 %
présentent une valeur HE inférieure ou égale à la médiane et 50 % une valeur supérieure ou
égale.<br>
Elle permet de caractériser la tendance globale du niveau d’engorgement du site. Son évolution entre
plusieurs campagnes de suivi permet d’apprécier l’évolution des conditions d’engorgement."""

I02_MEDIANE_DESCRIPTION = """Note de l’indicateur à l’échelle du site, calculée à partir de la
médiane des valeurs HE des quadrats."""

I02_BARCHART_INFO = """Pour chaque quadrat, une valeur HE est calculée à partir des valeurs
indicatrices d’humidité des espèces végétales présentes, sans tenir compte de leur abondance ou de
leur recouvrement.<br><br>

He = Σ(xi) / n<br>
<em><strong>xi</strong> est la valeur indicatrice de l’espèce i</em><br>
<em><strong>n</strong> est le nombre total d’espèces prises en compte dans le quadrat</em><br><br>

Chaque espèce contribue ainsi de manière identique au calcul. Il varie pour les habitats de zones
humides, de 2,5 (habitats mésophiles) à 9 (habitats subaquatiques).<br><br>

L’histogramme représente la valeur HE obtenue pour chaque quadrat. Il permet de comparer les
quadrats entre eux et de visualiser la variabilité des conditions d’engorgement au sein du site."""

I02_BARCHART_DESCRIPTION = """Valeur d’engorgement floristique calculée pour chaque quadrat sans
tenir compte de l’abondance des espèces."""

I02_LINECHART_INFO = """Cette représentation reprend les valeurs HE calculées pour chaque
quadrat et présentées dans l’histogramme ci-dessus. La courbe offre une autre visualisation de la
variabilité des valeurs entre les différents quadrats du site."""

I02_LINECHART_DESCRIPTION = """Courbe permettant la visualisation des valeurs HE par
quadrats pour 1 année."""

I02_TABLE_INFO = """Ce tableau reprend les valeurs HE calculées pour chaque quadrat et
permet de consulter précisément la valeur obtenue pour chacun d’entre eux."""

I02_TABLE_DESCRIPTION = """Tableau permettant la visualisation des valeurs HE par quadrats
pour 1 année."""


def install_i02_visualization_config(indicators):
    i02 = indicators["i02"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Médiane HE",
            info=I02_MEDIANE_INFO,
            description=I02_MEDIANE_DESCRIPTION,
            type=VizBlockType.scalar,
            params={
                "variable": "médiane",
            },
        )
        db.session.add(scalar_block)
        barchart_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Moyenne HE par quadrat (non pondérée par abondance)",
            info=I02_MEDIANE_INFO,
            description=I02_MEDIANE_DESCRIPTION,
            type=VizBlockType.bar_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(barchart_block)
        linechart_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Moyenne HE par quadrat (non pondérée par abondance)",
            info=I02_LINECHART_INFO,
            description=I02_LINECHART_DESCRIPTION,
            type=VizBlockType.line_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(linechart_block)
        table_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Moyenne HE par quadrat (non pondérée par abondance)",
            info=I02_TABLE_INFO,
            description=I02_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(table_block)

    return scalar_block, barchart_block, table_block, linechart_block


I02_OVERVIEW_TABLE_INFO = """Pour analyser une tendance, il faut
disposer d’au moins trois campagnes de suivi. L’évolution observée peut alors indiquer une tendance
à la hausse, à la baisse ou une relative stabilité de l’indicateur.<br><br>

Une différence entre deux campagnes ne traduit cependant pas nécessairement un changement
significatif du fonctionnement de la zone humide. Les résultats des tests statistiques présentés
plus bas dans la calculatrice doivent être consultés afin d’évaluer la significativité des
différences observées.<br><br>

L’indicateur I02 de MhéO constitue un outil de suivi et d’alerte : il permet de mettre en évidence
une évolution, mais ne permet pas, à lui seul, d’en déterminer la cause. En cas de changement,
l’interprétation doit être complétée par une analyse du contexte de la zone humide et de son
évolution.<br>
De nombreux facteurs peuvent être à l’origine des changements observés : modifications de
l’occupation du sol ou du tissu urbain, drainage agricole, prélèvements ou pompages d’eau,
travaux de gestion, évolution climatique, conditions particulières lors des différentes campagnes
de terrain, etc. Cette liste n’est pas exhaustive : d’autres facteurs, propres au contexte local
et au fonctionnement de chaque zone humide, peuvent également expliquer l’évolution de
l’indicateur.<br>
Ces éléments permettent de rechercher les facteurs susceptibles d’expliquer l’évolution observée
et d’orienter, si nécessaire, des analyses complémentaires ou la potentielle nécessité de
réaliser des travaux."""

I02_OVERVIEW_TABLE_DESCRIPTION = """Tableau synthèse de l’évolution de l’indicateur au
cours du temps.<br>
Ce bloc présente la note de l’indicateur obtenue à chaque campagne de suivi, correspondant à la
médiane des valeurs calculées pour l’ensemble des quadrats (en tenant compte de l’abondance des
espèces)."""

I02_OVERVIEW_EVOLUTION_INFO = """Le graphique permet de visualiser l’évolution de
l’indicateur au cours du temps."""

I02_OVERVIEW_EVOLUTION_DESCRIPTION = """Courbe d’évolution de l’indicateur au cours du temps."""


def install_i02_overview_visualization_config(indicators):
    i02 = indicators["i02"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Médiane des valeurs HE des quadrats par année",
            info=I02_OVERVIEW_TABLE_INFO,
            description=I02_OVERVIEW_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            scope=VizBlockScope.overview,
            params={
                "variable": "tableau_médianes",
            },
        )
        db.session.add(scalar_block)
        line_chart_block = VizBlockConfig(
            id_indicator=i02.id_indicator,
            title="Évolution de la valeur de l'indicateur",
            info=I02_OVERVIEW_EVOLUTION_INFO,
            description=I02_OVERVIEW_EVOLUTION_DESCRIPTION,
            type=VizBlockType.line_chart,
            scope=VizBlockScope.overview,
            params={
                "variable": "évolution",
            },
        )
        db.session.add(line_chart_block)

    return scalar_block, line_chart_block


I06_MEDIANE_INFO = """La médiane des valeurs de fertilité HT calculées pour l’ensemble des quadrats
correspond à la note de l’indicateur à l’échelle du site, sans tenir compte de l’abondance des
espèces.<br><br>

Elle correspond à la valeur qui partage les quadrats en deux groupes de même effectif : 50 %
présentent une valeur de fertilité inférieure ou égale à la médiane et 50 % une valeur supérieure ou
égale.<br><br>

Elle permet de caractériser la tendance globale du niveau de fertilité du sol. Son évolution entre
plusieurs campagnes de suivi permet d’apprécier l’évolution de la disponibilité en nutriments du
site."""

I06_MEDIANE_DESCRIPTION = """Note de l’indicateur à l’échelle du site, calculée à partir de la
médiane des valeurs de fertilité HT des quadrats."""

I06_BARCHART_INFO = """La disponibilité des nutriments dans le sol, principalement l’azote et le
phosphore, influence la composition de la végétation. Les espèces végétales étant plus ou moins
adaptées à des sols riches en nutriments, leur présence permet d’estimer indirectement le niveau de
fertilité du sol à partir de leur valeur indicatrice.<br><br>

Pour chaque quadrat, une valeur de fertilité HT est calculée à partir des valeurs indicatrices de
fertilité des espèces végétales présentes, sans tenir compte de leur abondance ou de leur
recouvrement.<br><br>

HT = Σ(xi) / n<br>
<em><strong>xi</strong> est la valeur indicatrice de fertilité de l’espèce i. </em><br>
<em><strong>n</strong> est le nombre total d’espèces prises en compte dans le quadrat.</em><br><br>

Chaque espèce contribue ainsi de manière identique au calcul. L’indice varie de 1 pour les sites
très pauvres en nutriments à 9 pour les sites très riches en nutriments.<br><br>

L’histogramme représente la valeur HT obtenue pour chaque quadrat. Il permet de comparer les
quadrats entre eux et de visualiser la variabilité de la fertilité du sol au sein du site."""

I06_BARCHART_DESCRIPTION = """Valeur de fertilité du sol calculée pour chaque quadrat sans tenir
compte de l’abondance des espèces."""

I06_LINECHART_INFO = """Cette représentation reprend les valeurs de fertilité HT calculées pour
chaque quadrat et présentées dans l’histogramme ci-dessus. La courbe offre une autre visualisation
de la variabilité des valeurs entre les différents quadrats du site."""

I06_LINECHART_DESCRIPTION = """Courbe permettant la visualisation des valeurs de fertilité HT par
quadrats pour 1 année."""

I06_TABLE_INFO = """Ce tableau reprend les valeurs de fertilité HT calculées pour chaque quadrat et
permet de consulter précisément la valeur obtenue pour chacun d’entre eux."""

I06_TABLE_DESCRIPTION = """Tableau permettant la visualisation des valeurs de fertilité HT par
quadrats pour 1 année."""


def install_i06_visualization_config(indicators):
    i06 = indicators["i06"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Médiane HT",
            info=I06_MEDIANE_INFO,
            description=I06_MEDIANE_DESCRIPTION,
            type=VizBlockType.scalar,
            params={
                "variable": "médiane",
            },
        )
        db.session.add(scalar_block)
        barchart_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Moyenne HT",
            info=I06_BARCHART_INFO,
            description=I06_BARCHART_DESCRIPTION,
            type=VizBlockType.bar_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(barchart_block)
        linechart_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Moyenne HT par quadrat (pondérée par abondance)",
            info=I06_LINECHART_INFO,
            description=I06_LINECHART_DESCRIPTION,
            type=VizBlockType.line_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(linechart_block)
        table_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Moyenne HT par quadrat (pondérée par abondance)",
            info=I06_TABLE_INFO,
            description=I06_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(table_block)

    return scalar_block, barchart_block, table_block, linechart_block


I06_OVERVIEW_TABLE_INFO = """Pour analyser une tendance, il faut disposer d’au moins trois campagnes
de suivi. L’évolution observée peut alors indiquer une tendance à la hausse, à la baisse ou une
relative stabilité de l’indicateur.<br><br>

Une différence entre deux campagnes ne traduit cependant pas nécessairement un changement
significatif du fonctionnement de la zone humide. Les résultats des tests statistiques présentés
plus bas dans la calculatrice doivent être consultés afin d’évaluer la significativité des
différences observées.<br><br>

L’indicateur I06 de MhéO constitue un outil de suivi et d’alerte : il permet de mettre en évidence
une évolution de la fertilité du sol, mais ne permet pas, à lui seul, d’en déterminer la cause. En
cas de changement, l’interprétation doit être complétée par une analyse du contexte de la zone
humide et de son évolution.<br><br>

De nombreux facteurs peuvent être à l’origine des changements observés : évolution des pratiques
agricoles, apports de nutriments, modification des écoulements ou du fonctionnement hydrologique,
changements d’occupation du sol, travaux de gestion, etc. Cette liste n’est pas exhaustive :
d’autres facteurs, propres au contexte local et au fonctionnement de chaque zone humide, peuvent
également expliquer l’évolution de l’indicateur.<br><br>

Ces éléments permettent de rechercher les facteurs susceptibles d’expliquer l’évolution observée et
d’orienter, si nécessaire, des analyses complémentaires ou la potentielle nécessité de réaliser des
travaux."""

I06_OVERVIEW_TABLE_DESCRIPTION = """Tableau synthèse de l’évolution de l’indicateur au cours du
temps.<br>
Ce bloc présente la note de l’indicateur obtenue à chaque campagne de suivi, correspondant à la
médiane des valeurs de fertilité du sol calculées pour l’ensemble des quadrats en tenant compte de
l’abondance des espèces. """

I06_OVERVIEW_EVOLUTION_INFO = """Le graphique permet de visualiser son évolution au cours du
temps."""

I06_OVERVIEW_EVOLUTION_DESCRIPTION = """Courbe d’évolution de l’indicateur au cours du temps."""


def install_i06_overview_visualization_config(indicators):
    i06 = indicators["i06"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Médiane des valeurs HT des quadrats par année",
            info=I06_OVERVIEW_TABLE_INFO,
            description=I06_OVERVIEW_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            scope=VizBlockScope.overview,
            params={
                "variable": "tableau_médianes",
            },
        )
        db.session.add(scalar_block)
        line_chart_block = VizBlockConfig(
            id_indicator=i06.id_indicator,
            title="Évolution de la valeur de l'indicateur",
            info=I06_OVERVIEW_EVOLUTION_INFO,
            description=I06_OVERVIEW_EVOLUTION_DESCRIPTION,
            type=VizBlockType.line_chart,
            scope=VizBlockScope.overview,
            params={
                "variable": "évolution",
            },
        )
        db.session.add(line_chart_block)

    return scalar_block, line_chart_block


I06_ABONDANCE_MEDIANE_INFO = """La médiane des valeurs de fertilité HT calculées pour l’ensemble des
quadrats correspond à la note de l’indicateur à l’échelle du site en tenant compte de l’abondance
des espèces.<br><br>

Elle correspond à la valeur qui partage les quadrats en deux groupes de même effectif : 50 %
présentent une valeur de fertilité inférieure ou égale à la médiane et 50 % une valeur supérieure ou
égale.<br><br>

Elle permet de caractériser la tendance globale du niveau de fertilité du sol. Son évolution entre
plusieurs campagnes de suivi permet d’apprécier l’évolution de la disponibilité en nutriments du
site."""

I06_ABONDANCE_MEDIANE_DESCRIPTION = """Note de l’indicateur à l’échelle du site, calculée à partir
de la médiane des valeurs HT des quadrats."""

I06_ABONDANCE_BARCHART_INFO = """La disponibilité des nutriments dans le sol, principalement l’azote
et le phosphore, influence la composition de la végétation. Les espèces végétales étant plus ou
moins adaptées à des sols riches en nutriments, leur présence permet d’estimer indirectement le
niveau de fertilité du sol à partir de leur valeur indicatrice.<br><br>

Pour chaque quadrat, une valeur de fertilité HT est calculée à partir des valeurs indicatrices de
fertilité des espèces végétales présentes, pondérées par leur abondance ou leur
recouvrement.<br><br>

HT = Σ (rij × xi) / Σ (rij)
<em><strong>rij</strong> est l’abondance (ou le recouvrement) de l’espèce i dans le relevé j.
</em><br>
<em><strong>xi</strong> est la valeur indicatrice de fertilité de l’espèce i.</em><br><br>

Les espèces les plus abondantes contribuent ainsi davantage au calcul que les espèces peu
représentées. L’indice varie de 1 pour les sites très pauvres en nutriments à 9 pour les sites très
riches en nutriments.<br><br>

L’histogramme représente la valeur HT obtenue pour chaque quadrat. Il permet de comparer les
quadrats entre eux et de visualiser la variabilité de la fertilité du sol au sein du site."""

I06_ABONDANCE_BARCHART_DESCRIPTION = """Valeur de fertilité du sol calculée pour chaque quadrat en
tenant compte de l’abondance des espèces."""

I06_ABONDANCE_LINECHART_INFO = """Cette représentation reprend les valeurs de fertilité HT calculées
pour chaque quadrat et présentées dans l’histogramme ci-dessus. La courbe offre une autre
visualisation de la variabilité des valeurs entre les différents quadrats du site."""

I06_ABONDANCE_LINECHART_DESCRIPTION = """Courbe permettant la visualisation des valeurs HT par
quadrats pour 1 année."""

I06_ABONDANCE_TABLE_INFO = """Ce tableau reprend les valeurs de fertilité HT calculées pour chaque
quadrat et permet de consulter précisément la valeur obtenue pour chacun d’entre eux."""

I06_ABONDANCE_TABLE_DESCRIPTION = """Tableau permettant la visualisation des valeurs HT par quadrats
pour 1 année."""


def install_i06_abondance_visualization_config(indicators):
    i06_abondance = indicators["i06_abondance"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Médiane HT",
            info=I06_ABONDANCE_MEDIANE_INFO,
            description=I06_ABONDANCE_MEDIANE_DESCRIPTION,
            type=VizBlockType.scalar,
            params={
                "variable": "médiane",
            },
        )
        db.session.add(scalar_block)
        barchart_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Moyenne HT",
            info=I06_ABONDANCE_BARCHART_INFO,
            description=I06_ABONDANCE_BARCHART_DESCRIPTION,
            type=VizBlockType.bar_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(barchart_block)
        linechart_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Moyenne HT par quadrat (pondérée par abondance)",
            info=I06_ABONDANCE_LINECHART_INFO,
            description=I06_ABONDANCE_LINECHART_DESCRIPTION,
            type=VizBlockType.line_chart,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(linechart_block)
        table_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Moyenne HT par quadrat (pondérée par abondance)",
            info=I06_ABONDANCE_TABLE_INFO,
            description=I06_ABONDANCE_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            params={
                "variable": "moyenne_viz_data",
            },
        )
        db.session.add(table_block)

    return scalar_block, barchart_block, table_block, linechart_block


I06_ABONDANCE_OVERVIEW_TABLE_INFO = """Pour analyser une tendance, il faut disposer d’au moins trois
campagnes de suivi. L’évolution observée peut alors indiquer une tendance à la hausse, à la baisse
ou une relative stabilité de l’indicateur.<br><br>

Une différence entre deux campagnes ne traduit cependant pas nécessairement un changement
significatif du fonctionnement de la zone humide. Les résultats des tests statistiques présentés
plus bas dans la calculatrice doivent être consultés afin d’évaluer la significativité des
différences observées.<br><br>

L’indicateur I06 de MhéO constitue un outil de suivi et d’alerte : il permet de mettre en évidence
une évolution de la fertilité du sol, mais ne permet pas, à lui seul, d’en déterminer la cause. En
cas de changement, l’interprétation doit être complétée par une analyse du contexte de la zone
humide et de son évolution.<br><br>

De nombreux facteurs peuvent être à l’origine des changements observés : évolution des pratiques
agricoles, apports de nutriments, modification des écoulements ou du fonctionnement hydrologique,
changements d’occupation du sol, travaux de gestion, etc. Cette liste n’est pas exhaustive :
d’autres facteurs, propres au contexte local et au fonctionnement de chaque zone humide, peuvent
également expliquer l’évolution de l’indicateur.<br><br>

Ces éléments permettent de rechercher les facteurs susceptibles d’expliquer l’évolution observée et
d’orienter, si nécessaire, des analyses complémentaires ou la potentielle nécessité de réaliser des
travaux."""

I06_ABONDANCE_OVERVIEW_TABLE_DESCRIPTION = """Tableau synthèse de l’évolution de l’indicateur au
cours du temps.<br>
Ce bloc présente la note de l’indicateur obtenue à chaque campagne de suivi, correspondant à la
médiane des valeurs de fertilité du sol calculées pour l’ensemble des quadrats sans tenir compte de
l’abondance des espèces. """

I06_ABONDANCE_OVERVIEW_EVOLUTION_INFO = """Le graphique permet de visualiser son évolution au cours
du temps."""

I06_ABONDANCE_OVERVIEW_EVOLUTION_DESCRIPTION = """Courbe d’évolution de l’indicateur au cours du
temps."""


def install_i06_abondance_overview_visualization_config(indicators):
    i06_abondance = indicators["i06_abondance"]
    with db.session.begin_nested():
        scalar_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Médiane des valeurs HT des quadrats par année",
            info=I06_ABONDANCE_OVERVIEW_TABLE_INFO,
            description=I06_ABONDANCE_OVERVIEW_TABLE_DESCRIPTION,
            type=VizBlockType.table,
            scope=VizBlockScope.overview,
            params={
                "variable": "tableau_médianes",
            },
        )
        db.session.add(scalar_block)
        line_chart_block = VizBlockConfig(
            id_indicator=i06_abondance.id_indicator,
            title="Évolution de la valeur de l'indicateur",
            info=I06_ABONDANCE_OVERVIEW_EVOLUTION_INFO,
            description=I06_ABONDANCE_OVERVIEW_EVOLUTION_DESCRIPTION,
            type=VizBlockType.line_chart,
            scope=VizBlockScope.overview,
            params={
                "variable": "évolution",
            },
        )
        db.session.add(line_chart_block)

    return scalar_block, line_chart_block


def install_all_test_sample_objects():
    users = install_test_users()
    protocols = get_test_protocols()
    install_test_permissions(protocols, users)
    metadata = install_metadata()
    dataset = metadata["dataset"]
    flore_site_type = get_quadrat_flore_site_type()
    flore_protocol = configure_mheo_flore_test_protocol(
        protocols["mheo_flore_test"], dataset, flore_site_type
    )
    install_test_monitoring_objects(flore_protocol, flore_site_type, users)
    install_more_fake_data(flore_protocol, flore_site_type, users)
    reference_tables = install_reference_tables()
    indicators = install_test_indicators(protocols, reference_tables)
    install_i02_abondance_visualization_config(indicators)
    install_i02_abondance_overview_visualization_config(indicators)
    install_i02_abondance_statistical_tests_visualization_config(indicators)
    install_i02_visualization_config(indicators)
    install_i02_overview_visualization_config(indicators)
    install_i06_visualization_config(indicators)
    install_i06_overview_visualization_config(indicators)
    install_i06_abondance_visualization_config(indicators)
    install_i06_abondance_overview_visualization_config(indicators)
