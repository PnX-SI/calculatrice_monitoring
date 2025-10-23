# ruff: noqa: PLC2401  # (PLC2401=Function name contains a non-ASCII character)

import datetime
from decimal import Decimal

import pytest

from calculatrice_monitoring.eval import evaluate

from .fixtures import (
    eval_context,
    monitoring_objects,
    # FIXME: is there a way no to import those "unused" fixtures
    protocols,
    users,
)


class TestEvalIndicator:
    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_all_observations(self, eval_context):
        code = """
moyenne = Moyenne(observations.abondance)
        """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        assert len(variables["moyenne"].values) == 1
        assert variables["moyenne"].values[0].value == 1.4102564102564104

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_percentages_all_observations(self, eval_context):
        code = """
moyenne = Moyenne(create_abondance_perc(observations))
        """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        assert len(variables["moyenne"].values) == 1
        assert variables["moyenne"].values[0].value == 10.333333333333334

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_per_visit_all_observations(self, eval_context):
        code = """
moyenne = Moyenne(observations.abondance, scope="visit")
            """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        properties = variables["moyenne"].values
        labels = [prop.entity.visit_date_min for prop in properties]
        assert labels == [datetime.date(2023, 5, 22)] * 5
        values = [prop.value for prop in properties]
        expected_values = [
            Decimal(1.3333333333333333),
            Decimal(3),
            Decimal(1.3571428571428571),
            Decimal(1),
            Decimal(1.3571428571428571),
        ]
        assert values == pytest.approx(expected_values)

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_percentages_per_visit_all_observations(self, eval_context):
        code = """
moyenne = Moyenne(create_abondance_perc(observations), scope="visit")
            """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        properties = variables["moyenne"].values
        labels = [prop.entity.visit_date_min for prop in properties]
        assert labels == [datetime.date(2023, 5, 22)] * 5
        values = [prop.value for prop in properties]
        expected_values = [
            Decimal("7"),
            Decimal("41.25"),
            Decimal("10.07142857142857142857142857"),
            Decimal("3"),
            Decimal("9.321428571428571428571428571"),
        ]
        assert values == pytest.approx(expected_values)

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_per_site_all_observations(self, eval_context):
        code = """
moyenne = Moyenne(observations.abondance, scope="site")
                """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        properties = variables["moyenne"].values
        labels = [prop.entity.base_site_name for prop in properties]
        expected_labels = [
            "Transect 1 Quadrat 1",
            "Transect 1 Quadrat 2",
            "Transect 1 Quadrat 3",
            "Transect 2 Quadrat 4",
            "Transect 2 Quadrat 5",
        ]
        assert labels == expected_labels
        values = [prop.value for prop in properties]
        expected_values = [
            Decimal("1.333333333333333333333333333"),
            Decimal("3"),
            Decimal("1.357142857142857142857142857"),
            Decimal("1"),
            Decimal("1.357142857142857142857142857"),
        ]
        assert values == pytest.approx(expected_values)

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_he_per_site_and_médiane_all_observations(self, eval_context):
        code = """
valeurs_he = get_he_prop_collection(observations.cd_nom)
moyenne = Moyenne(valeurs_he, scope="site")
médiane = Médiane(moyenne)
"""

        variables = evaluate(code, eval_context)

        assert "médiane" in variables
        médianes = variables["médiane"]
        assert médianes.scope == "global"
        assert len(médianes.values) == 1
        médiane = médianes.values[0]
        assert médiane.value == 6.5

        assert "moyenne" in variables
        properties = variables["moyenne"].values
        labels = [prop.entity.base_site_name for prop in properties]
        expected_labels = [
            "Transect 1 Quadrat 1",
            "Transect 1 Quadrat 2",
            "Transect 1 Quadrat 3",
            "Transect 2 Quadrat 4",
            "Transect 2 Quadrat 5",
        ]
        assert labels == expected_labels
        values = [prop.value for prop in properties]
        expected_values = [
            Decimal("7.833333333333333333333333333"),
            Decimal("7.5"),
            Decimal("5.769230769230769230769230769"),
            Decimal("6.5"),
            Decimal("6"),
        ]
        assert values == pytest.approx(expected_values)

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_he_pondérée_abondance_per_site_and_médiane_all_observations(
        self, eval_context
    ):
        code = """
valeurs_he = get_he_prop_collection(observations.cd_nom)
abondance_perc = create_abondance_perc(observations)
moyenne = Moyenne(valeurs_he, scope="site", weights=abondance_perc)
médiane = Médiane(moyenne)
"""

        variables = evaluate(code, eval_context)

        assert "médiane" in variables
        médianes = variables["médiane"]
        assert médianes.scope == "global"
        assert len(médianes.values) == 1
        médiane = médianes.values[0]
        assert médiane.value == 6.5

        assert "moyenne" in variables
        properties = variables["moyenne"].values
        labels = [prop.entity.base_site_name for prop in properties]
        expected_labels = [
            "Transect 1 Quadrat 1",
            "Transect 1 Quadrat 2",
            "Transect 1 Quadrat 3",
            "Transect 2 Quadrat 4",
            "Transect 2 Quadrat 5",
        ]
        assert labels == expected_labels
        values = [prop.value for prop in properties]
        expected_values = [
            Decimal("8.785714285714285714285714286"),
            Decimal("7.181818181818181818181818182"),
            Decimal("5.684782608695652173913043478"),
            Decimal("6.5"),
            Decimal("5.4"),
        ]
        assert values == pytest.approx(expected_values)
