import pytest
from flask import url_for

from .fixtures import indicators  # noqa: F401  # We need to import fixtures so pytest can use them


def test_get_indicators_empty_list(client):
    r = client.get(url_for("calculatrice.get_indicators"))
    assert r.status_code == 200
    assert r.json == []


@pytest.mark.usefixtures("indicators")
def test_get_indicators(client):
    r = client.get(url_for("calculatrice.get_indicators"))
    assert r.status_code == 200
    expected_names = ["Indicator0", "Indicator1", "Indicator2"]
    assert [j["name"] for j in r.json] == expected_names
