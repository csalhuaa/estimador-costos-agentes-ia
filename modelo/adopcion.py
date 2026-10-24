"""Fixed and variable adoption costs, F17–F19 (M3)."""

from .tipos import CostosAdopcion, EstimacionBase, ValoresIA


def costos_adopcion(base: EstimacionBase, v: ValoresIA, n_u: int) -> CostosAdopcion:
    """Calculate fixed USD costs and USD per delegated hour."""
    C_lic = n_u * v.p_lic * base.T
    C_cap = n_u * v.h_cap * base.t_h
    C_int = v.h_int * base.t_h
    return CostosAdopcion(
        C_lic=C_lic,
        C_cap=C_cap,
        C_int=C_int,
        C_fijo=C_lic + C_cap + C_int,
        u=v.c_api_h + (v.rho_rev + v.rho_retr + v.delta * v.h_def) * base.t_h,
    )


def costo_adopcion(ca: CostosAdopcion, base: EstimacionBase, r: float) -> float:
    """Calculate F19 using the remaining delegated effort."""
    return ca.C_fijo + ca.u * base.H_trad * (1 - r)
