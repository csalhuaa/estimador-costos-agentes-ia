"""Automated interface tests for app.py using Streamlit AppTest."""

from io import BytesIO
from pathlib import Path

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
    assert len(at.title) >= 1
    assert "Estimador de Costo Previo al Proyecto" in at.title[0].value
    assert len(at.sidebar.file_uploader) == 1
    assert len(at.sidebar.slider) == 1
    assert len(at.sidebar.button) == 1
    assert any("Por favor, sube un archivo Excel" in str(msg.value) for msg in at.info)
    assert len(at.tabs) == 0


def test_app_successful_run_with_case():
    """App processes valid input with case and renders all six tabs and downloads."""
    data = _bytes_sintetico(caso=True)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.sidebar.file_uploader[0].upload(filename="proyecto_con_caso.xlsx", content=data)
    at.sidebar.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.tabs) == 6
    tab_labels = [t.label for t in at.tabs]
    assert tab_labels == [
        "Resumen",
        "Escenarios",
        "Sensibilidad",
        "Contraste",
        "Supuestos y fuentes",
        "Descargas",
    ]

    # Check Resumen tab contents
    assert any("NO CONCLUYENTE" in str(w.value) for w in at.warning)
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

    # Check downloads tab has download buttons
    assert len(at.download_button) >= 4


def test_app_successful_run_without_case():
    """App processes valid input without case and shows predictive mode notice."""
    data = _bytes_sintetico(caso=False)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.sidebar.file_uploader[0].upload(filename="proyecto_sin_caso.xlsx", content=data)
    at.sidebar.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.tabs) == 6
    assert any(
        "no contiene datos de caso de validación" in str(i.value) for i in at.info
    )


def test_app_validation_error_renders_problem_table():
    """Input validation errors render problem table and suppress result tabs."""

    def mutate(w):
        w["proyecto"]["C6"] = "EUR"

    data = _bytes_sintetico(caso=True, mutate=mutate)

    at = AppTest.from_file(APP_PATH)
    at.run()
    at.sidebar.file_uploader[0].upload(filename="invalido.xlsx", content=data)
    at.sidebar.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.tabs) == 0
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
    at.sidebar.file_uploader[0].upload(filename="valid.xlsx", content=data)
    at.sidebar.button[0].click()
    at.run()

    assert not at.exception
    assert len(at.tabs) == 0
    assert len(at.error) >= 1
    assert "error inesperado" in at.error[0].value.lower()
    assert "Simulated crash" not in at.error[0].value
