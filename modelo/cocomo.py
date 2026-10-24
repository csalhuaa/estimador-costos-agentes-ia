"""Pure COCOMO II.2000 Post-Architecture calculations (M1)."""

from math import isclose, prod

from .constantes import NOMBRES_EM
from .tipos import Constantes, EstimacionBase, Proyecto


def estimar_base(p: Proyecto, c: Constantes) -> EstimacionBase:
    """Calculate F1–F8 from already validated inputs, without rounding."""
    sum_sf = sum(p.sf.values())
    E = c.B + 0.01 * sum_sf
    PM_ns = c.A * p.size_ksloc**E * prod(p.em.values())
    PM = PM_ns * p.sced_em
    phi = c.D + 0.2 * (E - c.B)
    TDEV = c.C * PM_ns**phi * p.sced_pct / 100
    return EstimacionBase(
        sum_sf=sum_sf,
        E=E,
        PM_ns=PM_ns,
        PM=PM,
        phi=phi,
        TDEV=TDEV,
        t_h=p.c_pm / c.horas_por_pm,
        C_trad=PM * p.c_pm,
        H_trad=p.f * PM * c.horas_por_pm,
        T=p.T_meses if p.T_meses is not None else TDEV,
    )


def verificar_cocomo(c: Constantes) -> bool:
    """Check the nominal 100-KSLOC reference using absolute tolerance 0.1."""
    # Salary, f and users do not affect the two reference quantities.
    nominal = Proyecto(
        nombre="100 KSLOC nominal verification",
        moneda="USD",
        size_ksloc=100,
        sf=dict(c.sf_nominal),
        em=dict.fromkeys(NOMBRES_EM, c.em_nominal),
        sced_em=c.em_nominal,
        sced_pct=c.sced_pct_nominal,
        c_pm=1,
        f=0.59,
        T_meses=None,
        n_u=1,
    )
    base = estimar_base(nominal, c)
    return isclose(base.PM, 465.3, abs_tol=0.1, rel_tol=0) and isclose(
        base.TDEV, 25.87, abs_tol=0.1, rel_tol=0
    )
