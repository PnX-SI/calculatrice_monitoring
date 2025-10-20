from flask import Blueprint, abort, request
from flask_login import login_required
from flask_parameter_validation import Query, ValidateParameters
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
