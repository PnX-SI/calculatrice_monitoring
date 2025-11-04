import csv
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from calculatrice_monitoring.models import Indicator
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
        add_permission(users["public"], "CALCULATRICE", "R", "ALL", scope=2)
        add_permission(users["gestionnaire"], "CALCULATRICE", "R", "ALL", scope=2)
        add_permission(
            users["gestionnaire"], "CALCULATRICE", "R", "CALCULATRICE_INDICATOR", scope=2
        )
        add_permission(users["admin"], "CALCULATRICE", "R", "CALCULATRICE_INDICATOR", scope=None)
        add_permission(
            users["gestionnaire"], "mheo_amphibiens_test", "R", "MONITORINGS_MODULES", scope=2
        )
        add_permission(
            users["gestionnaire"], "mheo_flore_test", "R", "MONITORINGS_MODULES", scope=2
        )
        add_permission(
            users["gestionnaire"], "mheo_odonate_test", "R", "MONITORINGS_MODULES", scope=2
        )
        for protocol in protocols.values():
            add_permission(
                users["admin"], protocol.module_code, "R", "MONITORINGS_MODULES", scope=None
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
            "visits": {},
            "group": group,
        }

    def get_visit(row, site):
        return {
            "date": datetime.strptime(row["date"], "%d/%m/%Y").date(),
            "observations": [],
            "site": site,
        }

    def get_observation(row, visit):
        return {"cd_nom": int(row["cd_nom"]), "abondance": row["abondance"], "visit": visit}

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
                data={"abondance": obs_data["abondance"]},
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


def install_test_indicators(protocols):
    indicators = []

    def create_indicators(indicator_names, protocol):
        with db.session.begin_nested():
            for name in indicator_names:
                indicator = Indicator(
                    name=name,
                    id_protocol=protocol.id_module,
                    description=f"This is the {name} indicator description.",
                )
                indicators.append(indicator)
                db.session.add(indicator)

    flore_protocol = protocols["mheo_flore_test"]

    create_indicators(
        indicator_names=[
            "I02 - indice floristique d'engorgement",
            "I02 - indice floristique d'engorgement (avec abondance)",
            "I06 - indice floristique de fertilité du sol",
            "I06 - indice floristique de fertilité du sol (avec abondance)",
        ],
        protocol=flore_protocol,
    )

    odonate_protocol = db.session.scalar(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "mheo_odonate_test")
    )

    create_indicators(
        indicator_names=[
            "I10 - intégrité du peuplement d’odonates",
        ],
        protocol=odonate_protocol,
    )

    return indicators


def install_i02_abondance_code(indicators):
    i02_name = "I02 - indice floristique d'engorgement (avec abondance)"
    i02_abondance = next(indic for indic in indicators if indic.name == i02_name)
    with db.session.begin_nested():
        i02_abondance.code = """
valeurs_he = get_he_prop_collection(observations.cd_nom)
abondance_perc = create_abondance_perc(observations)
moyenne = Moyenne(valeurs_he, scope="site", weights=abondance_perc)
médiane = Médiane(moyenne)
        """
        db.session.add(i02_abondance)
    return i02_abondance


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
    install_test_indicators(protocols)
