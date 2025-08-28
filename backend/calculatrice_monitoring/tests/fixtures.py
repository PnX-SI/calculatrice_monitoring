import pytest
from geonature.utils.env import db

from calculatrice_monitoring.models import Indicator


@pytest.fixture()
def indicators():
    nb = 3
    indicators = []
    for i in range(nb):
        indicator = Indicator(name=f"Indicator{i}")
        db.session.add(indicator)
    db.session.commit()

    with db.session.begin_nested():
        db.session.add_all(indicators)
    return indicators
