from geonature.utils.env import ma

from calculatrice_monitoring.models import Indicator


class IndicatorSchema(ma.SQLAlchemyAutoSchema):
    id_indicator = ma.Integer(data_key="id")

    class Meta:
        model = Indicator
        include_fk = True


class ProtocolSchema(ma.Schema):
    id_module = ma.Integer(data_key="id")
    module_label = ma.String(data_key="label")
