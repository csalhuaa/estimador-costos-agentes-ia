"""M2 public-interface tests; all records are explicitly synthetic."""

from copy import deepcopy
from dataclasses import replace

import pytest

from modelo.parametros_ia import contrastar_r_con_estudios, valores
from modelo.tipos import Estudio, ParametrosIA, Trio, ValoresIA


def trio(minimum, expected, maximum):
    return Trio(
        minimum, expected, maximum, "Supuesto declarado", (), "Synthetic fixture"
    )


def estudios(values, cumple="Si", start=1):
    return tuple(
        Estudio(
            id=f"E{index:02d}",
            autores="Synthetic fixture",
            ano="2026",
            titulo="Synthetic record, not an empirical study",
            doi_url=f"https://example.invalid/study/{index}",
            r_equivalente=value,
            cumple=cumple,
        )
        for index, value in enumerate(values, start)
    )


@pytest.fixture
def parametros():
    return ParametrosIA(
        r=trio(0.1, 0.3, 0.5),
        rho_rev=trio(0.05, 0.1, 0.2),
        rho_retr=trio(0.02, 0.05, 0.1),
        c_api_h=trio(0.1, 0.2, 0.3),
        delta=trio(0.01, 0.02, 0.04),
        h_def=trio(1, 2, 3),
        p_lic=trio(10, 20, 30),
        h_cap=trio(4, 8, 16),
        h_int=trio(2, 4, 8),
    )


@pytest.mark.parametrize(
    "scenario, expected",
    [
        ("pesimista", ValoresIA(0.1, 0.2, 0.1, 0.3, 0.04, 3, 30, 16, 8)),
        ("esperado", ValoresIA(0.3, 0.1, 0.05, 0.2, 0.02, 2, 20, 8, 4)),
        ("optimista", ValoresIA(0.5, 0.05, 0.02, 0.1, 0.01, 1, 10, 4, 2)),
    ],
)
def test_every_parameter_uses_the_correct_scenario_direction(
    parametros, scenario, expected
):
    assert valores(parametros, scenario) == expected


def test_crosscheck_uses_only_eligible_studies_with_convertible_r(parametros):
    records = (
        estudios((0.1, 0.3, 0.5))
        + estudios((0.99,), "No", 4)
        + estudios((0.8,), "Por revisar", 5)
        + estudios((None,), start=6)
    )
    assert contrastar_r_con_estudios(parametros, records) == ()


def test_zero_reduction_is_a_usable_study_value(parametros):
    p = replace(parametros, r=trio(0, 0.2, 0.4))
    assert contrastar_r_con_estudios(p, estudios((0, 0.2, 0.4))) == ()


def test_even_study_count_uses_the_median(parametros):
    p = replace(parametros, r=trio(0.1, 0.25, 0.4))
    assert contrastar_r_con_estudios(p, estudios((0.1, 0.2, 0.3, 0.4))) == ()


@pytest.mark.parametrize(
    "changed", [trio(0.106, 0.3, 0.5), trio(0.1, 0.306, 0.5), trio(0.1, 0.3, 0.506)]
)
def test_any_range_component_can_trigger_one_mismatch_warning(parametros, changed):
    warnings = contrastar_r_con_estudios(
        replace(parametros, r=changed), estudios((0.1, 0.3, 0.5))
    )
    assert len(warnings) == 1
    assert (warnings[0].codigo, warnings[0].hoja, warnings[0].celda) == (
        "A02",
        "parametros_ia",
        "",
    )
    assert "0,005" in warnings[0].mensaje


@pytest.mark.parametrize(
    "minimum, warn",
    [
        (0.105, False),
        (0.095, False),
        (0.105000000001, True),
        (0.094999999999, True),
    ],
)
def test_mismatch_threshold_is_strict_on_both_sides(parametros, minimum, warn):
    p = replace(parametros, r=trio(minimum, 0.3, 0.5))
    assert tuple(
        w.codigo for w in contrastar_r_con_estudios(p, estudios((0.1, 0.3, 0.5)))
    ) == (("A02",) if warn else ())


def test_decimal_median_does_not_create_a_false_threshold_warning(parametros):
    p = replace(parametros, r=trio(0.1, 0.145, 0.2))
    assert tuple(
        w.codigo for w in contrastar_r_con_estudios(p, estudios((0.1, 0.2)))
    ) == ("A03",)


@pytest.mark.parametrize(
    "values, bounds",
    [
        ((), (0.1, 0.3, 0.5)),
        ((0.3,), (0.3, 0.3, 0.3)),
        ((0.1, 0.5), (0.1, 0.3, 0.5)),
    ],
)
def test_fewer_than_three_usable_studies_warn_without_fabricating_data(
    parametros, values, bounds
):
    warnings = contrastar_r_con_estudios(
        replace(parametros, r=trio(*bounds)), estudios(values)
    )
    assert len(warnings) == 1
    assert (warnings[0].codigo, warnings[0].hoja, warnings[0].celda) == (
        "A03",
        "estudios",
        "",
    )
    assert f"(valor: {len(values)})" in warnings[0].mensaje


def test_mismatch_and_low_support_warnings_can_coexist(parametros):
    assert tuple(
        w.codigo for w in contrastar_r_con_estudios(parametros, estudios((0.2,)))
    ) == ("A02", "A03")


def test_m2_is_repeatable_silent_and_does_not_correct_or_mutate_inputs(
    parametros, capsys
):
    records = estudios((0.4, 0.2))
    snapshot = deepcopy((parametros, records))
    for scenario in ("pesimista", "esperado", "optimista"):
        assert valores(parametros, scenario) == valores(parametros, scenario)
    assert contrastar_r_con_estudios(parametros, records) == contrastar_r_con_estudios(
        parametros, records
    )
    assert (parametros, records) == snapshot
    assert capsys.readouterr() == ("", "")
