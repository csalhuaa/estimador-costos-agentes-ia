# Streamlit interactive web application
Objective: deliver Step 9 (`app.py` and automated interface tests) connecting the pipeline and report adapters to an interactive Streamlit UI.
Branch: `feat/cocomo-core`; delivery: `single-pr` per coherent work unit, local only; runner: `python -B -m pytest`.

## Specs

- **S1 — Scope.** User authorization: **"continuemos"** (advancing to Step 9). Deliver `app.py` and `pruebas/test_app.py` per IMPLEMENTACION_MODELO.docx §§11, 12. Pure model modules remain untouched; `app.py` contains zero business arithmetic, delegating completely to `modelo.pipeline.ejecutar` and `modelo.reporte.escribir_reporte`.
- **S2 — User Flow.**
  - Sidebar file uploader (`st.file_uploader`, accepting only `.xlsx`).
  - Sensitivity slider (`±x %`, bounds [5, 50], default 20).
  - Calculate button triggering execution; inputs saved to a temporary location.
  - State caching in `st.session_state` keyed by input file SHA-256 and `x_pct`. Recalculates only when file or `x_pct` changes.
  - Safe error handling: `ErrorDeEntrada` renders a clean table of problems (`código`, `hoja`, `celda`, `mensaje`) without displaying partial results. Unexpected exceptions log to console and present a graceful message without Python tracebacks.
- **S3 — Executive summary plus five tabs (migration note).** The historical six-tab/three-state description is superseded by the current executive canvas and `binary-decision.md` S2–S4.
  - **1. Resumen:** Color-coded expected-case verdict (green "conviene", red "no conviene") and neutral robustness label (`robusta` / `sensible a los parámetros`); key metrics ($C_{trad}$, expected $C_{ia}$, expected net savings, $RBC$, payback); $r$ vs $r^*$; recovery within $T$; highest-impact sensitivity parameter; mandatory disclaimer: *"Los parámetros de agentes provienen de la hoja estudios; los marcados como supuesto no tienen fuente publicada"*.
  - **2. Escenarios:** Detailed comparison table across Pesimista, Esperado, and Optimista scenarios (parameters and economic outcomes).
  - **3. Sensibilidad:** Sensitivity bar chart ordered by absolute impact, accompanied by the detailed variation table.
  - **4. Contraste:** Active only when case data is present: figures A (budget), B (model estimate), C (actual cost), the three error metrics, and accuracy / stability flags. Informative notice when case data is omitted.
  - **5. Supuestos y fuentes:** Declared assumptions list, literature studies table, and active execution warnings (`A01`–`A08`).
  - **6. Descargas:** File download buttons for `reporte.xlsx`, `reporte.md`, `resultados.json`, and `sensibilidad.png`.
- **S4 — Display rules.** Amounts in USD with thousands separators and 2 decimals; fractions with 4 decimals; percentages with 1 decimal. All UI text in Spanish.
- **S5 — Automated Tests.** `pruebas/test_app.py` validating initial view, error handling on malformed files, complete rendering on valid workbooks (both with and without case data), and zero traceback leakage.

## Tasks

- **T1 — S1–S5 — inline — completed — commit pending.** Implemented `app.py` with six regulatory tabs and automated tests in `pruebas/test_app.py`. Full test suite passed (257/257). Ruff check and format clean. Ready for commit.

## Log

- **L1 — Current authorization, verbatim:** continuemos
- **L2 — Baseline:** clean `0312219`; M0–M8, pipeline and CLI complete, 252 prior tests.
