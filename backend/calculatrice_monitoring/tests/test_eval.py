# ruff: noqa: PLC2401  # (PLC2401=Function name contains a non-ASCII character)

import datetime
from decimal import Decimal

import pytest

from calculatrice_monitoring.eval import (
    Scope,
    VisualizationConfigError,
    evaluate,
    format_numbers,
    prepare_table_vizblock_data,
)
from calculatrice_monitoring.models import VizBlockConfig


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


class TestCreateTableVizBlock:
    def test_with_headers_and_rows_format(self):
        params = {"variable": "foo"}
        variables = {
            "foo": {
                "headers": ["", "1st column", "2nd column"],
                "rows": [["Item 1", 1, 11], ["Item 2", 2, 22]],
            }
        }
        vizblock_config = VizBlockConfig(params=params)
        data = prepare_table_vizblock_data(vizblock_config, variables)

        assert data == {
            "headers": ["", "1st column", "2nd column"],
            "rows": [["Item 1", 1, 11], ["Item 2", 2, 22]],
        }

    def test_with_datasets_and_labels_format(self):
        params = {"variable": "foo"}
        variables = {
            "foo": {
                "labels": ["Item 1", "Item 2"],
                "datasets": [
                    {"label": "1st column", "data": [1, 2]},
                    {"label": "2nd column", "data": [11, 22]},
                ],
            }
        }
        vizblock_config = VizBlockConfig(params=params)
        data = prepare_table_vizblock_data(vizblock_config, variables)

        assert data == {
            "headers": ["", "1st column", "2nd column"],
            "rows": [
                ["Item 1", Decimal("1"), Decimal("11")],
                ["Item 2", Decimal("2"), Decimal("22")],
            ],
        }

    def test_format_error(self):
        params = {"variable": "foo"}
        variables = {"foo": {"bad": "format"}}
        vizblock_config = VizBlockConfig(params=params)

        with pytest.raises(VisualizationConfigError):
            prepare_table_vizblock_data(vizblock_config, variables)


class TestFormatNumbers:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (Decimal("3.14159"), Decimal("3.14")),
            (Decimal("2.5"), Decimal("2.50")),
            (Decimal("0.005"), Decimal("0.01")),
            (Decimal("1.999"), Decimal("2.00")),
            (Decimal("-1.235"), Decimal("-1.24")),
            (Decimal("0"), Decimal("0.00")),
            (0.5, Decimal("0.50")),
            (0.1 + 0.2, Decimal("0.30")),
            (1234.5678, Decimal("1234.57")),
        ],
    )
    def test_rounds_to_two_decimal_places(self, value, expected):
        result = format_numbers(value)

        assert isinstance(result, Decimal)
        assert result == expected
        assert result.as_tuple().exponent == -2

    @pytest.mark.parametrize(
        "value",
        [42, 0, True, "abc", "3.14159", "", None, datetime.date(2024, 1, 1)],
    )
    def test_leaves_other_types_untouched(self, value):
        result = format_numbers(value)

        assert result == value
        assert type(result) is type(value)

    @pytest.mark.parametrize(
        "value", [Decimal("NaN"), Decimal("Infinity"), float("inf"), float("-inf")]
    )
    def test_leaves_non_finite_numbers_untouched(self, value):
        assert format_numbers(value) is value

    def test_float_nan_untouched(self):
        result = format_numbers(float("nan"))

        assert isinstance(result, float)
        assert result != result

    def test_list(self):
        assert format_numbers([Decimal("1.234"), 2, "x", 0.456]) == [
            Decimal("1.23"),
            2,
            "x",
            Decimal("0.46"),
        ]

    def test_tuple(self):
        result = format_numbers((Decimal("1.234"), 2))

        assert isinstance(result, tuple)
        assert result == (Decimal("1.23"), 2)

    def test_dict_keeps_keys(self):
        assert format_numbers({"a": Decimal("1.234"), "b": 2, "c": "x"}) == {
            "a": Decimal("1.23"),
            "b": 2,
            "c": "x",
        }

    def test_empty_containers(self):
        assert format_numbers({}) == {}
        assert format_numbers([]) == []

    def test_nested_dicts_and_lists(self):
        data = {
            "labels": ["A", "B"],
            "datasets": [
                {"label": "x", "data": [Decimal("12.345"), 0.5, 7]},
                {"label": "y", "data": [[Decimal("1.999")], {"deep": [Decimal("0.001")]}]},
            ],
            "rows": [["A", Decimal("1.999"), None]],
        }

        assert format_numbers(data) == {
            "labels": ["A", "B"],
            "datasets": [
                {"label": "x", "data": [Decimal("12.35"), Decimal("0.50"), 7]},
                {"label": "y", "data": [[Decimal("2.00")], {"deep": [Decimal("0.00")]}]},
            ],
            "rows": [["A", Decimal("2.00"), None]],
        }

    def test_does_not_mutate_input(self):
        data = {"a": [Decimal("1.234"), {"b": 0.456}]}

        format_numbers(data)

        assert data == {"a": [Decimal("1.234"), {"b": 0.456}]}
