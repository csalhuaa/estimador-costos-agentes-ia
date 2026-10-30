"""Pipeline: coordinates the execution order across modules M0 through M7."""

from dataclasses import replace
from datetime import date
from pathlib import Path

from .carga import cargar_entradas
from .cocomo import estimar_base, verificar_cocomo
from .contraste import contrastar
from .costo_real import calcular_costo_real
from .escenarios import correr_escenarios, decidir, sensibilidad
from .parametros_ia import contrastar_r_con_estudios
from .tipos import Decision, Resultados


def ejecutar(
    ruta_excel: Path | str,
    x_pct: float = 20.0,
    fecha_ejecucion: date | None = None,
) -> Resultados:
    """Coordinate validation, calculation, and decision without performing I/O on results.

    M0 reads and validates the spreadsheet, raising ErrorDeEntrada on failure.
    M1 computes COCOMO II base metrics.
    M2 appends study comparison warnings (A02/A03) to entradas.avisos.
    M5 runs scenarios, sensitivity, and decision rules.
    If optional case data is present, M6 and M7 run actual-cost accounting and contrast.
    """
    ruta = Path(ruta_excel)
    entradas = cargar_entradas(ruta)

    avisos_r = contrastar_r_con_estudios(entradas.parametros, entradas.estudios)
    if avisos_r:
        entradas = replace(entradas, avisos=entradas.avisos + avisos_r)

    base = estimar_base(entradas.proyecto, entradas.constantes)
    escenarios = correr_escenarios(
        entradas.proyecto, entradas.constantes, entradas.parametros
    )
    veredicto, robusta = decidir(escenarios)
    decision = Decision(
        escenarios=escenarios,
        sensibilidad=sensibilidad(
            entradas.proyecto, entradas.constantes, entradas.parametros, x_pct=x_pct
        ),
        x_pct=x_pct,
        veredicto=veredicto,
        robusta=robusta,
    )

    if entradas.caso is not None:
        costo_real = calcular_costo_real(entradas.caso, base.t_h)
        contraste = contrastar(
            base.C_trad,
            escenarios[1].resultado.C_ia,
            costo_real,
            decision.robusta,
            verificar_cocomo(entradas.constantes),
        )
    else:
        costo_real = None
        contraste = None

    return Resultados(
        entradas=entradas,
        base=base,
        decision=decision,
        costo_real=costo_real,
        contraste=contraste,
        fecha_ejecucion=fecha_ejecucion,
    )
