from geonature.utils.env import db


class Indicator(db.Model):
    __tablename__ = "t_indicators"
    __table_args__ = {"schema": "gn_calculatrice"}

    id_indicator = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False)
