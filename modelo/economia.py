"""Savings, break-even and recovery, F19–F27 and F31 (M4)."""

from .adopcion import costo_adopcion
from .tipos import CostosAdopcion, EstimacionBase, ResultadoEconomico, ValoresIA


def evaluar(
    base: EstimacionBase, f: float, v: ValoresIA, ca: CostosAdopcion
) -> ResultadoEconomico:
    """Evaluate the supplied scenario without rounding or input validation."""
    C_adop = costo_adopcion(ca, base, v.r)
    bruto = base.C_trad * f * v.r
    neto = bruto - C_adop
    rbc = bruto / C_adop if C_adop != 0 else None
    r_estrella = (ca.C_fijo / base.H_trad + ca.u) / (base.t_h + ca.u)
    recuperacion = base.T / rbc if rbc is not None and rbc > 0 else None
    return ResultadoEconomico(
        C_adop=C_adop,
        ahorro_bruto=bruto,
        ahorro_neto=neto,
        rbc=rbc,
        r_estrella=r_estrella,
        umbral_global=f * r_estrella,
        c_adop_max=bruto,
        margen=v.r - r_estrella,
        recuperacion_meses=recuperacion,
        recupera_dentro_de_T=recuperacion is not None and recuperacion <= base.T,
        C_ia=base.C_trad - neto,
    )
