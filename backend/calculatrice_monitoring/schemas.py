from geonature.utils.env import ma

from calculatrice_monitoring.models import (
    VIZ_BLOCK_CONFIG_PARAMS,
    Indicator,
    ReferenceTable,
    VizBlockConfig,
)


class VizBlockConfigSchema(ma.SQLAlchemyAutoSchema):
    id_viz_block_config = ma.Integer(data_key="id")
    params = ma.Method("serialize_params")

    def serialize_params(self, obj):
        param_defs = {p["name"]: p for p in VIZ_BLOCK_CONFIG_PARAMS[obj.type]}
        rv = []
        for param_name, param_value in obj.params.items():
            serialized_param = param_defs[param_name].copy()
            serialized_param["value"] = param_value
            rv.append(serialized_param)
        return rv

    class Meta:
        model = VizBlockConfig


class ReferenceTableSchema(ma.SQLAlchemyAutoSchema):
    id_reference_table = ma.Integer(data_key="id")

    class Meta:
        model = ReferenceTable


class IndicatorSchema(ma.SQLAlchemyAutoSchema):
    id_indicator = ma.Integer(data_key="id")
    id_protocol = ma.Integer(data_key="protocolId")

    class Meta:
        model = Indicator
        include_fk = True
        exclude = ["code"]


class IndicatorDetailsSchema(ma.SQLAlchemyAutoSchema):
    id_indicator = ma.Integer(data_key="id")
    protocol = ma.Nested("ProtocolSchema", data_key="protocol")
    viz_block_configs = ma.Nested(
        "VizBlockConfigSchema", many=True, data_key="visualizationBlockConfigs"
    )
    reference_tables = ma.Nested(
        "ReferenceTableSchema",
        many=True,
        only=["id_reference_table", "name", "code"],
        data_key="referenceTables",
    )

    class Meta:
        model = Indicator


class ProtocolSchema(ma.Schema):
    id_module = ma.Integer(data_key="id")
    module_label = ma.String(data_key="label")
    module_code = ma.String(data_key="code")
