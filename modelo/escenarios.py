"""Pure scenario execution, sensitivity and decision, F28–F30 (M5)."""

from dataclasses import replace

from .adopcion import costos_adopcion
from .cocomo import estimar_base
from .economia import evaluar
from .parametros_ia import valores
from .tipos import (
    Constantes,
    Escenario,
    FilaSensibilidad,
    NombreEscenario,
    ParametrosIA,
    Proyecto,
    ValoresIA,
    Veredicto,
)

_NOMBRES: tuple[NombreEscenario, ...] = ("pesimista", "esperado", "optimista")
_PROYECTO = ("size_ksloc", "c_pm", "f", "n_u")
_AGENTES = (
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


def correr_escenarios(
    p: Proyecto, c: Constantes, par: ParametrosIA
) -> tuple[Escenario, ...]:
    """Run pessimistic, expected and optimistic cases using one baseline."""
    base = estimar_base(p, c)
    results = []
    for name in _NOMBRES:
        selected = valores(par, name)
        costs = costos_adopcion(base, selected, p.n_u)
        results.append(
            Escenario(name, selected, costs, evaluar(base, p.f, selected, costs))
        )
    return tuple(results)


def _ahorro_neto(p: Proyecto, c: Constantes, selected: ValoresIA) -> float:
    """Recompute all coupled quantities for one sensitivity variation."""
    base = estimar_base(p, c)
    costs = costos_adopcion(base, selected, p.n_u)
    return evaluar(base, p.f, selected, costs).ahorro_neto


def sensibilidad(
    p: Proyecto, c: Constantes, par: ParametrosIA, x_pct: float = 20.0
) -> tuple[FilaSensibilidad, ...]:
    """Return signed net-savings effects for thirteen independent changes."""
    selected = valores(par, "esperado")
    reference = _ahorro_neto(p, c, selected)
    factors = (1 - x_pct / 100, 1 + x_pct / 100)
    rows = []
    for name in _PROYECTO + _AGENTES:
        effects = []
        for factor in factors:
            if name in _PROYECTO:
                project = replace(p, **{name: getattr(p, name) * factor})
                varied = selected
            else:
                value = getattr(selected, name) * factor
                value = min(value, 1.0) if name == "r" else max(value, 0.0)
                project = p
                varied = replace(selected, **{name: value})
            effects.append(_ahorro_neto(project, c, varied) - reference)
        rows.append(FilaSensibilidad(name, *effects))
    return tuple(
        sorted(
            rows,
            key=lambda row: max(abs(row.efecto_bajo), abs(row.efecto_alto)),
            reverse=True,
        )
    )


def decidir(escenarios: tuple[Escenario, ...]) -> Veredicto:
    """Apply the strict pessimistic/optimistic net-savings rule."""
    net_by_name = {item.nombre: item.resultado.ahorro_neto for item in escenarios}
    if net_by_name["pesimista"] > 0:
        return "conviene"
    if net_by_name["optimista"] < 0:
        return "no conviene"
    return "no concluyente"
