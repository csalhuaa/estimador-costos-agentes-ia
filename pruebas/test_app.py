"""Automated interface tests for app.py using Streamlit AppTest."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from streamlit.testing.v1 import AppTest

from pruebas.fixtures_excel import libro_sintetico

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


def _bytes_sintetico(*, caso=True, mutate=lambda w: None) -> bytes:
    bio = BytesIO()
    workbook = libro_sintetico(caso=caso)
    mutate(workbook)
    workbook.save(bio)
    workbook.close()
    return bio.getvalue()


def test_app_initial_render():
    """App renders initial header and upload instructions without errors."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception
    assert len(at.file_uploader) == 1
    assert len(at.slider) == 1
    assert len(at.button) == 1
    assert any("Por favor, sube un archivo Excel" in str(msg.value) for msg in at.info)


def test_app_successful_run_with_case():
    """App processes valid input with case and renders executive canvas and downloads."""
    data = _bytes_sintetico(caso=True)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.file_uploader[0].upload(filename="proyecto_con_caso.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception

    # Check key metrics in main canvas
    metric_labels = [m.label for m in at.metric]
    assert "Costo sin agentes (C_trad)" in metric_labels
    assert "Costo con agentes (esperado)" in metric_labels
    assert "Ahorro neto esperado" in metric_labels
    assert "Relación Beneficio/Costo (RBC)" in metric_labels

    # Check mandatory disclaimer
    assert any(
        "Los parámetros de agentes provienen de la hoja estudios" in str(i.value)
        for i in at.info
    )

    # Check downloads section has download buttons
    assert len(at.download_button) >= 4


def test_app_successful_run_without_case():
    """App processes valid input without case and shows predictive mode notice."""
    data = _bytes_sintetico(caso=False)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.file_uploader[0].upload(filename="proyecto_sin_caso.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception
    assert any(
        "no contiene datos de caso de validación" in str(i.value) for i in at.info
    )


def test_app_validation_error_renders_problem_table():
    """Input validation errors render problem table."""

    def mutate(w):
        w["proyecto"]["C6"] = "EUR"

    data = _bytes_sintetico(caso=True, mutate=mutate)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.file_uploader[0].upload(filename="invalido.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.error) >= 1
    assert "problemas de validación" in at.error[0].value
    assert len(at.dataframe) >= 1


def test_app_unexpected_error_handling(monkeypatch):
    """Unexpected exception displays clean user message without leaking traceback."""

    def crash(*args, **kwargs):
        raise RuntimeError("Simulated crash")

    monkeypatch.setattr("modelo.pipeline.ejecutar", crash)
    data = _bytes_sintetico(caso=True)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.file_uploader[0].upload(filename="valid.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.error) >= 1
    assert "error inesperado" in at.error[0].value.lower()
    assert "Simulated crash" not in at.error[0].value


@pytest.mark.parametrize("verdict", ["conviene", "no conviene"])
@pytest.mark.parametrize("robust", [False, True])
def test_binary_decision_and_neutral_robustness_keep_five_tabs(
    tmp_path, verdict, robust
):
    from dataclasses import replace
    from pruebas.fixtures_excel import guardar_sintetico, resultados_sinteticos

    result = resultados_sinteticos(guardar_sintetico(tmp_path / "input.xlsx"))
    result = replace(
        result,
        decision=replace(result.decision, veredicto=verdict, robusta=robust),
        contraste=replace(result.contraste, decision_estable=robust),
    )
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["resultado"] = result
    at.run()
    assert not at.exception
    assert len(at.tabs) == 5
    text = "\n".join(str(m.value) for m in at.markdown)
    label = "robusta" if robust else "sensible a los parámetros"
    assert f"Robustez: {label}" in text
    assert ("ec-pos" if verdict == "conviene" else "ec-neg") in text
    assert "escenario esperado" in text
    assert "Incluso en el escenario pesimista" not in text
    assert "Ni siquiera en el escenario optimista" not in text
    assert text.count(label) >= 2


@pytest.mark.parametrize(
    "decision",
    [
        SimpleNamespace(veredicto="conviene"),
        SimpleNamespace(veredicto="retirado", robusta=False),
    ],
)
def test_legacy_cache_invalidates_outputs_errors_and_input_identity(decision):
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    for key, value in {
        "resultado": SimpleNamespace(decision=decision),
        "reportes": {"resultados.json": b"stale"},
        "problemas": ("stale",),
        "error_inesperado": "stale",
        "file_hash": "stale",
        "last_x_pct": 20,
    }.items():
        at.session_state[key] = value
    at.run()
    assert not at.exception
    for key in (
        "resultado",
        "reportes",
        "problemas",
        "error_inesperado",
        "file_hash",
        "last_x_pct",
    ):
        assert at.session_state[key] is None
    assert len(at.download_button) == 0
    assert not at.error
