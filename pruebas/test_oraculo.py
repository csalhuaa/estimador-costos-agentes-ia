"""Independent verifier's log-space oracle, retained as a regression test."""

from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from modelo.cocomo import estimar_base


@pytest.mark.parametrize("custom_calibration", [False, True])
def test_combined_inputs_match_a_high_precision_log_space_oracle(
    proyecto, constantes, custom_calibration
):
    # Synthetic combined nonnominal case; no estimates from real project data.
    p = replace(
        proyecto,
        size_ksloc=13.75,
        sf=dict(zip(proyecto.sf, (2.48, 2.03, 2.83, 2.19, 3.12))),
        em={name: 1.01 + index / 100 for index, name in enumerate(proyecto.em)},
        sced_em=1.43,
        sced_pct=75,
        c_pm=2345.67,
        f=0.37123,
        T_meses=12,
        n_u=8.4,
    )
    c = constantes
    if custom_calibration:
        c = replace(c, A=3.12, B=0.95, C=3.2, D=0.31, horas_por_pm=160)

    with localcontext() as context:
        context.prec = 60

        def decimal(value):
            return Decimal(str(value))

        scale = sum(map(decimal, p.sf.values()))
        exponent = decimal(c.B) + scale / 100
        log_effort = decimal(c.A).ln() + exponent * decimal(p.size_ksloc).ln()
        log_effort += sum(decimal(value).ln() for value in p.em.values())
        effort = log_effort.exp()
        phi = decimal(c.D) + scale / 500
        duration = (decimal(c.C).ln() + phi * log_effort).exp()
        duration *= decimal(p.sced_pct) / 100
        total_effort = effort * decimal(p.sced_em)
        expected = {
            "sum_sf": scale,
            "E": exponent,
            "PM_ns": effort,
            "PM": total_effort,
            "phi": phi,
            "TDEV": duration,
            "t_h": decimal(p.c_pm) / decimal(c.horas_por_pm),
            "C_trad": total_effort * decimal(p.c_pm),
            "H_trad": total_effort * decimal(p.f) * decimal(c.horas_por_pm),
            "T": decimal(p.T_meses),
        }

    actual = estimar_base(p, c)
    for name, value in expected.items():
        assert getattr(actual, name) == pytest.approx(float(value), rel=2e-13), name
