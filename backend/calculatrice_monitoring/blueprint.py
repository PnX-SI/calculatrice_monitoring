from flask import Blueprint, abort, request
from flask_login import login_required
from flask_parameter_validation import Json, Query, Route, ValidateParameters
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringModules, TMonitoringSites
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from werkzeug.datastructures import MultiDict

from calculatrice_monitoring import MODULE_CODE
from calculatrice_monitoring.eval import visualize
from calculatrice_monitoring.models import Indicator, ReferenceTable, VizBlockConfig
from calculatrice_monitoring.schemas import (
    IndicatorAttributesSchema,
    IndicatorDetailsSchema,
    IndicatorSchema,
    ProtocolSchema,
    ReferenceTableSchema,
    VizBlockConfigSchema,
)
from calculatrice_monitoring.utils import extract_variable_names

blueprint = Blueprint("calculatrice", __name__)


def _fetch_reference_tables(reference_table_ids):
    """Returns the ReferenceTable rows matching the given ids.

    Raises a ValueError with the set of unknown ids if some are not found.
    """
    reference_tables = db.session.scalars(
        select(ReferenceTable).filter(ReferenceTable.id_reference_table.in_(reference_table_ids))
    ).all()
    missing_ids = set(reference_table_ids) - {rt.id_reference_table for rt in reference_tables}
    if missing_ids:
        raise ValueError(missing_ids)
    return reference_tables


def _validate_indicator_relations(data):
    """Validates the protocol and reference tables referenced by an indicator payload.

    `data` is mutated: `reference_table_ids` is popped out of it.
    Returns a tuple `(reference_tables, error_response)`: on failure, `reference_tables`
    is None and `error_response` is the `(body, status)` tuple to return to the client.
    """
    protocol_id = data["id_protocol"]
    try:
        db.session.scalars(
            select(TMonitoringModules).filter(TMonitoringModules.id_module == protocol_id)
        ).one()
    except NoResultFound:
        return None, ({"protocolId": [f"Protocol with ID {protocol_id} not found"]}, 400)

    reference_table_ids = data.get("reference_table_ids", [])
    try:
        reference_tables = _fetch_reference_tables(reference_table_ids)
    except ValueError as error:
        missing_ids = sorted(error.args[0])
        return None, (
            {"referenceTableIds": [f"Reference table(s) with ID {missing_ids} not found"]},
            400,
        )
    return reference_tables, None


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


@blueprint.route("/indicator", methods=["POST"])
@check_cruved_scope(action="C", module_code=MODULE_CODE, object_code="CALC_ADMIN_INDICATOR")
def create_indicator():
    try:
        data = IndicatorAttributesSchema().load(request.json)
    except ValidationError as error:
        return error.messages, 400
    reference_tables, error_response = _validate_indicator_relations(data)
    if error_response:
        return error_response
    indicator = Indicator(**data)
    indicator.reference_tables = reference_tables
    db.session.add(indicator)
    db.session.commit()
    return IndicatorSchema().jsonify(indicator), 201


@blueprint.route("/indicator/<int:indicator_id>", methods=["PUT"])
@check_cruved_scope(action="U", module_code=MODULE_CODE, object_code="CALC_ADMIN_INDICATOR")
def edit_indicator(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)

    schema = IndicatorAttributesSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as error:
        # TODO: check needed
        return error.messages, 400
    reference_tables, error_response = _validate_indicator_relations(data)
    if error_response:
        return error_response

    for field in schema.load_fields.keys():
        if field == "reference_table_ids":
            continue
        if field in data:
            setattr(indicator, field, data[field])
        else:
            column_default = getattr(Indicator, field).expression.default
            setattr(indicator, field, column_default.arg if column_default else None)
    indicator.reference_tables = reference_tables

    db.session.add(indicator)
    db.session.commit()
    return IndicatorSchema().jsonify(indicator), 200


@blueprint.route("/indicator/<int:indicator_id>/code", methods=["PUT"])
@check_cruved_scope(action="U", module_code=MODULE_CODE, object_code="CALC_ADMIN_INDICATOR")
def edit_indicator_code(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    indicator.code = request.json["code"]
    db.session.add(indicator)
    db.session.commit()
    return "", 204


@blueprint.route("/indicator/<int:indicator_id>/viz-blocks", methods=["PUT"])
@check_cruved_scope(action="U", module_code=MODULE_CODE, object_code="CALC_ADMIN_INDICATOR")
def update_indicator_viz_blocks(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    data = VizBlockConfigSchema(many=True).load(request.json)
    # Delete previous vizblock configs
    for old_vb in indicator.viz_block_configs:
        db.session.delete(old_vb)
    indicator.viz_block_configs.clear()
    # Create and attach new ones
    for vb_config in data:
        vb = VizBlockConfig(**vb_config)
        indicator.viz_block_configs.append(vb)
    db.session.add(indicator)
    db.session.commit()
    return "", 204


@blueprint.route("/indicator/<int:indicator_id>", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE)
def get_indicator(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    return IndicatorSchema().jsonify(indicator)


@blueprint.route("/indicator/<int:indicator_id>/details", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE)
def get_indicator_details(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    return IndicatorDetailsSchema().jsonify(indicator)


@blueprint.route("/indicator/<int:indicator_id>/code-variables", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE)
def get_indicator_code_variables(indicator_id: int):
    error_msg = f"Indicator {indicator_id} not found"
    indicator = db.get_or_404(Indicator, indicator_id, description=error_msg)
    variables = extract_variable_names(indicator.code)
    return variables, 200


@blueprint.route("/indicators", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE)
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
@check_cruved_scope(action="R", module_code=MODULE_CODE)
@ValidateParameters()
def get_indicator_visualization(
    indicator_id: int = Route(),
    sites_ids: list[int] = Json(),  # noqa: B008  # Calling Json function for a default parameter is
    campaigns: list[dict] = Json(),  # noqa: B008  # the way flask-parameter-validation works.
    viz_type: str = Json(),  # noqa: B008
):
    indicator = db.one_or_404(select(Indicator).filter(Indicator.id_indicator == indicator_id))
    monitoring_sites = db.session.scalars(
        select(TMonitoringSites).filter(TMonitoringSites.id_base_site.in_(sites_ids))
    )
    if viz_type == "campaign":
        return visualize(
            indicator,
            monitoring_sites,
            campaigns,
            viz_type,
        )
    else:
        # for now hard-coded vizblocks are returned for other visualization types
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


@blueprint.route("/reftables", methods=["GET"])
@check_cruved_scope(action="R", module_code=MODULE_CODE, object_code="CALC_ADMIN_INDICATOR")
def get_reference_tables():
    reftables = db.session.execute(db.select(ReferenceTable)).scalars()
    return ReferenceTableSchema().jsonify(reftables, many=True)
