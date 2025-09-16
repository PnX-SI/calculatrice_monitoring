from flask import Blueprint, request
from flask_login import login_required
from geonature.core.gn_permissions.decorators import check_cruved_scope
from geonature.core.gn_permissions.tools import get_scopes_by_action
from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringModules
from werkzeug.datastructures import MultiDict

from calculatrice_monitoring import MODULE_CODE
from calculatrice_monitoring.models import Indicator
from calculatrice_monitoring.schemas import IndicatorSchema, ProtocolSchema

blueprint = Blueprint("calculatrice", __name__)


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
def get_protocols():
    all_modules = (
        db.session.execute(db.select(TMonitoringModules).order_by(TMonitoringModules.module_label))
        .scalars()
        .all()
    )
    modules = []
    for module in all_modules:
        scopes = get_scopes_by_action(
            module_code=module.module_code, object_code="MONITORINGS_MODULES"
        )
        if scopes["R"] > 0:
            modules.append(module)
    return ProtocolSchema().jsonify(modules, many=True)
