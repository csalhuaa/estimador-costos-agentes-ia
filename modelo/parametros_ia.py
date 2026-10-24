"""Scenario parameters and literature checks (M2)."""

from fractions import Fraction
from statistics import median

from .tipos import Aviso, Estudio, NombreEscenario, ParametrosIA, ValoresIA


def valores(par: ParametrosIA, escenario: NombreEscenario) -> ValoresIA:
    """Select the nine scenario values without modifying the input ranges."""
    reduction_field, cost_field = {
        "pesimista": ("minimo", "maximo"),
        "esperado": ("esperado", "esperado"),
        "optimista": ("maximo", "minimo"),
    }[escenario]
    return ValoresIA(
        r=getattr(par.r, reduction_field),
        rho_rev=getattr(par.rho_rev, cost_field),
        rho_retr=getattr(par.rho_retr, cost_field),
        c_api_h=getattr(par.c_api_h, cost_field),
        delta=getattr(par.delta, cost_field),
        h_def=getattr(par.h_def, cost_field),
        p_lic=getattr(par.p_lic, cost_field),
        h_cap=getattr(par.h_cap, cost_field),
        h_int=getattr(par.h_int, cost_field),
    )


def contrastar_r_con_estudios(
    par: ParametrosIA, estudios: tuple[Estudio, ...]
) -> tuple[Aviso, ...]:
    """Compare r ranges with eligible studies; warnings do not change inputs."""
    # Decimal strings keep the strict 0.005 boundary exact, including medians.
    reductions = [
        Fraction(str(study.r_equivalente))
        for study in estudios
        if study.cumple == "Si" and study.r_equivalente is not None
    ]
    warnings: list[Aviso] = []
    if reductions:
        observed = (min(reductions), median(reductions), max(reductions))
        reported = (par.r.minimo, par.r.esperado, par.r.maximo)
        if any(
            abs(Fraction(str(value)) - reference) > Fraction("0.005")
            for value, reference in zip(reported, observed)
        ):
            warnings.append(
                Aviso(
                    "A02",
                    "parametros_ia",
                    "",
                    "r no coincide con el mínimo, la mediana o el máximo de los estudios "
                    "elegibles (diferencia mayor que 0,005). Revise la hoja estudios.",
                )
            )
    if len(reductions) < 3:
        warnings.append(
            Aviso(
                "A03",
                "estudios",
                "",
                f"Hay menos de 3 estudios elegibles con r equivalente (valor: {len(reductions)}). "
                "El rango de r tiene poco respaldo.",
            )
        )
    return tuple(warnings)
