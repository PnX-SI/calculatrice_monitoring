import enum

from geonature.utils.env import db
from gn_module_monitoring.monitoring.models import TMonitoringModules
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB


class VizBlockType(enum.Enum):
    scalar = "scalaire"
    bar_chart = "barChart"


VIZ_BLOCK_CONFIG_PARAMS = {
    VizBlockType.scalar: [
        {"name": "variable", "type": "variable"},
    ],
    VizBlockType.bar_chart: [
        {"name": "variable", "type": "variable"},
        {"name": "entity_prop", "type": "text"},
        {"name": "dataset_label", "type": "text"},
    ],
}

cor_indicator_reference_table = db.Table(
    "cor_indicator_reference_table",
    db.Column(
        "id_indicator",
        db.ForeignKey("gn_calculatrice.t_indicators.id_indicator"),
        primary_key=True,
    ),
    db.Column(
        "id_reference_table",
        db.ForeignKey("gn_calculatrice.t_reference_tables.id_reference_table"),
        primary_key=True,
    ),
    schema="gn_calculatrice",
)


class Indicator(db.Model):
    __tablename__ = "t_indicators"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_indicator = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
    id_protocol = db.Column(db.ForeignKey("gn_monitoring.t_module_complements.id_module"))
    description = db.Column(db.Unicode)
    code = db.Column(db.Unicode, nullable=False, default="")
    protocol = db.relationship(TMonitoringModules)
    reference_tables = db.relationship(
        "ReferenceTable",
        secondary=cor_indicator_reference_table,
        back_populates="indicators",
    )
    viz_block_configs = db.relationship(
        "VizBlockConfig",
        back_populates="indicator",
    )


class VizBlockConfig(db.Model):
    __tablename__ = "t_viz_block_configs"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_viz_block_config = db.Column(db.Integer, primary_key=True)
    id_indicator = db.Column(db.ForeignKey("gn_calculatrice.t_indicators.id_indicator"))
    title = db.Column(db.Unicode(100), nullable=False)
    info = db.Column(db.Unicode, nullable=False, default="")
    description = db.Column(db.Unicode, nullable=False, default="")
    type = db.Column(Enum(VizBlockType, inherit_schema=True))
    params = db.Column(JSONB)
    indicator = db.relationship(Indicator)


class ReferenceTable(db.Model):
    __tablename__ = "t_reference_tables"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_reference_table = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64), nullable=False)
    description = db.Column(db.Unicode)
    code = db.Column(db.Unicode(32), nullable=False, unique=True)
    data = db.Column(db.Text, nullable=False)
    indicators = db.relationship(
        Indicator,
        secondary=cor_indicator_reference_table,
        back_populates="reference_tables",
    )
