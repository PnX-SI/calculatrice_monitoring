import enum

from geonature.utils.env import db
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB


class VizBlockType(enum.Enum):
    scalar = "scalaire"
    bar_chart = "barChart"


class Indicator(db.Model):
    __tablename__ = "t_indicators"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_indicator = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    id_protocol = db.Column(db.ForeignKey("gn_monitoring.t_module_complements.id_module"))
    description = db.Column(db.Unicode)
    code = db.Column(db.Unicode, nullable=False, default="")


class VizBlockConfig(db.Model):
    __tablename__ = "t_viz_block_configs"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_viz_block_config = db.Column(db.Integer, primary_key=True)
    id_indicator = db.Column(db.ForeignKey("gn_calculatrice.t_indicators.id_indicator"))
    title = db.Column(db.Unicode(100), nullable=False)
    info = db.Column(db.Unicode, nullable=False, default="")
    description = db.Column(db.Unicode, nullable=False, default="")
    type = db.Column(Enum(VizBlockType))
    params = db.Column(JSONB)
