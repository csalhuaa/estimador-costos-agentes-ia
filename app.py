"""Streamlit entry point for the COCOMO II + AI agents cost estimator.

Orchestration only: layout order and controls. Rendering lives in ``interfaz``;
all calculations live in ``modelo`` and are reached through ``modelo.pipeline``.
"""

import streamlit as st

from interfaz import estado, vistas
from interfaz.componentes import encabezado
from interfaz.tema import aplicar_tema

st.set_page_config(
    page_title="Estimador de costo previo al proyecto",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed",
)
aplicar_tema()
estado.inicializar()
encabezado()

archivo_col, sens_col, boton_col = st.columns(
    [5, 3, 1.4], gap="medium", vertical_alignment="bottom"
)
with archivo_col:
    archivo = st.file_uploader(
        "Libro de entradas (.xlsx)",
        type=["xlsx"],
        help="Plantilla oficial de 9 hojas (ENTRADAS_EXCEL.xlsx).",
    )
with sens_col:
    x_pct = st.slider(
        "Variación para sensibilidad (± %)",
        min_value=5.0,
        max_value=50.0,
        value=20.0,
        step=1.0,
        help="Cuánto se sube y se baja cada parámetro, uno a la vez, en la sección Sensibilidad.",
    )
with boton_col:
    st.button(
        "Calcular",
        type="primary",
        icon=":material/play_arrow:",
        use_container_width=True,
    )

if archivo is not None:
    estado.procesar(archivo, x_pct, forzar=False)
else:
    estado.limpiar()

s = st.session_state
if archivo is None and s.resultado is None and not s.problemas:
    vistas.inicio()
elif s.problemas:
    vistas.problemas(s.problemas)
elif s.error_inesperado:
    st.error(s.error_inesperado)
elif s.resultado is not None:
    res = s.resultado
    vistas.contexto(res, s.archivo_nombre)
    vistas.decision(res)

    st.write("")
    t_esc, t_sens, t_val, t_evid, t_exp = st.tabs(
        [
            ":material/table_chart: Escenarios",
            ":material/tune: Sensibilidad",
            ":material/fact_check: Validación",
            ":material/menu_book: Evidencia",
            ":material/download: Exportar",
        ]
    )
    with t_esc:
        vistas.escenarios(res)
    with t_sens:
        vistas.sensibilidad(res)
    with t_val:
        vistas.validacion(res)
    with t_evid:
        vistas.evidencia(res)
    with t_exp:
        vistas.exportar(s.reportes)
