"""Pure estimate/recorded-cost comparison, F34–F36 (M7)."""

from fractions import Fraction

from .tipos import Contraste, CostoReal


def contrastar(
    C_trad: float,
    C_ia: float,
    cr: CostoReal,
    robusta: bool,
    verificacion_ok: bool,
) -> Contraste:
    """Compare costs with independent accuracy, stability and verification flags.

    Positive actual cost and budget are caller preconditions (M0 validation).
    Decimal-rational ratios preserve the exact inclusive quarter threshold;
    only numeric return fields are converted to float, without money rounding.
    Stability transports the canonical M5 recommendation agreement unchanged.
    """
    real = Fraction(str(cr.C_real))
    budget = Fraction(str(cr.C_presup))
    ia_error = abs(real - Fraction(str(C_ia))) / real
    cocomo_error = abs(budget - Fraction(str(C_trad))) / budget
    deviation = (real - budget) / budget
    return Contraste(
        float(ia_error),
        float(cocomo_error),
        float(deviation),
        ia_error <= Fraction(1, 4),
        robusta,
        verificacion_ok,
    )
