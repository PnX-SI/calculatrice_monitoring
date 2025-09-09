import pytest
from flask import url_for

from .fixtures import indicators  # noqa: F401  # We need to import fixtures so pytest can use them


def test_get_indicators_empty_list(client):
    response = client.get(url_for("calculatrice.get_indicators"))
    assert response.status_code == 200
    assert response.json == []


@pytest.mark.usefixtures("indicators")
def test_get_indicators(client):
    response = client.get(url_for("calculatrice.get_indicators"))
    assert response.status_code == 200
    expected_names = ["Indicator0", "Indicator1", "Indicator2"]
    assert [indic["name"] for indic in response.json] == expected_names
