"""Session state and the single call into the model pipeline."""

from hashlib import sha256
import logging
from pathlib import Path
import tempfile

import streamlit as st

from modelo import pipeline
from modelo.errores import ErrorDeEntrada
from modelo.reporte import escribir_reporte

logger = logging.getLogger(__name__)

_CLAVES = (
    "resultado",
    "reportes",
    "file_hash",
    "last_x_pct",
    "problemas",
    "error_inesperado",
    "archivo_nombre",
)


def inicializar() -> None:
    for clave in _CLAVES:
        st.session_state.setdefault(clave, None)
    result = st.session_state.resultado
    if result is not None:
        decision = getattr(result, "decision", None)
        if type(getattr(decision, "robusta", None)) is not bool or getattr(
            decision, "veredicto", None
        ) not in ("conviene", "no conviene"):
            # Old schemas must not retain downloads or suppress identical re-uploads.
            limpiar()


def limpiar() -> None:
    """Invalidate outputs and their input identity as one state transition."""
    st.session_state.update(dict.fromkeys(_CLAVES))


def procesar(archivo, x_pct: float, forzar: bool) -> None:
    """Run the pipeline when the file, the sensitivity or the user request changes."""
    try:
        datos = archivo.getvalue()
        huella = sha256(datos).hexdigest()
        cambio = (
            st.session_state.file_hash != huella or st.session_state.last_x_pct != x_pct
        )
        if not (forzar or cambio or st.session_state.resultado is None):
            return

        limpiar()
        st.session_state.file_hash = huella
        st.session_state.last_x_pct = x_pct
        st.session_state.archivo_nombre = archivo.name

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / Path(archivo.name).name
            ruta.write_bytes(datos)
            # Module attribute lookup keeps the pipeline replaceable in tests.
            resultado = pipeline.ejecutar(ruta, x_pct=float(x_pct))
            archivos = escribir_reporte(resultado, Path(carpeta) / "salidas")
            st.session_state.resultado = resultado
            st.session_state.reportes = {p.name: p.read_bytes() for p in archivos}
    except ErrorDeEntrada as exc:
        limpiar()
        st.session_state.problemas = exc.problemas
    except Exception:
        logger.exception("Unexpected workbook processing failure")
        limpiar()
        st.session_state.error_inesperado = (
            "Ocurrió un error inesperado al procesar el archivo. "
            "Verifique que sea un libro Excel .xlsx válido basado en la plantilla."
        )
