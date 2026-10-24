"""Pure estimate/recorded-cost comparison, F34–F36 (M7)."""

from fractions import Fraction

from .tipos import Contraste, CostoReal, Escenario


def contrastar(
    C_trad: float,
    C_ia: float,
    cr: CostoReal,
    veredicto_por_escenarios: tuple[Escenario, ...],
    verificacion_ok: bool,
) -> Contraste:
    """Compare costs with independent accuracy, stability and verification flags.

    Positive actual cost and budget are caller preconditions (M0 validation).
    Decimal-rational ratios preserve the exact inclusive quarter threshold;
    only numeric return fields are converted to float, without money rounding.
    Exactly three strictly positive or three strictly negative savings are stable.
    """
    real = Fraction(str(cr.C_real))
    budget = Fraction(str(cr.C_presup))
    ia_error = abs(real - Fraction(str(C_ia))) / real
    cocomo_error = abs(budget - Fraction(str(C_trad))) / budget
    deviation = (real - budget) / budget
    savings = tuple(item.resultado.ahorro_neto for item in veredicto_por_escenarios)
    stable = len(savings) == 3 and (
        all(value > 0 for value in savings) or all(value < 0 for value in savings)
    )
    return Contraste(
        float(ia_error),
        float(cocomo_error),
        float(deviation),
        ia_error <= Fraction(1, 4),
        stable,
        verificacion_ok,
    )
