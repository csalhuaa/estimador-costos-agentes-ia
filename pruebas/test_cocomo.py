"""Published M1 examples and formula-derived variations, not case data."""

from copy import deepcopy
from dataclasses import asdict, replace

import pytest

from modelo.cocomo import estimar_base, verificar_cocomo
from modelo.constantes import NOMBRES_EM


def test_32_ksloc_reference_covers_f1_through_f8(proyecto, constantes):
    base = estimar_base(proyecto, constantes)
    # Published decimal precision; PM/month tolerance is documented in S5.
    expected = {
        "sum_sf": (18.97, 0.0001),
        "E": (1.0997, 0.0001),
        "PM_ns": (132.9109, 0.0001),
        "PM": (132.9109, 0.0001),
        "phi": (0.3179, 0.0001),
        "TDEV": (17.3712, 0.0001),
        "t_h": (6.5789, 0.0001),
        "C_trad": (132910.95, 0.01),
        "H_trad": (11919.45, 0.01),
        "T": (17.3712, 0.0001),
    }
    for field, (value, tolerance) in expected.items():
        assert getattr(base, field) == pytest.approx(value, abs=tolerance, rel=0), field


def test_100_ksloc_reference_distinguishes_total_and_reducible_hours(
    proyecto, constantes
):
    base = estimar_base(replace(proyecto, size_ksloc=100), constantes)
    assert base.PM == pytest.approx(465.3153, abs=0.0001, rel=0)
    assert base.TDEV == pytest.approx(25.873, abs=0.001, rel=0)
    assert base.PM * constantes.horas_por_pm == pytest.approx(70727.93, abs=0.01, rel=0)
    assert base.H_trad == pytest.approx(proyecto.f * 70727.92521524624)
    assert verificar_cocomo(constantes) is True


def test_size_one_uses_calibration_coefficient(proyecto, constantes):
    base = estimar_base(replace(proyecto, size_ksloc=1), constantes)
    assert base.PM_ns == base.PM == constantes.A
    assert base.C_trad == constantes.A * proyecto.c_pm
    assert base.H_trad == proyecto.f * constantes.A * constantes.horas_por_pm
    assert base.T == base.TDEV == pytest.approx(5.170974718768743)


def test_custom_duration_does_not_replace_calculated_tdev(proyecto, constantes):
    nominal = estimar_base(proyecto, constantes)
    assert estimar_base(replace(proyecto, T_meses=12), constantes) == replace(
        nominal, T=12
    )


def test_sced_effort_multiplier_does_not_change_schedule(proyecto, constantes):
    nominal = estimar_base(proyecto, constantes)
    changed = estimar_base(replace(proyecto, sced_em=1.5), constantes)
    expected = replace(
        nominal,
        PM=nominal.PM * 1.5,
        C_trad=nominal.C_trad * 1.5,
        H_trad=nominal.H_trad * 1.5,
    )
    assert asdict(changed) == pytest.approx(asdict(expected), rel=1e-12)


def test_sced_percentage_changes_only_schedule_and_default_t(proyecto, constantes):
    nominal = estimar_base(proyecto, constantes)
    changed = estimar_base(replace(proyecto, sced_pct=75), constantes)
    expected = replace(nominal, TDEV=nominal.TDEV * 0.75, T=nominal.T * 0.75)
    assert asdict(changed) == pytest.approx(asdict(expected), rel=1e-12)


@pytest.mark.parametrize("name", NOMBRES_EM)
def test_each_of_the_sixteen_effort_multipliers_is_used(name, proyecto, constantes):
    nominal = estimar_base(proyecto, constantes)
    changed = estimar_base(
        replace(proyecto, em={**proyecto.em, name: 1.25}), constantes
    )
    schedule = nominal.TDEV * 1.25**nominal.phi
    expected = replace(
        nominal,
        PM_ns=nominal.PM_ns * 1.25,
        PM=nominal.PM * 1.25,
        C_trad=nominal.C_trad * 1.25,
        H_trad=nominal.H_trad * 1.25,
        TDEV=schedule,
        T=schedule,
    )
    assert asdict(changed) == pytest.approx(asdict(expected), rel=1e-12)


@pytest.mark.parametrize("name", ("PREC", "FLEX", "RESL", "TEAM", "PMAT"))
def test_each_scale_factor_contributes_to_both_exponents(name, proyecto, constantes):
    nominal = estimar_base(proyecto, constantes)
    changed = estimar_base(
        replace(proyecto, sf={**proyecto.sf, name: proyecto.sf[name] + 1}), constantes
    )
    effort = nominal.PM * 32**0.01
    phi = nominal.phi + 0.002
    schedule = 3.67 * effort**phi
    expected = replace(
        nominal,
        sum_sf=nominal.sum_sf + 1,
        E=nominal.E + 0.01,
        PM_ns=effort,
        PM=effort,
        phi=phi,
        TDEV=schedule,
        T=schedule,
        C_trad=effort * 1000,
        H_trad=0.59 * effort * 152,
    )
    assert asdict(changed) == pytest.approx(asdict(expected), rel=1e-12)


def test_calculation_preserves_full_precision(proyecto, constantes):
    base = estimar_base(proyecto, constantes)
    assert base.PM == pytest.approx(132.91094980831903, rel=1e-14)
    assert base.TDEV == pytest.approx(17.371246090606004, rel=1e-14)
    assert base.t_h == 1000 / 152
    assert base.PM != round(base.PM, 4)
    assert base.C_trad == base.PM * proyecto.c_pm


def test_inputs_are_unchanged_and_repeated_results_are_identical(
    proyecto, constantes, capsys
):
    before = deepcopy((proyecto, constantes))
    first = estimar_base(proyecto, constantes)
    assert estimar_base(proyecto, constantes) == first
    assert verificar_cocomo(constantes) is True
    assert (proyecto, constantes) == before
    assert capsys.readouterr() == ("", "")


def test_m1_accepts_the_fractional_user_count_used_by_sensitivity(proyecto, constantes):
    assert estimar_base(replace(proyecto, n_u=8.4), constantes) == estimar_base(
        proyecto, constantes
    )


@pytest.mark.parametrize("target, expected", [(465.39, True), (465.41, False)])
def test_reference_check_uses_absolute_effort_tolerance(target, expected, constantes):
    modified = replace(constantes, A=constantes.A * target / 465.3152974687253)
    assert verificar_cocomo(modified) is expected


@pytest.mark.parametrize("target, expected", [(25.96, True), (25.98, False)])
def test_reference_check_uses_absolute_schedule_tolerance(target, expected, constantes):
    modified = replace(constantes, C=constantes.C * target / 25.873170501888215)
    assert verificar_cocomo(modified) is expected
