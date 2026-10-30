"""Automated interface tests for app.py using Streamlit AppTest."""

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from streamlit.testing.v1 import AppTest

from pruebas.fixtures_excel import libro_sintetico

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
APP_TIMEOUT = 15


def app_test():
    return AppTest.from_file(APP_PATH, default_timeout=APP_TIMEOUT)


def _bytes_sintetico(*, caso=True, mutate=lambda w: None) -> bytes:
    bio = BytesIO()
    workbook = libro_sintetico(caso=caso)
    mutate(workbook)
    workbook.save(bio)
    workbook.close()
    return bio.getvalue()


def test_app_initial_render():
    """App renders initial header and upload instructions without errors."""
    at = app_test()
    at.run()
    assert not at.exception
    assert len(at.file_uploader) == 1
    assert len(at.slider) == 1
    assert len(at.button) == 1
    assert any("Por favor, sube un archivo Excel" in str(msg.value) for msg in at.info)


def test_app_successful_run_with_case():
    """App processes valid input with case and renders executive canvas and downloads."""
    data = _bytes_sintetico(caso=True)

    at = app_test()
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

    at = app_test()
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

    at = app_test()
    at.run()
    at.file_uploader[0].upload(filename="invalido.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.error) >= 1
    assert "problemas de validación" in at.error[0].value
    assert len(at.dataframe) >= 1


def test_app_unexpected_error_handling(monkeypatch, caplog):
    """Unexpected exception displays clean user message without leaking traceback."""

    def crash(*args, **kwargs):
        raise RuntimeError("Simulated crash")

    monkeypatch.setattr("modelo.pipeline.ejecutar", crash)
    data = _bytes_sintetico(caso=True)

    at = app_test()
    at.run()
    at.file_uploader[0].upload(filename="valid.xlsx", content=data)
    at.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.error) >= 1
    assert "error inesperado" in at.error[0].value.lower()
    assert "Simulated crash" not in at.error[0].value
    assert any(
        record.exc_info and "Simulated crash" in str(record.exc_info[1])
        for record in caplog.records
    )
    for key in ("resultado", "reportes", "file_hash", "last_x_pct"):
        assert at.session_state[key] is None
    at.file_uploader[0].clear().run()
    assert not at.exception and not at.error
    assert at.session_state["error_inesperado"] is None


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
    at = app_test()
    at.run()
    at.file_uploader[0].upload(filename="input.xlsx", content=_bytes_sintetico())
    at.run()
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
    at = app_test()
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


def test_upload_cache_calculate_change_remove_and_identical_reupload(monkeypatch):
    from modelo import pipeline

    original = pipeline.ejecutar
    calls = []

    def traced(path, x_pct):
        calls.append((Path(path).read_bytes(), x_pct))
        return original(path, x_pct=x_pct)

    monkeypatch.setattr(pipeline, "ejecutar", traced)
    data = _bytes_sintetico()
    at = app_test().run()
    at.file_uploader[0].upload(filename="input.xlsx", content=data)
    at.run()
    assert not at.exception
    assert len(calls) == 1
    at.button[0].click().run()
    assert not at.exception
    assert len(calls) == 1
    at.slider[0].set_value(25).run()
    assert not at.exception
    assert len(calls) == 2 and calls[-1][1] == 25
    changed = _bytes_sintetico(caso=False)
    at.file_uploader[0].upload(filename="changed.xlsx", content=changed)
    at.run()
    assert not at.exception
    assert len(calls) == 3 and calls[-1][0] == changed
    at.file_uploader[0].clear().run()
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
    at.file_uploader[0].upload(filename="changed.xlsx", content=changed)
    at.run()
    assert not at.exception
    assert len(calls) == 4
    assert len(at.download_button) == 4


def test_explicit_internal_force_is_not_silently_ignored(monkeypatch):
    from modelo import pipeline

    original = pipeline.ejecutar
    calls = []

    def traced(path, x_pct):
        calls.append(x_pct)
        return original(path, x_pct=x_pct)

    monkeypatch.setattr(pipeline, "ejecutar", traced)
    at = AppTest.from_function(_force_probe, default_timeout=APP_TIMEOUT)
    at.session_state["data"] = _bytes_sintetico()
    at.run()
    assert not at.exception
    assert calls == [20, 20]


def _force_probe():
    import streamlit as st
    from interfaz import estado
    from types import SimpleNamespace

    estado.inicializar()
    uploaded = SimpleNamespace(
        name="input.xlsx", getvalue=lambda: st.session_state.data
    )
    estado.procesar(uploaded, 20, forzar=False)
    estado.procesar(uploaded, 20, forzar=False)
    estado.procesar(uploaded, 20, forzar=True)


def test_rbc_four_decimals_in_metric_and_scenario_table():
    at = app_test().run()
    at.file_uploader[0].upload(filename="input.xlsx", content=_bytes_sintetico())
    at.run()
    assert not at.exception
    from interfaz.formato import num

    result = at.session_state["resultado"]
    expected = num(result.decision.escenarios[1].resultado.rbc, 4)
    assert (
        next(m.value for m in at.metric if m.label == "Relación Beneficio/Costo (RBC)")
        == expected
    )
    text = "\n".join(str(m.value) for m in at.markdown)
    for scenario in result.decision.escenarios:
        assert num(scenario.resultado.rbc, 4) in text


def test_temporary_input_write_error_is_logged_sanitized_and_invalidates_identity(
    monkeypatch, caplog
):
    original = Path.write_bytes

    def fail(path, data):
        if path.name == "input.xlsx":
            raise OSError("Synthetic temporary write failure")
        return original(path, data)

    monkeypatch.setattr(Path, "write_bytes", fail)
    at = app_test().run()
    at.file_uploader[0].upload(filename="input.xlsx", content=_bytes_sintetico())
    at.run()
    assert not at.exception
    assert "error inesperado" in at.error[0].value
    assert "Synthetic temporary write failure" not in at.error[0].value
    assert any(
        record.exc_info
        and "Synthetic temporary write failure" in str(record.exc_info[1])
        for record in caplog.records
    )
    for key in ("resultado", "reportes", "file_hash", "last_x_pct"):
        assert at.session_state[key] is None
