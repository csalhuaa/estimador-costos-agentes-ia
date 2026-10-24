"""Pure recorded actual-cost accounting, F9/F32/F33 (M6)."""

from .tipos import CasoValidacion, CostoReal


def calcular_costo_real(caso: CasoValidacion, t_h: float) -> CostoReal:
    """Use historical budget cash and all hours in code-producing sprints.

    Training/integration cash records third-party payments, not team labor.
    Missing included activity hours stay unknown; recorded zero stays known.
    Inputs are already validated by the caller; no scope allocation is inferred.
    """
    sprints = tuple(sprint for sprint in caso.sprints if sprint.hubo_programacion)
    budget = sum((row.costo_usd for row in caso.rubros if row.en_alcance), 0.0)
    hours = sum((sprint.horas_totales for sprint in sprints), 0.0)
    ia_cash = sum(
        (
            sprint.licencias + sprint.api + sprint.capacitacion + sprint.integracion
            for sprint in sprints
        ),
        0.0,
    )
    activity_hours = (
        None
        if any(sprint.horas_4_actividades is None for sprint in sprints)
        else sum(
            (
                sprint.horas_4_actividades
                for sprint in sprints
                if sprint.horas_4_actividades is not None
            ),
            0.0,
        )
    )
    return CostoReal(
        budget, hours * t_h + ia_cash, hours, ia_cash, activity_hours, len(sprints)
    )
