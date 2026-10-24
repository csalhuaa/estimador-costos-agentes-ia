"""M5 rules tested with synthetic ranges, never real-case calibration."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from modelo import escenarios as module
from modelo.adopcion import costos_adopcion
from modelo.cocomo import estimar_base
from modelo.economia import evaluar
from modelo.escenarios import correr_escenarios, decidir, sensibilidad
from modelo.parametros_ia import valores
from modelo.tipos import Escenario, FilaSensibilidad, ParametrosIA, Trio

PROJECT_FIELDS = ("size_ksloc", "c_pm", "f", "n_u")
AGENT_FIELDS = (
    "r",
    "rho_rev",
    "rho_retr",
    "c_api_h",
    "delta",
    "h_def",
    "p_lic",
    "h_cap",
    "h_int",
)


def trio(minimum, expected, maximum):
    return Trio(
        minimum, expected, maximum, "Supuesto declarado", (), "Synthetic fixture"
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


def zero_costs(parameters):
    return replace(
        parameters, **{name: trio(0, 0, 0) for name in AGENT_FIELDS if name != "r"}
    )


def net_oracle(p, c, v):
    """Independent 60-digit F1–F21 arithmetic, without M1–M5 calls."""
    with localcontext() as context:
        context.prec = 60

        def d(value):
            return Decimal(str(value))

        exponent = d(c.B) + sum(map(d, p.sf.values())) / 100
        effort = d(c.A) * d(p.size_ksloc) ** exponent
        for multiplier in p.em.values():
            effort *= d(multiplier)
        duration = (
            d(c.C) * effort ** (d(c.D) + (exponent - d(c.B)) / 5) * d(p.sced_pct) / 100
        )
        total_effort = effort * d(p.sced_em)
        hourly = d(p.c_pm) / d(c.horas_por_pm)
        horizon = duration if p.T_meses is None else d(p.T_meses)
        hours = d(p.f) * total_effort * d(c.horas_por_pm)
        fixed = (
            d(p.n_u) * (d(v.p_lic) * horizon + d(v.h_cap) * hourly)
            + d(v.h_int) * hourly
        )
        unit = (
            d(v.c_api_h)
            + (d(v.rho_rev) + d(v.rho_retr) + d(v.delta) * d(v.h_def)) * hourly
        )
        return (
            total_effort * d(p.c_pm) * d(p.f) * d(v.r)
            - fixed
            - unit * hours * (1 - d(v.r))
        )


def expected_effects(p, c, par, field, percent):
    selected = valores(par, "esperado")
    reference = net_oracle(p, c, selected)
    results = []
    for factor in (1 - percent / 100, 1 + percent / 100):
        if field in PROJECT_FIELDS:
            changed_p = replace(p, **{field: getattr(p, field) * factor})
            changed_v = selected
        else:
            value = getattr(selected, field) * factor
            value = min(value, 1) if field == "r" else max(value, 0)
            changed_p = p
            changed_v = replace(selected, **{field: value})
        results.append(float(net_oracle(changed_p, c, changed_v) - reference))
    return tuple(results)


@pytest.mark.parametrize("duration", [None, 12])
def test_scenarios_preserve_order_full_results_and_one_project_baseline(
    proyecto, constantes, parametros, duration, monkeypatch
):
    project = replace(proyecto, T_meses=duration)
    base = estimar_base(project, constantes)
    original = module.estimar_base
    calls = []

    def traced(p, c):
        calls.append((p, c))
        return original(p, c)

    monkeypatch.setattr(module, "estimar_base", traced)
    actual = correr_escenarios(project, constantes, parametros)
    assert isinstance(actual, tuple)
    assert calls == [(project, constantes)]
    assert tuple(item.nombre for item in actual) == (
        "pesimista",
        "esperado",
        "optimista",
    )
    for name, item in zip(("pesimista", "esperado", "optimista"), actual):
        selected = valores(parametros, name)
        costs = costos_adopcion(base, selected, project.n_u)
        assert item == Escenario(
            name, selected, costs, evaluar(base, project.f, selected, costs)
        )
        assert item.costos.C_lic / (project.n_u * item.valores.p_lic) == pytest.approx(
            base.T
        )


@pytest.mark.parametrize("field", PROJECT_FIELDS + AGENT_FIELDS)
def test_each_parameter_changes_alone_around_expected_net_savings(
    proyecto, constantes, parametros, field
):
    rows = {
        row.parametro: row for row in sensibilidad(proyecto, constantes, parametros)
    }
    assert (rows[field].efecto_bajo, rows[field].efecto_alto) == pytest.approx(
        expected_effects(proyecto, constantes, parametros, field, 20),
        rel=1e-11,
        abs=1e-8,
    )


@pytest.mark.parametrize("percent", [5, 30, 50])
def test_custom_percentages_are_honored_for_all_thirteen_parameters(
    proyecto, constantes, parametros, percent
):
    rows = sensibilidad(proyecto, constantes, parametros, x_pct=percent)
    assert len(rows) == 13
    for row in rows:
        assert (row.efecto_bajo, row.efecto_alto) == pytest.approx(
            expected_effects(proyecto, constantes, parametros, row.parametro, percent),
            rel=1e-11,
            abs=1e-8,
        ), row.parametro


def test_sensitivity_returns_all_labels_sorted_by_maximum_absolute_effect(
    proyecto, constantes, parametros
):
    rows = sensibilidad(proyecto, constantes, parametros)
    assert isinstance(rows, tuple)
    assert len(rows) == 13
    assert all(isinstance(row, FilaSensibilidad) for row in rows)
    assert {row.parametro for row in rows} == set(PROJECT_FIELDS + AGENT_FIELDS)
    scores = [max(abs(row.efecto_bajo), abs(row.efecto_alto)) for row in rows]
    assert scores == sorted(scores, reverse=True)
    assert rows == sensibilidad(proyecto, constantes, parametros, x_pct=20)


def test_ranking_uses_the_larger_negative_impact_not_the_signed_maximum(
    proyecto, constantes, parametros
):
    base = estimar_base(proyecto, constantes)
    hours = 1.1 * base.H_trad / (proyecto.n_u * base.t_h)
    parameters = replace(
        zero_costs(parametros),
        r=trio(0, 0, 0),
        c_api_h=trio(1, 1, 1),
        h_cap=trio(hours, hours, hours),
    )
    rows = sensibilidad(proyecto, constantes, parameters)
    by_name = {row.parametro: row for row in rows}
    size, users = by_name["size_ksloc"], by_name["n_u"]
    assert size.efecto_bajo < users.efecto_bajo < abs(size.efecto_alto)
    assert rows.index(size) < rows.index(users)


def test_r_is_capped_at_one_not_at_the_original_literature_range(
    proyecto, constantes, parametros
):
    parameters = replace(parametros, r=trio(0.9, 0.95, 0.99))
    selected = valores(parameters, "esperado")
    reference = net_oracle(proyecto, constantes, selected)
    rows = {
        row.parametro: row for row in sensibilidad(proyecto, constantes, parameters)
    }
    assert (rows["r"].efecto_bajo, rows["r"].efecto_alto) == pytest.approx(
        (
            float(
                net_oracle(proyecto, constantes, replace(selected, r=0.76)) - reference
            ),
            float(net_oracle(proyecto, constantes, replace(selected, r=1)) - reference),
        ),
        rel=1e-11,
        abs=1e-8,
    )


def test_zero_cost_boundary_stays_zero_without_rounding_or_new_costs(
    proyecto, constantes, parametros
):
    rows = sensibilidad(proyecto, constantes, zero_costs(parametros), x_pct=50)
    for row in rows:
        if row.parametro in AGENT_FIELDS[1:] + ("n_u",):
            assert (row.efecto_bajo, row.efecto_alto) == (0, 0)


@pytest.mark.parametrize("users", [1, 7])
def test_user_perturbations_remain_fractional_instead_of_clipping_or_rounding(
    proyecto, constantes, parametros, users
):
    project = replace(proyecto, n_u=users)
    base = estimar_base(project, constantes)
    selected = valores(parametros, "esperado")
    per_user = selected.p_lic * base.T + selected.h_cap * base.t_h
    rows = {row.parametro: row for row in sensibilidad(project, constantes, parametros)}
    assert (rows["n_u"].efecto_bajo, rows["n_u"].efecto_alto) == pytest.approx(
        (users * 0.2 * per_user, -users * 0.2 * per_user),
        rel=1e-11,
        abs=1e-8,
    )


def test_size_sensitivity_keeps_an_explicit_horizon_while_recomputing_effort(
    proyecto, constantes, parametros
):
    project = replace(proyecto, T_meses=12)
    rows = {row.parametro: row for row in sensibilidad(project, constantes, parametros)}
    assert (
        rows["size_ksloc"].efecto_bajo,
        rows["size_ksloc"].efecto_alto,
    ) == pytest.approx(
        expected_effects(project, constantes, parametros, "size_ksloc", 20),
        rel=1e-11,
        abs=1e-8,
    )


def test_sensitivity_does_not_invent_an_extra_cap_for_f(
    proyecto, constantes, parametros
):
    project = replace(proyecto, f=0.9)
    rows = {
        row.parametro: row for row in sensibilidad(project, constantes, parametros, 50)
    }
    assert (rows["f"].efecto_bajo, rows["f"].efecto_alto) == pytest.approx(
        expected_effects(project, constantes, parametros, "f", 50),
        rel=1e-11,
        abs=1e-8,
    )


@pytest.mark.parametrize(
    "reductions, licenses, expected",
    [
        ((0.1, 0.3, 0.5), (0, 0, 0), "conviene"),
        ((0.1, 0.3, 0.5), (500, 500, 500), "no conviene"),
        ((0.1, 0.3, 0.5), (0, 100, 500), "no concluyente"),
        ((0.1, 0.3, 0.5), (0, 200, 500), "no concluyente"),
        ((0, 0.2, 0.4), (0, 0, 0), "no concluyente"),
        ((0, 0, 0), (0, 10, 20), "no concluyente"),
        ((0, 0, 0), (0, 0, 0), "no concluyente"),
    ],
)
def test_verdict_uses_strict_extreme_signs_not_the_expected_case(
    proyecto, constantes, parametros, reductions, licenses, expected
):
    parameters = replace(
        zero_costs(parametros),
        r=trio(*reductions),
        p_lic=trio(*licenses),
    )
    assert decidir(correr_escenarios(proyecto, constantes, parameters)) == expected


def test_m5_is_repeatable_silent_and_preserves_every_input(
    proyecto, constantes, parametros, capsys
):
    before = deepcopy((proyecto, constantes, parametros))
    cases = correr_escenarios(proyecto, constantes, parametros)
    rows = sensibilidad(proyecto, constantes, parametros)
    verdict = decidir(cases)
    assert correr_escenarios(proyecto, constantes, parametros) == cases
    assert sensibilidad(proyecto, constantes, parametros) == rows
    assert decidir(cases) == verdict
    assert (proyecto, constantes, parametros) == before
    assert capsys.readouterr() == ("", "")
