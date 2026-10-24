"""M6/M7 public-interface checks; all row allocations are synthetic."""

from copy import deepcopy
from dataclasses import replace
from decimal import localcontext
from fractions import Fraction
from itertools import product

import pytest

from modelo.cocomo import estimar_base, verificar_cocomo
from modelo.escenarios import correr_escenarios, decidir
from modelo.tipos import (
    CasoValidacion,
    Contraste,
    CostoReal,
    ParametrosIA,
    Rubro,
    Sprint,
    Trio,
)


@pytest.fixture
def parametros():
    return ParametrosIA(
        *(
            Trio(value, value, value, "Supuesto declarado", (), "Synthetic fixture")
            for value in (0.3, 0, 0, 0, 0, 0, 0, 0, 0)
        )
    )


@pytest.fixture
def escenarios(proyecto, constantes, parametros):
    return correr_escenarios(proyecto, constantes, parametros)


def with_savings(escenarios, savings):
    return tuple(
        replace(item, resultado=replace(item.resultado, ahorro_neto=value))
        for item, value in zip(escenarios, savings)
    )


def assert_actual(caso, rate, expected):
    from modelo.costo_real import calcular_costo_real

    before = deepcopy((caso, rate))
    actual = calcular_costo_real(caso, rate)
    assert isinstance(actual, CostoReal)
    assert actual == expected
    assert calcular_costo_real(caso, rate) == actual
    assert (caso, rate) == before
    return actual


def assert_contrast(traditional, agent, actual, scenarios, verified, expected):
    from modelo.contraste import contrastar

    before = deepcopy((traditional, agent, actual, scenarios, verified))
    result = contrastar(
        C_trad=traditional,
        C_ia=agent,
        cr=actual,
        veredicto_por_escenarios=scenarios,
        verificacion_ok=verified,
    )
    assert isinstance(result, Contraste)
    assert result == expected
    assert all(
        type(value) is float
        for value in (
            result.err_estimacion_ia,
            result.err_cocomo_vs_presup,
            result.desviacion_presup,
        )
    )
    assert result.cumple_exactitud is expected.cumple_exactitud
    assert result.decision_estable is expected.decision_estable
    assert result.verificacion_cocomo_ok is verified
    assert contrastar(traditional, agent, actual, scenarios, verified) == result
    assert (traditional, agent, actual, scenarios, verified) == before
    return result


@pytest.mark.parametrize("budget_hours", [None, 0, 999999])
def test_recorded_budget_cash_and_all_programming_hours_are_used(budget_hours):
    case = CasoValidacion(
        (
            Rubro("Synthetic historical budget", budget_hours, 1300, True),
            Rubro("Synthetic cash-only budget", None, 200, True),
            Rubro("Excluded budget", 100000, 100000, False),
        ),
        (
            Sprint(1, None, None, 100, 40, 20, 5, 10, 15, True),
            Sprint(2, None, None, 50, 0, 10, 2, 3, 5, True),
            Sprint(3, None, None, 99999, None, 9000, 8000, 7000, 6000, False),
        ),
    )
    assert_actual(case, 10, CostoReal(1500, 1570, 150, 70, 40, 2))


@pytest.mark.parametrize(
    "category", ["licencias", "api", "capacitacion", "integracion"]
)
def test_each_ia_cash_category_is_counted_once_not_as_team_labor(category):
    sprint = Sprint(1, None, None, 12, 3, 0, 0, 0, 0, True)
    case = CasoValidacion(
        (Rubro("Synthetic budget", None, 80, True),),
        (replace(sprint, **{category: 7}),),
    )
    assert_actual(case, 5, CostoReal(80, 67, 12, 7, 3, 1))


@pytest.mark.parametrize(
    "activity_hours, expected",
    [
        ((0, 0), 0),
        ((12.5, 0), 12.5),
        ((12.5, 7.5), 20),
        ((None, 20), None),
        ((10, None), None),
        ((None, None), None),
    ],
)
def test_activity_completeness_uses_included_rows_and_zero_is_recorded(
    activity_hours, expected
):
    case = CasoValidacion(
        (Rubro("Synthetic budget", None, 120, True),),
        (
            Sprint(1, None, None, 10, activity_hours[0], 0, 0, 0, 0, True),
            Sprint(2, None, None, 20, activity_hours[1], 0, 0, 0, 0, True),
            Sprint(3, None, None, 999, None, 999, 999, 999, 999, False),
        ),
    )
    assert_actual(case, 4, CostoReal(120, 120, 30, 0, expected, 2))


def test_excluded_only_records_leave_all_totals_and_count_zero():
    case = CasoValidacion(
        (Rubro("Excluded budget", 10, 500, False),),
        (Sprint(1, None, None, 10, None, 1, 2, 3, 4, False),),
    )
    assert_actual(case, 5, CostoReal(0, 0, 0, 0, 0, 0))


@pytest.mark.parametrize(
    "budget, traditional, agent, expected",
    [
        (200, 250, 120, Contraste(0.25, 0.25, -0.2, True, True, True)),
        (200, 150, 200, Contraste(0.25, 0.25, -0.2, True, True, True)),
        (100, 100, 160, Contraste(0.0, 0.0, 0.6, True, True, True)),
        (160, 160, 160, Contraste(0.0, 0.0, 0.0, True, True, True)),
    ],
)
def test_absolute_errors_and_signed_budget_deviation(
    escenarios, budget, traditional, agent, expected
):
    assert_contrast(
        traditional,
        agent,
        CostoReal(budget, 160, 10, 10, None, 1),
        escenarios,
        True,
        expected,
    )


@pytest.mark.parametrize(
    "agent, error, accurate",
    [
        (750.075, Fraction(1, 4), True),
        (750.0750000001, Fraction(1, 4) - Fraction(1, 10001000000000), True),
        (750.0749999999, Fraction(1, 4) + Fraction(1, 10001000000000), False),
        (1250.125, Fraction(1, 4), True),
        (1250.1249999999, Fraction(1, 4) - Fraction(1, 10001000000000), True),
        (1250.1250000001, Fraction(1, 4) + Fraction(1, 10001000000000), False),
    ],
)
def test_decimal_quarter_boundary_is_exact_on_both_sides(
    escenarios, agent, error, accurate
):
    # Arithmetic must not depend on the ambient Decimal precision or an epsilon.
    with localcontext() as context:
        context.prec = 6
        assert_contrast(
            1000.1,
            agent,
            CostoReal(800.08, 1000.1, 1, 0, None, 1),
            escenarios,
            True,
            Contraste(float(error), 0.25, 0.25, accurate, True, True),
        )


@pytest.mark.parametrize(
    "savings", list(product((-1, 0, 1), repeat=3)) + [(1, 2, 3), (-3, -2, -1)]
)
def test_stability_requires_three_strictly_matching_nonzero_signs(escenarios, savings):
    stable = savings in ((1, 1, 1), (-1, -1, -1), (1, 2, 3), (-3, -2, -1))
    assert_contrast(
        100,
        100,
        CostoReal(100, 100, 1, 0, None, 1),
        with_savings(escenarios, savings),
        True,
        Contraste(0.0, 0.0, 0.0, True, stable, True),
    )


@pytest.mark.parametrize("savings", [(), (1,), (-1,), (0,), (1, 2), (-2, -1), (0, 0)])
def test_empty_or_partial_scenario_evidence_is_not_stable(escenarios, savings):
    assert_contrast(
        100,
        100,
        CostoReal(100, 100, 1, 0, None, 1),
        with_savings(escenarios, savings),
        True,
        Contraste(0.0, 0.0, 0.0, True, False, True),
    )


@pytest.mark.parametrize("verified", [False, True])
@pytest.mark.parametrize("agent, accurate", [(100, True), (50, False)])
@pytest.mark.parametrize("savings, stable", [((1, 2, 3), True), ((-1, 0, 1), False)])
def test_all_three_flags_remain_independent(
    escenarios, verified, agent, accurate, savings, stable
):
    assert_contrast(
        100,
        agent,
        CostoReal(100, 100, 1, 0, None, 1),
        with_savings(escenarios, savings),
        verified,
        Contraste(0.0 if accurate else 0.5, 0.0, 0.0, accurate, stable, verified),
    )


def test_published_aggregates_with_explicitly_synthetic_row_allocation(escenarios):
    # Only aggregate cash/hours are published; this single-row layout is invented.
    case = CasoValidacion(
        (Rubro("Synthetic allocation of published budget", None, 120000, True),),
        (Sprint(1, None, None, 19800, None, 8736.84, 0, 0, 0, True),),
    )
    real = 19800 * (1000 / 152) + 8736.84
    actual = assert_actual(
        case, 1000 / 152, CostoReal(120000, real, 19800, 8736.84, None, 1)
    )
    decimal_real = Fraction(str(real))
    result = assert_contrast(
        132910.95,
        135935.68,
        actual,
        escenarios,
        True,
        Contraste(
            float((decimal_real - Fraction("135935.68")) / decimal_real),
            0.10759125,
            float((decimal_real - 120000) / 120000),
            True,
            True,
            True,
        ),
    )
    # The published total is a display, not a rounded return value.
    assert real != 139000
    assert f"{real:.2f}" == "139000.00"
    assert tuple(
        f"{value:.4f}"
        for value in (
            result.err_estimacion_ia,
            result.err_cocomo_vs_presup,
            result.desviacion_presup,
        )
    ) == ("0.0220", "0.1076", "0.1583")


def test_public_chain_is_silent_repeatable_and_preserves_upstream_inputs(
    proyecto, constantes, parametros, capsys
):
    project = replace(proyecto, size_ksloc=1, c_pm=1520, T_meses=2, n_u=2)
    before = deepcopy((project, constantes, parametros))
    base = estimar_base(project, constantes)
    scenarios = correr_escenarios(project, constantes, parametros)
    case = CasoValidacion(
        (Rubro("Synthetic budget", None, 1300, True),),
        (
            Sprint(1, None, None, 100, None, 20, 5, 10, 15, True),
            Sprint(2, None, None, 50, None, 10, 0, 0, 0, True),
        ),
    )
    actual = assert_actual(case, base.t_h, CostoReal(1300, 1560, 150, 60, None, 2))
    expected_agent = scenarios[1].resultado.C_ia
    result = assert_contrast(
        base.C_trad,
        expected_agent,
        actual,
        scenarios,
        verificar_cocomo(constantes),
        Contraste(
            float(abs(Fraction(1560) - Fraction(str(expected_agent))) / 1560),
            float(abs(Fraction(1300) - Fraction(str(base.C_trad))) / 1300),
            0.2,
            False,
            True,
            True,
        ),
    )
    assert result.desviacion_presup == 0.2
    assert estimar_base(project, constantes) == base
    assert correr_escenarios(project, constantes, parametros) == scenarios
    assert (project, constantes, parametros) == before
    assert capsys.readouterr() == ("", "")


def test_m5_equilibrium_verdict_is_preserved_but_m7_zero_is_not_stable(
    proyecto, constantes, parametros
):
    parameters = replace(
        parametros, r=replace(parametros.r, minimo=0, esperado=0, maximo=0)
    )
    before = deepcopy((proyecto, constantes, parameters))
    scenarios = correr_escenarios(proyecto, constantes, parameters)
    assert decidir(scenarios) == "no concluyente"
    assert_contrast(
        100,
        100,
        CostoReal(100, 100, 1, 0, None, 1),
        scenarios,
        True,
        Contraste(0.0, 0.0, 0.0, True, False, True),
    )
    assert (proyecto, constantes, parameters) == before
