from geonature.utils.env import ma

from calculatrice_monitoring.models import Indicator


class IndicatorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Indicator
        include_fk = True
