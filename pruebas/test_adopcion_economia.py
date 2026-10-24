"""Synthetic economic fixtures, not a reconstruction of missing case inputs."""

from copy import deepcopy
from dataclasses import asdict, replace
from decimal import Decimal, localcontext

import pytest

from modelo.adopcion import costo_adopcion, costos_adopcion
from modelo.economia import evaluar
from modelo.tipos import EstimacionBase, ValoresIA


@pytest.fixture
def base():
    return EstimacionBase(
        sum_sf=18.97,
        E=1.0997,
        PM_ns=10,
        PM=10,
        phi=0.31794,
        TDEV=3.67 * 10**0.31794,
        t_h=10,
        C_trad=15200,
        H_trad=760,
        T=2,
    )


@pytest.fixture
def v():
    return ValoresIA(
        r=0.3,
        rho_rev=0.1,
        rho_retr=0.05,
        c_api_h=0.2,
        delta=0.02,
        h_def=2,
        p_lic=20,
        h_cap=8,
        h_int=4,
    )


def test_fixed_and_per_hour_costs_follow_f17_and_f18(base, v):
    assert asdict(costos_adopcion(base, v, 2)) == pytest.approx(
        {
            "C_lic": 80,
            "C_cap": 160,
            "C_int": 40,
            "C_fijo": 280,
            "u": 2.1,
        },
        rel=1e-14,
    )


def test_total_adoption_uses_remaining_delegated_hours(base, v):
    assert costo_adopcion(costos_adopcion(base, v, 2), base, v.r) == pytest.approx(
        1397.2
    )


def test_licenses_use_supplied_t_without_rescaling_training_or_integration(base, v):
    changed = costos_adopcion(replace(base, T=4), v, 2)
    nominal = costos_adopcion(base, v, 2)
    assert asdict(changed) == pytest.approx(
        asdict(replace(nominal, C_lic=160, C_fijo=360))
    )


def test_fractional_users_scale_licenses_and_training_but_not_total_integration(
    base, v
):
    assert asdict(costos_adopcion(base, v, 8.4)) == pytest.approx(
        {
            "C_lic": 336,
            "C_cap": 672,
            "C_int": 40,
            "C_fijo": 1048,
            "u": 2.1,
        }
    )


def test_all_economic_fields_match_the_synthetic_fixture(base, v):
    result = evaluar(base, 0.5, v, costos_adopcion(base, v, 2))
    threshold = 469 / 2299
    assert result.recupera_dentro_de_T is True
    numeric = asdict(result)
    numeric.pop("recupera_dentro_de_T")
    assert numeric == pytest.approx(
        {
            "C_adop": 1397.2,
            "ahorro_bruto": 2280,
            "ahorro_neto": 882.8,
            "rbc": 2280 / 1397.2,
            "r_estrella": threshold,
            "umbral_global": 0.5 * threshold,
            "c_adop_max": 2280,
            "margen": 0.3 - threshold,
            "recuperacion_meses": 2 * 1397.2 / 2280,
            "C_ia": 14317.2,
        },
        rel=1e-13,
    )


def test_zero_savings_has_no_positive_payback(base, v):
    result = evaluar(base, 0.5, replace(v, r=0), costos_adopcion(base, v, 2))
    assert result.C_adop == pytest.approx(1876)
    assert result.ahorro_bruto == result.rbc == 0
    assert result.ahorro_neto == -result.C_adop
    assert result.recuperacion_meses is None
    assert result.recupera_dentro_de_T is False
    assert result.C_ia == pytest.approx(17076)


@pytest.mark.parametrize("r", [0, 0.3, 1])
def test_zero_adoption_cost_returns_none_ratios_instead_of_infinity(base, r):
    values = ValoresIA(r, 0, 0, 0, 0, 0, 0, 0, 0)
    result = evaluar(base, 0.5, values, costos_adopcion(base, values, 2))
    assert result.C_adop == 0
    assert result.rbc is result.recuperacion_meses is None
    assert result.recupera_dentro_de_T is False
    assert result.r_estrella == result.umbral_global == 0
    assert result.margen == r
    assert result.ahorro_bruto == result.ahorro_neto == result.c_adop_max == 7600 * r
    assert result.C_ia == 15200 - 7600 * r


def test_full_savings_removes_variable_costs_but_keeps_fixed_adoption(base, v):
    result = evaluar(base, 0.5, replace(v, r=1), costos_adopcion(base, v, 2))
    assert result.C_adop == 280
    assert result.ahorro_bruto == 7600
    assert result.ahorro_neto == 7320
    assert result.C_ia == 7880


def test_unachievable_break_even_is_reported_above_one(base):
    values = ValoresIA(0.3, 0, 0, 0, 0, 0, 2500, 0, 0)
    result = evaluar(base, 0.5, values, costos_adopcion(base, values, 2))
    assert result.r_estrella == pytest.approx(10000 / 7600)
    assert result.r_estrella > 1
    assert result.margen < 0
    assert result.ahorro_neto == -7720
    assert result.recuperacion_meses > base.T
    assert result.recupera_dentro_de_T is False


def test_recovery_exactly_at_t_counts_as_within_t(base):
    values = ValoresIA(0.3, 0, 0, 0, 0, 0, 570, 0, 0)
    result = evaluar(base, 0.5, values, costos_adopcion(base, values, 2))
    assert result.ahorro_neto == 0
    assert result.rbc == 1
    assert result.recuperacion_meses == base.T
    assert result.recupera_dentro_de_T is True


def test_adoption_and_economics_preserve_precision_against_decimal_oracle(base, v):
    values = replace(v, r=0.3123456789, p_lic=19.123456, rho_rev=0.123456789)
    with localcontext() as context:
        context.prec = 50
        r = Decimal(".3123456789")
        fixed = Decimal("19.123456") * 2 * 2 + 160 + 40
        unit = (
            Decimal(".2")
            + (Decimal(".123456789") + Decimal(".05") + Decimal(".02") * 2) * 10
        )
        adoption = fixed + unit * 760 * (1 - r)
        gross = Decimal("15200") * Decimal(".5") * r
        net = gross - adoption
        threshold = (fixed / 760 + unit) / (10 + unit)
        expected = {
            "C_adop": adoption,
            "ahorro_bruto": gross,
            "ahorro_neto": net,
            "rbc": gross / adoption,
            "r_estrella": threshold,
            "umbral_global": threshold / 2,
            "c_adop_max": gross,
            "margen": r - threshold,
            "recuperacion_meses": 2 * adoption / gross,
            "C_ia": 15200 - net,
        }
    costs = costos_adopcion(base, values, 2)
    result = evaluar(base, 0.5, values, costs)
    for field, expected_value in expected.items():
        assert getattr(result, field) == pytest.approx(
            float(expected_value), rel=1e-13
        ), field
    assert result.ahorro_neto != round(result.ahorro_neto, 2)
    assert costs.C_fijo == pytest.approx(float(fixed), rel=1e-14)
    assert costs.u == pytest.approx(float(unit), rel=1e-14)


def test_m3_m4_are_repeatable_silent_and_do_not_mutate_inputs(base, v, capsys):
    snapshot = deepcopy((base, v))
    costs = costos_adopcion(base, v, 2)
    original_costs = deepcopy(costs)
    first = evaluar(base, 0.5, v, costs)
    assert costos_adopcion(base, v, 2) == costs
    assert evaluar(base, 0.5, v, costs) == first
    assert (base, v, costs) == (*snapshot, original_costs)
    assert capsys.readouterr() == ("", "")
