# End-to-end verification and acceptance closure
Objective: deliver Step 10 (end-to-end verification against Section 13 acceptance criteria) certifying the completed COCOMO II + AI adoption estimation system.
Branch: `feat/cocomo-core`; delivery: `single-pr` per coherent work unit, local only; runner: `python -B -m pytest`.

## Specs

- **S1 — Scope.** User authorization: **"vamos con el paso 10"**. Execute Step 10 from IMPLEMENTACION_MODELO.docx §§12, 13. Deliver `pruebas/test_punta_a_punta.py`, seed `datos/ejemplo_dorado.xlsx`, verify all 13 acceptance criteria, and record full audit results. Original files in `D:\FICHAS DE TRABAJO\` remain strictly read-only and preserved.
- **S2 — Acceptance Criteria Audit (Section 13).**
  - **Funcionamiento:**
    - All pytest test cases pass across the full suite (core, adapters, pipeline, CLI, UI, and architecture).
    - `verificar_cocomo` evaluates to `True` with default manual constants.
    - An Excel file with missing required inputs aggregates all located problems simultaneously with `[Código] Hoja ..., celda ...:` and terminates before calculation.
    - A workbook without validation case computes M1–M5 and M8 without errors (`costo_real=None`, `contraste=None`); a workbook with case executes M6 and M7.
    - Repeated executions on identical files yield bit-for-bit and numerically identical outputs.
  - **Trazabilidad:**
    - Every report metric includes its formula code (`F...`) and origin cell (`sheet!cell`).
    - Declared assumptions are reported in both artifacts and UI.
    - Results of M2–M5 remain invariant under modifications restricted to case validation sheets.
  - **Interfaz:**
    - Streamlit application allows uploading `.xlsx`, renders all six tabs, and exposes download buttons for generated artifacts.
    - Zero local arithmetic or validation logic inside `app.py`.
  - **Coherencia con la tesis:**
    - Pure formulas follow F1–F36 (omitting retired F11 and F12).
    - Zero non-deterministic sampling, bootstrapping, or circular empirical calibration of $r$.
    - Estimation accuracy is reported via $F_{34}$ and evaluated against the $\le 25\%$ threshold.
- **S3 — Code Quality & Artifacts.** All files clean under `ruff check` and `ruff format`. Python 3.11 AST compatibility certified across all modules.

## Tasks

- **T1 — S1–S3 — inline — completed — commit pending.** Implemented `pruebas/test_punta_a_punta.py` covering all Section 13 acceptance criteria, generated `datos/ejemplo_dorado.xlsx`, and verified 100% green suite (264/264 tests). Ready for commit.

## Log

- **L1 — Current authorization, verbatim:** vamos con el paso 10
- **L2 — Baseline:** clean `11ac1f3`; M0–M9 complete, 257 prior tests.
