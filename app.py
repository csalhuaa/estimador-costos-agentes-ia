"""Interfaz interactiva Streamlit para el estimador de costos COCOMO II con agentes IA.

Consumo exclusivo de modelo.pipeline.ejecutar y modelo.reporte.escribir_reporte.
Cero fórmulas o validaciones de negocio locales.
Estilo profesional, minimalista y orientado a análisis ejecutivo de ingeniería.
"""

from hashlib import sha256
from pathlib import Path
import tempfile

import streamlit as st

from modelo.errores import ErrorDeEntrada
from modelo.pipeline import ejecutar
from modelo.reporte import escribir_reporte

# Configuración de página
st.set_page_config(
    page_title="Estimador de Costo Previo al Proyecto — COCOMO II & IA",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyección de estilos de diseño moderno, limpio y profesional (Executive Analytics)
st.markdown(
    """
    <style>
    /* Tipografía y espaciado general */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    code, kbd, pre, samp {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.88em;
    }

    /* Insignias ejecutivas superiores */
    .top-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: rgba(37, 99, 235, 0.07);
        color: #2563eb;
        border: 1px solid rgba(37, 99, 235, 0.18);
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* Barra de metadatos del proyecto */
    .project-header-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin: 0.8rem 0 1.6rem 0;
        padding: 0.75rem 1rem;
        background: rgba(148, 163, 184, 0.05);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
    }

    .project-chip {
        display: inline-flex;
        align-items: center;
        font-size: 0.82rem;
        color: #475569;
    }

    .project-chip span {
        font-weight: 600;
        color: inherit;
        margin-left: 4px;
    }

    .project-chip-sep {
        color: #cbd5e1;
        margin: 0 4px;
    }

    /* Tarjetas de Métricas (KPI Cards) */
    div[data-testid="stMetric"] {
        background: rgba(148, 163, 184, 0.04);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
        transition: all 0.2s ease-in-out;
    }

    div[data-testid="stMetric"]:hover {
        border-color: rgba(37, 99, 235, 0.35);
        background: rgba(37, 99, 235, 0.02);
    }

    div[data-testid="stMetric"] label {
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        color: #64748b !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Pestañas de Navegación */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.75rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        padding-bottom: 2px;
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 4px 12px 4px;
        font-size: 0.92rem;
        font-weight: 500;
        color: #64748b;
    }

    .stTabs [aria-selected="true"] {
        color: #2563eb !important;
        font-weight: 600 !important;
    }

    /* Tarjetas de Escenarios */
    .scenario-summary-card {
        padding: 14px 16px;
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(148, 163, 184, 0.03);
        margin-bottom: 1rem;
    }

    .scenario-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(148, 163, 184, 0.15);
    }

    /* Tarjetas de Descarga */
    .download-tile {
        padding: 16px;
        border-radius: 8px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(148, 163, 184, 0.03);
        margin-bottom: 12px;
    }

    .download-tile-title {
        font-weight: 600;
        font-size: 0.92rem;
        margin-bottom: 4px;
    }

    .download-tile-desc {
        font-size: 0.80rem;
        color: #64748b;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Encabezado principal
st.markdown(
    '<div class="top-badge">Marco de Decisión Previa al Proyecto</div>',
    unsafe_allow_html=True,
)
st.title("Estimador de Costo Previo al Proyecto (COCOMO II + Agentes IA)")
st.caption(
    "Evaluación económica determinista: modelo paramétrico COCOMO II (2000), costos de fricción de agentes y análisis empírico de sensibilidad."
)

# Barra lateral
st.sidebar.markdown("### Configuración del Caso")
uploaded_file = st.sidebar.file_uploader(
    "Subir archivo Excel del proyecto (.xlsx)",
    type=["xlsx"],
    help="Debe seguir la plantilla oficial de 9 hojas (ENTRADAS_EXCEL.xlsx).",
)

x_pct = st.sidebar.slider(
    "Variación para análisis de sensibilidad (±x %)",
    min_value=5.0,
    max_value=50.0,
    value=20.0,
    step=1.0,
    help="Porcentaje para evaluar impacto individual de parámetros sobre el ahorro neto.",
)

st.sidebar.markdown("---")
calcular_btn = st.sidebar.button("Calcular", type="primary", use_container_width=True)

# Manejo de estado
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "reportes" not in st.session_state:
    st.session_state.reportes = None
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None
if "last_x_pct" not in st.session_state:
    st.session_state.last_x_pct = None
if "problemas" not in st.session_state:
    st.session_state.problemas = None
if "error_inesperado" not in st.session_state:
    st.session_state.error_inesperado = None

# Ejecución al pulsar Calcular o si hay archivo y cambió
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    current_hash = sha256(file_bytes).hexdigest()

    should_calc = calcular_btn or (
        st.session_state.file_hash != current_hash
        or st.session_state.last_x_pct != x_pct
    )

    if should_calc:
        st.session_state.problemas = None
        st.session_state.error_inesperado = None
        st.session_state.resultado = None
        st.session_state.reportes = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir) / uploaded_file.name
            temp_path.write_bytes(file_bytes)
            try:
                res = ejecutar(temp_path, x_pct=float(x_pct))
                st.session_state.resultado = res
                st.session_state.file_hash = current_hash
                st.session_state.last_x_pct = x_pct

                # Generar reportes para descargas en carpeta temporal
                rep_dir = Path(tmp_dir) / "salidas"
                archivos = escribir_reporte(res, rep_dir)
                st.session_state.reportes = {p.name: p.read_bytes() for p in archivos}
            except ErrorDeEntrada as exc:
                st.session_state.problemas = exc.problemas
            except Exception as exc:
                print(f"[ERROR INESPERADO EN APP]: {exc}")
                st.session_state.error_inesperado = (
                    "Ocurrió un error inesperado al procesar el archivo. "
                    "Verifique que el formato del archivo sea un libro Excel .xlsx válido."
                )

# Visualización de estados
if st.session_state.problemas:
    st.error("Se encontraron problemas de validación en el archivo Excel ingresado:")
    tabla_problemas = [
        {
            "Código": p.codigo,
            "Hoja": p.hoja,
            "Celda": p.celda,
            "Mensaje": p.mensaje,
        }
        for p in st.session_state.problemas
    ]
    st.dataframe(tabla_problemas, use_container_width=True, hide_index=True)

elif st.session_state.error_inesperado:
    st.error(st.session_state.error_inesperado)

elif st.session_state.resultado is not None:
    res = st.session_state.resultado
    d = res.decision
    b = res.base
    p = res.entradas.proyecto
    esp = d.escenarios[1].resultado
    pes = d.escenarios[0].resultado
    opt = d.escenarios[2].resultado

    # Barra informativa de contexto del proyecto cargado
    st.markdown(
        f"""
        <div class="project-header-bar">
            <div class="project-chip">Proyecto: <span>{p.nombre or "Sin nombre"}</span></div>
            <div class="project-chip-sep">|</div>
            <div class="project-chip">Tamaño: <span>{p.size_ksloc:.1f} KSLOC</span></div>
            <div class="project-chip-sep">|</div>
            <div class="project-chip">Moneda: <span>{p.moneda}</span></div>
            <div class="project-chip-sep">|</div>
            <div class="project-chip">Salario base: <span>${p.c_pm:,.2f} USD/PM</span></div>
            <div class="project-chip-sep">|</div>
            <div class="project-chip">Equipo con IA: <span>{p.n_u} usuarios</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Resumen",
            "Escenarios",
            "Sensibilidad",
            "Contraste",
            "Supuestos y fuentes",
            "Descargas",
        ]
    )

    # 1. Resumen
    with tabs[0]:
        st.markdown("### Veredicto de Decisión Económica")
        veredicto = d.veredicto
        if veredicto == "conviene":
            st.success("### ✔ CONVIENE ADOPTAR AGENTES IA")
            st.write(
                "El ahorro neto es estrictamente positivo incluso bajo el escenario pesimista."
            )
        elif veredicto == "no conviene":
            st.error("### ✖ NO CONVIENE ADOPTAR AGENTES IA")
            st.write("El ahorro neto es negativo incluso bajo el escenario optimista.")
        else:
            st.warning("### ⚠ NO CONCLUYENTE")
            st.write(
                "La conveniencia económica depende de los supuestos del escenario; "
                "el ahorro neto cambia de signo entre el caso pesimista y el optimista."
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Costo sin agentes (C_trad)", f"{b.C_trad:,.2f} USD")
        col2.metric("Costo con agentes (esperado)", f"{esp.C_ia:,.2f} USD")
        col3.metric("Ahorro neto esperado", f"{esp.ahorro_neto:,.2f} USD")
        rbc_text = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
        col4.metric("Relación Beneficio/Costo (RBC)", rbc_text)

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("### Parámetros Clave y Plazo de Recuperación")
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"**Reducción $r$ vs Umbral $r^*$:**\n\n"
            f"`{d.escenarios[1].valores.r:.4f}` frente a `{esp.r_estrella:.4f}`"
        )
        if esp.recuperacion_meses is not None:
            dentro_txt = "Dentro de $T$" if esp.recupera_dentro_de_T else "Fuera de $T$"
            c2.markdown(
                f"**Recuperación de inversión ($T_{{rec}}$):**\n\n"
                f"`{esp.recuperacion_meses:.1f} meses` ({dentro_txt})"
            )
        else:
            c2.markdown(
                "**Recuperación de inversión:**\n\n`No recupera (RBC ≤ 0 o C_adop = 0)`"
            )

        if d.sensibilidad:
            c3.markdown(
                f"**Parámetro de mayor efecto:**\n\n`{d.sensibilidad[0].parametro}`"
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.info(
            "Los parámetros de agentes provienen de la hoja estudios; "
            "los marcados como supuesto no tienen fuente publicada."
        )

    # 2. Escenarios
    with tabs[1]:
        st.markdown("### Comparación Tripartita de Escenarios")
        st.caption(
            "Contraste simultáneo de las tres condiciones de adopción (pesimista, esperada y optimista)."
        )

        # Resumen en tarjetas ejecutivas
        rbc_pes_txt = f"{pes.rbc:.4f}" if pes.rbc is not None else "N/A"
        rbc_esp_txt = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
        rbc_opt_txt = f"{opt.rbc:.4f}" if opt.rbc is not None else "N/A"

        col_pes, col_esp, col_opt = st.columns(3)
        with col_pes:
            st.markdown(
                f"""
                <div class="scenario-summary-card">
                    <div class="scenario-title" style="color: #ef4444;">Escenario Pesimista</div>
                    <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">${pes.C_ia:,.2f} USD</div>
                    <div style="font-size: 0.82rem; color: #64748b;">Ahorro neto: <b>${pes.ahorro_neto:,.2f} USD</b></div>
                    <div style="font-size: 0.82rem; color: #64748b;">RBC: <b>{rbc_pes_txt}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_esp:
            st.markdown(
                f"""
                <div class="scenario-summary-card" style="border-color: rgba(37,99,235,0.4); background: rgba(37,99,235,0.02);">
                    <div class="scenario-title" style="color: #2563eb;">Escenario Esperado</div>
                    <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">${esp.C_ia:,.2f} USD</div>
                    <div style="font-size: 0.82rem; color: #64748b;">Ahorro neto: <b>${esp.ahorro_neto:,.2f} USD</b></div>
                    <div style="font-size: 0.82rem; color: #64748b;">RBC: <b>{rbc_esp_txt}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_opt:
            st.markdown(
                f"""
                <div class="scenario-summary-card">
                    <div class="scenario-title" style="color: #10b981;">Escenario Optimista</div>
                    <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 4px;">${opt.C_ia:,.2f} USD</div>
                    <div style="font-size: 0.82rem; color: #64748b;">Ahorro neto: <b>${opt.ahorro_neto:,.2f} USD</b></div>
                    <div style="font-size: 0.82rem; color: #64748b;">RBC: <b>{rbc_opt_txt}</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        esc_rows = []
        for s in d.escenarios:
            esc_rows.append(
                {
                    "Escenario": s.nombre.capitalize(),
                    "r (reducción)": f"{s.valores.r:.4f}",
                    "Costo fijo (USD)": f"{s.costos.C_fijo:,.2f}",
                    "Costo variable u ($/h)": f"{s.costos.u:,.2f}",
                    "Costo adopción C_adop (USD)": f"{s.resultado.C_adop:,.2f}",
                    "Ahorro bruto (USD)": f"{s.resultado.ahorro_bruto:,.2f}",
                    "Ahorro neto (USD)": f"{s.resultado.ahorro_neto:,.2f}",
                    "Costo total IA C_ia (USD)": f"{s.resultado.C_ia:,.2f}",
                    "RBC": f"{s.resultado.rbc:.4f}"
                    if s.resultado.rbc is not None
                    else "N/A",
                }
            )
        st.dataframe(esc_rows, use_container_width=True, hide_index=True)

    # 3. Sensibilidad
    with tabs[2]:
        st.markdown(f"### Análisis de Sensibilidad (±{d.x_pct:.1f} %)")
        st.caption(
            f"Impacto marginal individual sobre el ahorro neto al variar cada parámetro en ±{d.x_pct:.1f}% ceteris paribus."
        )

        if (
            st.session_state.reportes
            and "sensibilidad.png" in st.session_state.reportes
        ):
            st.image(
                st.session_state.reportes["sensibilidad.png"],
                caption=f"Gráfico de tornado: ordenado de mayor a menor impacto sobre el ahorro neto (±{d.x_pct:.1f}%).",
                use_container_width=True,
            )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        sens_rows = [
            {
                "Parámetro": fila.parametro,
                f"Efecto al bajar {d.x_pct:.1f}% (USD)": f"{fila.efecto_bajo:,.2f}",
                f"Efecto al subir {d.x_pct:.1f}% (USD)": f"{fila.efecto_alto:,.2f}",
                "Impacto absoluto máximo (USD)": f"{max(abs(fila.efecto_bajo), abs(fila.efecto_alto)):,.2f}",
            }
            for fila in d.sensibilidad
        ]
        st.dataframe(sens_rows, use_container_width=True, hide_index=True)

    # 4. Contraste
    with tabs[3]:
        st.markdown("### Validación y Contraste Empírico")
        st.caption(
            "Cotejo de la estimación COCOMO II y con agentes frente al presupuesto histórico y el costo real ejecutado."
        )

        if res.contraste is not None and res.costo_real is not None:
            cr = res.costo_real
            ct = res.contraste
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(
                "Cifra A: Presupuesto inicial (sin agentes)",
                f"{cr.C_presup:,.2f} USD",
            )
            col_b.metric(
                "Cifra B: Estimación de herramienta (C_ia)",
                f"{esp.C_ia:,.2f} USD",
            )
            col_c.metric(
                "Cifra C: Costo real registrado",
                f"{cr.C_real:,.2f} USD",
            )

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### Métricas de Desviación y Control")
            e1, e2, e3 = st.columns(3)
            e1.markdown(
                f"**Error estimación IA ($F_{{34}}$):**\n\n`{ct.err_estimacion_ia * 100:.1f} %`"
            )
            e2.markdown(
                f"**Error COCOMO vs Presupuesto ($F_{{35}}$):**\n\n`{ct.err_cocomo_vs_presup * 100:.1f} %`"
            )
            e3.markdown(
                f"**Desviación presupuestaria ($F_{{36}}$):**\n\n`{ct.desviacion_presup * 100:.1f} %`"
            )

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            ok_exact = "Cumple (≤ 25%)" if ct.cumple_exactitud else "No cumple (> 25%)"
            ok_est = "Decisión estable" if ct.decision_estable else "No estable"
            ok_cocomo = (
                "Verificación COCOMO OK"
                if ct.verificacion_cocomo_ok
                else "Verificación fallida"
            )

            st.markdown(
                f"""
                - **Criterio de exactitud ($F_{{34}} \\le 0.25$):** `{ok_exact}`
                - **Criterio de estabilidad de decisión:** `{ok_est}`
                - **Verificación COCOMO II con constantes:** `{ok_cocomo}`
                """
            )
        else:
            st.info(
                "El libro cargado no contiene datos de caso de validación "
                "(hojas `presupuesto_inicial` y `costo_real_sprint` vacías). "
                "La herramienta operó en modo puramente predictivo (M0 a M5)."
            )

    # 5. Supuestos y fuentes
    with tabs[4]:
        st.markdown("### Supuestos Declarados")
        st.caption(
            "Parámetros que no cuentan con estudio primario en la literatura y fueron declarados por juicio experto."
        )

        if res.entradas.supuestos:
            for s in res.entradas.supuestos:
                st.markdown(
                    f"- `{s}`: parámetro basado en supuesto declarado sin respaldo en estudio publicado."
                )
        else:
            st.write(
                "No se registraron supuestos declarados; todos los parámetros provienen de estudios primarios."
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("### Estudios Primarios Identificados")
        st.caption(
            "Evidencia empírica extraída de la literatura primaria indexada en la hoja `estudios`."
        )

        if res.entradas.estudios:
            est_data = [
                {
                    "ID": e.id,
                    "Autores": e.autores,
                    "Año": e.ano,
                    "Título": e.titulo,
                    "DOI / URL": e.doi_url,
                    "r equivalente": f"{e.r_equivalente:.4f}"
                    if e.r_equivalente is not None
                    else "-",
                    "Cumple criterios": e.cumple,
                }
                for e in res.entradas.estudios
            ]
            st.dataframe(est_data, use_container_width=True, hide_index=True)
        else:
            st.write("No hay estudios primarios registrados en la hoja `estudios`.")

        if res.entradas.avisos:
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("### Avisos del Sistema")
            avisos_data = [
                {
                    "Código": a.codigo,
                    "Hoja": a.hoja,
                    "Celda": a.celda,
                    "Mensaje": a.mensaje,
                }
                for a in res.entradas.avisos
            ]
            st.dataframe(avisos_data, use_container_width=True, hide_index=True)

    # 6. Descargas
    with tabs[5]:
        st.markdown("### Exportación y Artefactos Estáticos")
        st.caption(
            "Descargue los cuatro artefactos estáticos certificados con trazabilidad matemática completa."
        )

        if st.session_state.reportes:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if "reporte.xlsx" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-tile">
                            <div class="download-tile-title">Libro Excel Trazable (reporte.xlsx)</div>
                            <div class="download-tile-desc">Contiene todas las hojas de cálculo, fuentes y fórmulas de M0 a M8.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Descargar reporte.xlsx",
                        data=st.session_state.reportes["reporte.xlsx"],
                        file_name="reporte.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                if "reporte.md" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-tile">
                            <div class="download-tile-title">Documento Markdown (reporte.md)</div>
                            <div class="download-tile-desc">Reporte ejecutivo listo para documentación técnica o Pull Request.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Descargar reporte.md",
                        data=st.session_state.reportes["reporte.md"],
                        file_name="reporte.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )

            with col_d2:
                if "resultados.json" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-tile">
                            <div class="download-tile-title">Esquema JSON Estricto (resultados.json)</div>
                            <div class="download-tile-desc">Estructura máquina de datos con identificación unívoca de fórmulas.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Descargar resultados.json",
                        data=st.session_state.reportes["resultados.json"],
                        file_name="resultados.json",
                        mime="application/json",
                        use_container_width=True,
                    )

                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                if "sensibilidad.png" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-tile">
                            <div class="download-tile-title">Gráfico de Tornado (sensibilidad.png)</div>
                            <div class="download-tile-desc">Visualización estática de alta resolución generada con Matplotlib.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        "Descargar sensibilidad.png",
                        data=st.session_state.reportes["sensibilidad.png"],
                        file_name="sensibilidad.png",
                        mime="image/png",
                        use_container_width=True,
                    )

else:
    st.info(
        "Por favor, sube un archivo Excel válido (.xlsx) desde la barra lateral "
        "para comenzar la estimación."
    )
