"""Command-line interface for the AI cost estimation model."""

import argparse
from math import isfinite
from pathlib import Path
import sys

from modelo.errores import ErrorDeEntrada
from modelo.cocomo import verificar_cocomo
from modelo.constantes import constantes_predeterminadas
from modelo.pipeline import ejecutar
from modelo.reporte import escribir_reporte


def _imprimir_resumen(resultados) -> None:
    d = resultados.decision
    b = resultados.base
    p = resultados.entradas.proyecto
    esp = d.escenarios[1].resultado
    pes = d.escenarios[0].resultado
    opt = d.escenarios[2].resultado

    print("=" * 60)
    print(f"RESUMEN DE ESTIMACIÓN — {p.nombre}")
    print(f"Archivo de entrada : {resultados.entradas.fuente.nombre}")
    print(f"Fecha de ejecución : {resultados.fecha_ejecucion or 'N/A'}")
    print(f"Veredicto          : {d.veredicto.upper()}")
    print(
        f"Robustez           : {'robusta' if d.robusta else 'sensible a los parámetros'}"
    )
    print("-" * 60)
    print(f"Costo tradicional (C_trad)     : {b.C_trad:,.2f} USD")
    print(f"Costo con IA — Esperado (C_ia) : {esp.C_ia:,.2f} USD")
    print(f"Costo con IA — Pesimista       : {pes.C_ia:,.2f} USD")
    print(f"Costo con IA — Optimista       : {opt.C_ia:,.2f} USD")
    print(f"Ahorro neto esperado           : {esp.ahorro_neto:,.2f} USD")
    rbc_str = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
    print(f"Relación beneficio-costo (RBC) : {rbc_str}")
    print(
        f"Reducción r vs r*              : {d.escenarios[1].valores.r:.4f} vs {esp.r_estrella:.4f}"
    )
    if esp.recuperacion_meses is not None:
        recup = f"{esp.recuperacion_meses:.1f} meses ({'dentro de T' if esp.recupera_dentro_de_T else 'fuera de T'})"
    else:
        recup = "N/A"
    print(f"Recuperación de inversión      : {recup}")
    if d.sensibilidad:
        print(f"Parámetro de mayor efecto      : {d.sensibilidad[0].parametro}")

    if resultados.entradas.supuestos:
        print("-" * 60)
        print("Supuestos declarados:")
        for s in resultados.entradas.supuestos:
            print(f"  - {s}")

    if resultados.entradas.avisos:
        print("-" * 60)
        print("Avisos:")
        for a in resultados.entradas.avisos:
            print(f"  [{a.codigo}] Hoja {a.hoja}, celda {a.celda}: {a.mensaje}")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimador de costo previo al proyecto con adopción de agentes IA (COCOMO II). Muestra la recomendación del escenario esperado y su robustez.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "excel_pos",
        nargs="?",
        default=None,
        help="Ruta al archivo Excel de entradas (.xlsx).",
    )
    parser.add_argument(
        "--entrada",
        "--entradas",
        "-e",
        dest="excel_flag",
        default=None,
        help="Ruta al archivo Excel de entradas (.xlsx).",
    )
    parser.add_argument(
        "--salida",
        "--salidas",
        "-s",
        "-o",
        dest="salidas",
        default=None,
        help="Directorio de destino (por defecto salidas) para reporte.xlsx, reporte.md, resultados.json y sensibilidad.png. No sobrescribe archivos existentes.",
    )
    parser.add_argument(
        "--x",
        "--x_pct",
        "-x",
        type=float,
        default=None,
        dest="x_pct",
        help="Sensibilidad finita entre 5 y 50 inclusive (por defecto 20.0).",
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Verifica COCOMO con constantes nominales, sin entradas ni reportes: ok (0) o revisar (2). No admite otras opciones de cálculo.",
    )

    args = parser.parse_args(argv)
    if args.excel_pos is not None and args.excel_flag is not None:
        parser.error("Use una entrada posicional o --entrada, no ambas.")
    if args.verificar:
        if any(
            value is not None
            for value in (args.excel_pos, args.excel_flag, args.salidas, args.x_pct)
        ):
            parser.error("--verificar no admite entradas, salidas ni sensibilidad.")
        try:
            ok = verificar_cocomo(constantes_predeterminadas())
            print("ok" if ok else "revisar")
            return 0 if ok else 2
        except Exception as exc:
            print(f"Error inesperado: {exc}", file=sys.stderr)
            return 2
    x_pct = 20.0 if args.x_pct is None else args.x_pct
    if not isfinite(x_pct) or not 5 <= x_pct <= 50:
        parser.error("La sensibilidad debe ser finita y estar entre 5 y 50.")
    ruta = args.excel_flag or args.excel_pos
    if not ruta:
        print(
            "Error: Se requiere la ruta del archivo Excel de entradas.",
            file=sys.stderr,
        )
        parser.print_usage(sys.stderr)
        return 2

    try:
        resultados = ejecutar(ruta, x_pct=x_pct)
        _imprimir_resumen(resultados)
        dest = Path(args.salidas) if args.salidas is not None else Path("salidas")
        generados = escribir_reporte(resultados, dest)
        print(f"\nReportes generados en {dest}:")
        for g in generados:
            print(f"  - {g.name}")
        return 0
    except ErrorDeEntrada as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error inesperado: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
