# Pipeline orchestration, CLI entry point and architecture verification
Objective: deliver Step 8 (pipeline, CLI and architecture tests) connecting M0–M8 cleanly without violating layer boundaries.
Branch: `feat/cocomo-core`; delivery: `single-pr` per coherent work unit, local only; runner: `python -B -m pytest`.

## Specs

- **S1 — Scope.** User authorization: **"arranquemos con el paso 8"**. Deliver `modelo/pipeline.py`, `cli.py`, and `pruebas/test_arquitectura.py` from IMPLEMENTACION_MODELO.docx §§10, 12 (Paso 8). Pure M1–M7 mathematical logic remains untouched. Original reference documents in `D:\FICHAS DE TRABAJO` remain strictly read-only.
- **S2 — Pipeline.** Implement `ejecutar(ruta_excel: Path | str, x_pct: float = 20.0, fecha_ejecucion: date | None = None) -> Resultados` in `modelo/pipeline.py`.
  - Step M0: `entradas = cargar_entradas(ruta)`. Propagate `ErrorDeEntrada` on validation failure.
  - Step M2: `avisos_r = contrastar_r_con_estudios(entradas.parametros, entradas.estudios)`. Append to `entradas.avisos`.
  - Step M1: `base = estimar_base(entradas.proyecto, entradas.constantes)`.
  - Step M5: `escenarios = correr_escenarios(entradas.proyecto, entradas.constantes, entradas.parametros)`, `sens = sensibilidad(entradas.proyecto, entradas.constantes, entradas.parametros, x_pct=x_pct)`, `veredicto = decidir(escenarios)`. Pack into `Decision`.
  - Case validation: If `entradas.caso is not None`, compute M6 `costo_real = calcular_costo_real(entradas.caso, base.t_h)` and M7 `contraste = contrastar(base.C_trad, escenarios[1].resultado.C_ia, costo_real, escenarios, verificar_cocomo(entradas.constantes))`. If `entradas.caso is None`, set `costo_real = None` and `contraste = None`.
  - Return `Resultados(entradas, base, decision, costo_real, contraste, fecha_ejecucion)`. Never write files or touch terminal/UI.
- **S3 — CLI.** Implement `cli.py` at the project root.
  - Command line flags: positional `ruta_excel` or `--entradas`/`-e`. Optional `--salidas`/`-o` output directory. Optional `--x_pct`/`-x` (default 20.0, float between 5 and 50).
  - Terminal output: prints execution summary, verdict, cost metrics, declared assumptions, and warnings.
  - When `--salidas` is provided, calls `escribir_reporte(resultados, ruta_salidas)` and prints confirmation of generated report files.
  - Exit codes: `0` on success, `1` on `ErrorDeEntrada` (formatting each problem with `[Código] Hoja <hoja>, celda <celda>: <mensaje> (valor: <valor>).`), `2` on unexpected error (file not found, OS error, unexpected exception). Avisos are printed whenever present.
- **S4 — Architecture tests.** Implement `pruebas/test_arquitectura.py` verifying:
  - Modules M1 to M7 do not import `openpyxl`, `streamlit`, `matplotlib`, or `random`.
  - Case independence: changing `presupuesto_inicial` and `costo_real_sprint` leaves M1–M5 results byte/numerically identical.
  - Determinism: consecutive runs with identical inputs produce identical results.
  - Immutability: M1 to M7 functions do not mutate argument objects.
  - Pipeline behavior: with case, without case, error propagation.
  - CLI behavior: exit code 0 on valid workbook, exit code 1 on invalid workbook with formatted problem output, exit code 2 on missing file.
- **S5 — Code quality.** Conventional commit, ruff check and format clean, 100% test coverage for new components, AST Python 3.11 compatibility.

## Tasks

- **T1 — S1–S5 — inline — completed — commit pending.** Implemented `modelo/pipeline.py`, `cli.py`, and `pruebas/test_arquitectura.py`. Full suite passed (252/252 tests). Ruff check and format verified clean. Ready for commit.

## Log

- **L1 — Current authorization, verbatim:** arranquemos con el paso 8
- **L2 — Baseline:** clean `9b0f2dc`; M0–M8 complete, 245 prior tests.
