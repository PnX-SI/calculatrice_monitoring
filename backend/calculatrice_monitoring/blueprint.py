from flask import Blueprint, abort, request
from flask_login import login_required
from flask_parameter_validation import Json, Query, Route, ValidateParameters
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringModules
from werkzeug.datastructures import MultiDict

from calculatrice_monitoring import MODULE_CODE
from calculatrice_monitoring.models import Indicator
from calculatrice_monitoring.schemas import IndicatorSchema, ProtocolSchema

blueprint = Blueprint("calculatrice", __name__)


@blueprint.route("/protocol/<int:protocol_id>", methods=["GET"])
@login_required
def get_protocol(protocol_id: int):
    protocol = db.get_or_404(
        TMonitoringModules, protocol_id, description=f"Protocol {protocol_id} not found"
    )
    scopes = get_scopes_by_action(
        module_code=protocol.module_code, object_code="MONITORINGS_MODULES"
    )
    if scopes["R"] == 0:
        abort(403, description=f"Missing permission to read protocol {protocol_id}")
    return ProtocolSchema().jsonify(protocol)


@blueprint.route("/indicator/<int:indicator_id>", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE, object_code="CALCULATRICE_INDICATOR")
def get_indicator(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    return IndicatorSchema().jsonify(indicator)


@blueprint.route("/indicators", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE, object_code="CALCULATRICE_INDICATOR")
def get_indicators():
    params = MultiDict(request.args)
    id_protocol_param = params.pop("id_protocol")
    try:
        id_protocol = int(id_protocol_param)
    except ValueError:
        return f"param `id_protocol` should be an integer, {id_protocol_param} received", 400
    db.get_or_404(
        TMonitoringModules, id_protocol, description=f"protocol {id_protocol} does not exist"
    )
    indicators = db.session.execute(
        db.select(Indicator).where(Indicator.id_protocol == id_protocol).order_by(Indicator.name)
    ).scalars()
    return IndicatorSchema().jsonify(indicators, many=True)


@blueprint.route("/protocols", methods=["GET"])
@login_required
@ValidateParameters()
def get_protocols(with_indicators_only: bool = Query(False)):
    """Returns the list of protocols visible to the user.

    Parameters:

    - with_indicators_only (boolean, false by default): returns only protocols with indicators
    """
    query = db.select(TMonitoringModules).order_by(TMonitoringModules.module_label)

    if with_indicators_only:
        query = query.join(Indicator).distinct()

    all_modules = db.session.execute(query).scalars().all()
    modules = []
    for module in all_modules:
        scopes = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )
        if scopes["R"] > 0:
            modules.append(module)
    return ProtocolSchema().jsonify(modules, many=True)


# The method is POST in order to pass parameters with the body. Since two parameters are
# lists of unknown size (sites IDs and campaigns) we want to avoid reaching the URL max length
# limit at some point.
@blueprint.route("/indicator/<int:indicator_id>/visualize", methods=["POST"])
@check_cruved_scope(action="R", module_code=MODULE_CODE, object_code="CALCULATRICE_INDICATOR")
@ValidateParameters()
def get_indicator_visualization(
    indicator_id: int = Route(),
    sites_ids: list[int] = Json(),  # noqa: B008  # Calling Json function for a default parameter is
    campaigns: list[dict] = Json(),  # noqa: B008  # the way flask-parameter-validation works.
    viz_type: str = Json(),  # noqa: B008
):
    if viz_type == "campaign":
        return [
            {
                "title": "Un bloc représentant un résultat scalaire",
                "info": "foobar",
                "description": f"""
<p>Aliquam varius vestibulum
ante ut tincidunt. In eu ultrices ex. Maecenas ultricies, metus eget porta tincidunt, velit
odio efficitur magna, nec aliquet erat orci sed elit. Vivamus elementum ante eget maximus
pellentesque. Aenean sit amet erat nec tortor vestibulum auctor. Mauris dapibus elit at ligula
laoreet sollicitudin. Morbi at condimentum enim.</p>
<ul>
    <li>indicator ID : {indicator_id}</li>
    <li>sites IDs : {sites_ids}</li>
    <li>campaigns : {campaigns}</li>
    <li>type : {viz_type}</li>
</ul>
<img src="https://geonature.fr/img/geonature-logo.jpg"/>
<p>Nulla facilisi. Donec vel erat placerat, iaculis mauris in, commodo metus.Mauris dapibus elit
at ligula laoree sollicitudin. Morbi at condimentum enim.</p>""",
                "type": "scalaire",
                "data": {
                    "figure": 7.9,
                },
            },
        ]
    else:
        return [
            {
                "title": "Bloc visualisation type scalaire",
                "info": """<h3>Ici des informations sur le calcul de ce résultat</h3>
<p>Pour celui-ci la valeur est statique, il n'y a pas de calcul</p>""",
                "description": f"""<h3>Description</h3>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ac tempor felis. Cras ut
blandit ipsum, rutrum blandit justo. Sed accumsan est ut consequat rhoncus. Nunc luctus rutrum
eros a suscipit.</p>
<h3>Paramètres reçus</h3>
<ul>
    <li>indicator ID : {indicator_id}</li>
    <li>sites IDs : {sites_ids}</li>
    <li>campaigns : {campaigns}</li>
    <li>type : {viz_type}</li>
</ul>
<h3>Un paragraphe avec une image</h3>
<img src="https://geonature.fr/img/geonature-logo.jpg"/>
<p>Nulla facilisi. Donec vel erat placerat, iaculis mauris in, commodo metus.</p>""",
                "type": "scalaire",
                "data": {
                    "figure": 6.2,
                },
            },
            {
                "title": "Bloc visualisation type bar chart",
                "type": "barChart",
                "info": """<h3>Ici des informations sur le calcul de ce résultat</h3>
<p>Pour celui-ci la valeur est statique, il n'y a pas de calcul</p>""",
                "description": """<h3>Description</h3>
<p>Un exemple de représentation avec un diagramme à barres. Les valeurs sont statiques.</p>""",
                "data": {
                    "labels": ["Q1", "Q2", "Q3"],
                    "datasets": [{"data": [5.5, 6.7, 4.9], "label": "Series A"}],
                },
            },
        ]
