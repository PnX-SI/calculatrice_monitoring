import csv
import os
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
    TMonitoringVisits,
)
from pypnnomenclature.models import BibNomenclaturesTypes, TNomenclatures
from pypnusershub.db.models import Organisme, User
from shapely import Point
from sqlalchemy import select


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
        add_permission(
            users["gestionnaire"], "mheo_amphibiens_test", "R", "MONITORINGS_MODULES", scope=2
        )
        add_permission(
            users["gestionnaire"], "mheo_flore_test", "R", "MONITORINGS_MODULES", scope=2
        )
        add_permission(
            users["gestionnaire"], "mheo_odonate_test", "R", "MONITORINGS_MODULES", scope=2
        )
        for protocol in protocols:
            add_permission(
                users["admin"], protocol.module_code, "R", "MONITORINGS_MODULES", scope=None
            )


def import_data_from_csv():
    """Reads the CSV data file and returns a list of site data."""
    filename = os.path.join(Path(__file__).parent, "./mheo_data.csv")
    datafile = open(filename, newline="")
    data = csv.DictReader(datafile, delimiter=";")

    def get_site(row):
        return {
            "name": row["site_name"],
            "longitude": row["site_long"],
            "latitude": row["site_lat"],
            "visits": {},
        }

    def get_visit(row):
        return {"date": datetime.strptime(row["date"], "%d/%m/%Y").date(), "observations": []}

    def get_observation(row):
        return {"cd_nom": int(row["cd_nom"]), "abondance": row["abondance"]}

    sites = {}
    for row in data:
        site_name = row["site_name"]
        if site_name not in sites:
            sites[site_name] = get_site(row)
        site = sites[site_name]
        visit_date = row["date"]
        if visit_date not in site["visits"]:
            site["visits"][visit_date] = get_visit(row)
        visit = site["visits"][visit_date]
        visit["observations"].append(get_observation(row))

    # Convert sites and visits dicts to lists
    sites_data = sites.values()
    for site in sites_data:
        site["visits"] = site["visits"].values()

    return sites_data


def install_test_monitoring_objects(protocols, users):  # noqa: ARG001 # Leave unused param to show dependency
    sites_data = import_data_from_csv()

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

    sites = []
    with db.session.begin_nested():
        for site_data in sites_data:
            geom_4326 = from_shape(Point(site_data["longitude"], site_data["latitude"]), srid=4326)
            site = TMonitoringSites(
                base_site_name=site_data["name"],
                base_site_code=site_data["name"].replace(" ", "-").lower(),
                geom=geom_4326,
                types_site=[site_quadrat_flore_type],
            )
            sites.append(site)
            db.session.add(site)

    flore_protocol = db.session.scalar(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "mheo_flore_test")
    )

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

    visits = []
    observations = []
    for site in sites:
        for site_data in sites_data:
            if site_data["name"] == site.base_site_name:
                break
        with db.session.begin_nested():
            for visit_data in site_data["visits"]:
                visit = TMonitoringVisits(
                    id_base_site=site.id_base_site,
                    dataset=ds,
                    module=flore_protocol,
                    visit_date_min=visit_data["date"],
                )
                visits.append(visit)
                db.session.add(visit)
                db.session.commit()

                for obs_data in visit_data["observations"]:
                    observation = TMonitoringObservations(
                        id_base_visit=visit.id_base_visit,
                        cd_nom=obs_data["cd_nom"],
                        digitiser=users["gestionnaire"],
                        data={"abondance": obs_data["abondance"]},
                    )
                    observations.append(observation)
                    db.session.add(observation)

    return {
        "sites": sites,
        "visits": visits,
        "observations": observations,
    }


def install_test_indicators(protocols):  # noqa: ARG001 # Leave unused param to show dependency
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

    flore_protocol = db.session.scalar(
        select(TMonitoringModules).where(TMonitoringModules.module_code == "mheo_flore_test")
    )

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


def install_all_test_sample_objects():
    users = install_test_users()
    protocols = db.session.scalars(select(TMonitoringModules))
    install_test_permissions(protocols, users)
    install_test_monitoring_objects(protocols, users)
    install_test_indicators(protocols)
