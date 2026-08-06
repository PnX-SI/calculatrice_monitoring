# ruff: noqa: PLC2401  # (PLC2401=Function name contains a non-ASCII character)

import datetime
from decimal import Decimal

import pytest

from calculatrice_monitoring.eval import Scope, evaluate


class TestEvalIndicator:
    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_all_observations(self, eval_context):
        code = """
moyenne = gn_mean(observations.abondance)
        """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        assert len(variables["moyenne"].values) == 1
        assert variables["moyenne"].values[0].value == Decimal("1.410256410256410256410256410")

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_percentages_all_observations(self, eval_context):
        code = """
abondance_perc = gn_extract(
    ref_table=valeurs_abondance,
    origin_field="libellé_abondance",
    target_field="valeur_abondance",
    properties=observations.abondance,
)
moyenne = gn_mean(abondance_perc)
        """

        variables = evaluate(code, eval_context)

        assert "moyenne" in variables
        assert len(variables["moyenne"].values) == 1
        assert variables["moyenne"].values[0].value == Decimal("10.38461538461538461538461538")

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_abondance_per_visit_all_observations(self, eval_context):
        code = """
moyenne = gn_mean(observations.abondance, scope=Scope.VISIT)
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
valeurs_abondance = gn_extract(
    ref_table=valeurs_abondance,
    origin_field="libellé_abondance",
    target_field="valeur_abondance",
    properties=observations.abondance,
)
moyenne = gn_mean(valeurs_abondance, scope=Scope.VISIT)
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
moyenne = gn_mean(observations.abondance, scope=Scope.SITE)
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
valeurs_he = gn_extract(indices_he, "cdnom", "indice_he", observations.cd_nom)
moyenne = gn_mean(valeurs_he, scope=Scope.SITE)
médiane = gn_median(moyenne)
"""

        variables = evaluate(code, eval_context)

        assert "médiane" in variables
        médianes = variables["médiane"]
        assert médianes.scope == Scope.GLOBAL
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
valeurs_he = gn_extract(indices_he, "cdnom", "indice_he", observations.cd_nom)
abondance_perc = gn_extract(
    ref_table=valeurs_abondance,
    origin_field="libellé_abondance",
    target_field="valeur_abondance",
    properties=observations.abondance,
)
moyenne = gn_mean(valeurs_he, scope=Scope.SITE, weights=abondance_perc)
médiane = gn_median(moyenne)
"""

        variables = evaluate(code, eval_context)

        assert "médiane" in variables
        médianes = variables["médiane"]
        assert médianes.scope == Scope.GLOBAL
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

    @pytest.mark.usefixtures("monitoring_objects")
    def test_eval_code_moyenne_durée_visites(self, eval_context):
        code = """
moyenne_durée = gn_mean(visites.durée_secondes)
"""

        variables = evaluate(code, eval_context)

        assert "moyenne_durée" in variables
        moyenne_durée = variables["moyenne_durée"]
        assert moyenne_durée.scope == Scope.GLOBAL
        assert len(moyenne_durée.values) == 1
        moyenne_durée = moyenne_durée.values[0]
        assert moyenne_durée.value == 576
