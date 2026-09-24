from geonature.utils.env import ma
from marshmallow import post_load, validate

from calculatrice_monitoring.models import (
    VIZ_BLOCK_CONFIG_PARAMS,
    Indicator,
    ReferenceTable,
    VizBlockConfig,
)

# A reference table's code must look like a Python variable name: it must start with a
# letter and may only contain letters, digits and underscores (no spaces or other characters).
REFERENCE_TABLE_CODE_REGEXP = r"^[A-Za-z][A-Za-z0-9_]*$"

# Maps the encoding names exposed to the frontend to the actual Python codec names.
REFERENCE_TABLE_ENCODINGS = {
    "utf-8": "utf-8",
    "latin-1": "iso-8859-1",
}

REFERENCE_TABLE_SEPARATORS = [",", ";"]


def _prepare_file_options(data):
    """Gather the file-decoding options for easier removal out of a loaded reference table payload.

    These options are never persisted on the ReferenceTable model: they are only used to decode
    and normalize the uploaded file before storing its content.
    """
    data["file_options"] = {
        "encoding": data.pop("encoding"),
        "separator": data.pop("separator"),
    }
    return data


class VizBlockConfigSchema(ma.SQLAlchemyAutoSchema):
    id_viz_block_config = ma.Integer(data_key="id")
    # Mandatory to declare the 'type' field due to this issue with marshmallow-sqlalchemy package:
    # https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/673
    type = ma.auto_field(validate=[])
    params = ma.Method(serialize="serialize_params", deserialize="deserialize_params")

    def serialize_params(self, obj):
        param_defs = {p["name"]: p for p in VIZ_BLOCK_CONFIG_PARAMS[obj.type]}
        rv = []
        for param_name, param_value in obj.params.items():
            serialized_param = param_defs[param_name].copy()
            serialized_param["value"] = param_value
            rv.append(serialized_param)
        return rv

    def deserialize_params(self, value):
        # TODO: add validation on params depending on the VizBlock's type
        return value

    class Meta:
        model = VizBlockConfig


class ReferenceTableSchema(ma.SQLAlchemyAutoSchema):
    id_reference_table = ma.Integer(data_key="id")

    class Meta:
        model = ReferenceTable
        exclude = ["data"]


class ReferenceTableCreationSchema(ma.SQLAlchemyAutoSchema):
    code = ma.auto_field(
        validate=validate.Regexp(
            REFERENCE_TABLE_CODE_REGEXP,
            error=(
                "Code must start with a letter and only contain letters, digits and underscores"
            ),
        )
    )
    encoding = ma.String(required=True, validate=validate.OneOf(REFERENCE_TABLE_ENCODINGS.keys()))
    separator = ma.String(required=True, validate=validate.OneOf(REFERENCE_TABLE_SEPARATORS))

    class Meta:
        model = ReferenceTable
        dump_only = ["id_reference_table", "data", "active"]

    @post_load
    def prepare_file_options(self, data, **kwargs):  # noqa: ARG002  # Unused method argument: `kwargs`
        return _prepare_file_options(data)


class ReferenceTableEditSchema(ma.SQLAlchemyAutoSchema):
    encoding = ma.String(required=True, validate=validate.OneOf(REFERENCE_TABLE_ENCODINGS.keys()))
    separator = ma.String(required=True, validate=validate.OneOf(REFERENCE_TABLE_SEPARATORS))

    class Meta:
        model = ReferenceTable
        dump_only = ["id_reference_table", "code", "data", "active"]

    @post_load
    def prepare_file_options(self, data, **kwargs):  # noqa: ARG002  # Unused method argument: `kwargs`
        return _prepare_file_options(data)


class IndicatorSchema(ma.SQLAlchemyAutoSchema):
    id_indicator = ma.Integer(data_key="id")
    id_protocol = ma.Integer(data_key="protocolId")

    class Meta:
        model = Indicator
        include_fk = True
        exclude = ["code"]


class IndicatorAttributesSchema(ma.SQLAlchemyAutoSchema):
    """Schema used to validate the payload when creating an indicator.

    Only the basic attributes of an indicator can be set on creation.
    """

    name = ma.String(required=True)
    id_protocol = ma.Integer(required=True, data_key="protocolId")
    description = ma.String(required=False)
    reference_table_ids = ma.List(ma.Integer(), required=False, data_key="referenceTableIds")

    class Meta:
        model = Indicator
        include_fk = True
        fields = ("name", "description", "id_protocol", "reference_table_ids")


class IndicatorDetailsSchema(ma.SQLAlchemyAutoSchema):
    id_indicator = ma.Integer(data_key="id")
    protocol = ma.Nested("ProtocolSchema", data_key="protocol")
    viz_block_configs = ma.Nested(
        "VizBlockConfigSchema", many=True, data_key="visualizationBlockConfigs"
    )
    reference_tables = ma.Nested(
        "ReferenceTableSchema",
        many=True,
        only=["id_reference_table", "name", "code", "description"],
        data_key="referenceTables",
    )

    class Meta:
        model = Indicator


class ProtocolSchema(ma.Schema):
    id_module = ma.Integer(data_key="id")
    module_label = ma.String(data_key="label")
    module_code = ma.String(data_key="code")
