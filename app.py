"""Interfaz interactiva Streamlit para el estimador de costos COCOMO II con agentes IA.

Panel de decisión ejecutiva de ingeniería y finanzas.
Consumo exclusivo de modelo.pipeline.ejecutar y modelo.reporte.escribir_reporte.
Cero fórmulas o validaciones de negocio locales.
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

# Sistema de estilos CSS tokenizado (Executive Decision Panel)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --brand: #2563EB;
        --brand-light: rgba(37, 99, 235, 0.08);
        --brand-border: rgba(37, 99, 235, 0.25);
        --success: #059669;
        --success-bg: rgba(5, 150, 105, 0.08);
        --success-border: rgba(5, 150, 105, 0.3);
        --warning: #D97706;
        --warning-bg: rgba(217, 119, 6, 0.08);
        --warning-border: rgba(217, 119, 6, 0.3);
        --danger: #DC2626;
        --danger-bg: rgba(220, 38, 38, 0.08);
        --danger-border: rgba(220, 38, 38, 0.3);
        --ink: #0F172A;
        --muted: #64748B;
        --surface: #FFFFFF;
        --canvas: #F8FAFC;
        --border: #E2E8F0;
        --radius: 12px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: var(--ink);
    }

    code, kbd, pre, samp {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.88em;
    }

    #MainMenu, footer { visibility: hidden; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3.5rem;
        max-width: 1320px;
    }

    /* Hero Ejecutivo */
    .hero-panel {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #1E3A8A 100%);
        color: #F8FAFC;
        border-radius: 16px;
        padding: 2rem 2.2rem;
        margin: 0.5rem 0 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.25);
    }

    .hero-eyebrow {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #93C5FD;
        margin-bottom: 0.4rem;
    }

    .hero-heading {
        font-size: 1.85rem;
        font-weight: 800;
        line-height: 1.2;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }

    .hero-subtext {
        font-size: 0.92rem;
        line-height: 1.55;
        color: #CBD5E1;
        max-width: 820px;
        margin-bottom: 0;
    }

    /* Barra de Metadatos del Proyecto */
    .meta-ribbon {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1.25rem;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }

    .meta-chip {
        font-size: 0.82rem;
        color: var(--muted);
    }

    .meta-chip strong {
        color: var(--ink);
        font-weight: 600;
        margin-left: 3px;
    }

    .meta-sep {
        color: #CBD5E1;
    }

    /* Tarjetas de Métricas Nativas */
    div[data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.15rem 1.25rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        transition: border-color 0.15s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--brand);
    }

    div[data-testid="stMetric"] label {
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: var(--muted) !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        color: var(--ink) !important;
    }

    /* Veredicto Ejecutivo */
    .verdict-card {
        display: flex;
        align-items: flex-start;
        gap: 1.25rem;
        padding: 1.35rem 1.6rem;
        border-radius: var(--radius);
        margin: 0.75rem 0 1.5rem 0;
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }

    .verdict-card.conviene {
        border-left: 5px solid var(--success);
    }

    .verdict-card.no_conviene {
        border-left: 5px solid var(--danger);
    }

    .verdict-card.no_concluyente {
        border-left: 5px solid var(--warning);
    }

    .verdict-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .verdict-badge.conviene {
        background: var(--success-bg);
        color: var(--success);
        border: 1px solid var(--success-border);
    }

    .verdict-badge.no_conviene {
        background: var(--danger-bg);
        color: var(--danger);
        border: 1px solid var(--danger-border);
    }

    .verdict-badge.no_concluyente {
        background: var(--warning-bg);
        color: var(--warning);
        border: 1px solid var(--warning-border);
    }

    .verdict-title {
        font-size: 1.2rem;
        font-weight: 800;
        color: var(--ink);
        margin-bottom: 0.25rem;
    }

    .verdict-explanation {
        font-size: 0.88rem;
        color: var(--muted);
        line-height: 1.5;
        margin: 0;
    }

    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        background: #F1F5F9;
        padding: 0.3rem;
        border-radius: 10px;
        border: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.55rem 1.15rem;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--muted);
    }

    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: var(--brand) !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
    }

    /* Tarjetas de Escenarios */
    .scenario-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.4rem;
        height: 100%;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }

    .scenario-card.pesimista { border-top: 3px solid var(--danger); }
    .scenario-card.esperado { border-top: 3px solid var(--brand); }
    .scenario-card.optimista { border-top: 3px solid var(--success); }

    .scenario-card-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }

    .scenario-card-cost {
        font-size: 1.55rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--ink);
        margin-bottom: 0.5rem;
    }

    .scenario-card-meta {
        font-size: 0.82rem;
        color: var(--muted);
        display: flex;
        justify-content: space-between;
        padding: 0.25rem 0;
        border-top: 1px solid #F1F5F9;
    }

    .scenario-card-meta strong {
        color: var(--ink);
    }

    /* Tarjetas de Descarga */
    .download-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }

    .download-card-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--ink);
        margin-bottom: 0.25rem;
    }

    .download-card-desc {
        font-size: 0.82rem;
        color: var(--muted);
        margin-bottom: 0.85rem;
    }

    /* Onboarding Empty State */
    .onboarding-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.25rem;
        margin: 1.5rem 0 2rem 0;
    }

    .onboarding-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
    }

    .onboarding-step {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--brand);
        margin-bottom: 0.4rem;
    }

    .onboarding-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--ink);
        margin-bottom: 0.45rem;
    }

    .onboarding-text {
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--muted);
    }

    /* Sidebar Refinada */
    .sidebar-section-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94A3B8;
        margin-bottom: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título y Encabezado Ejecutivo
st.title("Estimador de Costo Previo al Proyecto (COCOMO II + Agentes IA)")

st.markdown(
    """
    <div class="hero-panel">
        <div class="hero-eyebrow">Marco de Decisión Previa al Proyecto</div>
        <div class="hero-heading">Evaluación Económica de Adopción de Agentes IA</div>
        <p class="hero-subtext">
            Herramienta analítica de soporte de decisión para ingeniería de software.
            Evalúa el esfuerzo base con COCOMO II (2000), modela fricción y adopción de agentes,
            proyecta escenarios tripartitos y certifica trazabilidad estricta contra literatura empírica.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Barra lateral de configuración
st.sidebar.markdown(
    '<div class="sidebar-section-title">Parámetros del Caso</div>',
    unsafe_allow_html=True,
)
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
calcular_btn = st.sidebar.button(
    "Ejecutar Estimación", type="primary", use_container_width=True
)
st.sidebar.caption(
    "Cálculo determinista F1 a F36. Cero fórmulas ni validaciones locales en la interfaz."
)

# Manejo de estado de sesión
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

                # Generar los cuatro artefactos estáticos
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

# Visualización principal
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

    # Cinta ejecutiva de contexto del proyecto
    st.markdown(
        f"""
        <div class="meta-ribbon">
            <div class="meta-chip">Proyecto: <strong>{p.nombre or "Sin nombre registrado"}</strong></div>
            <div class="meta-sep">•</div>
            <div class="meta-chip">Tamaño de software: <strong>{p.size_ksloc:.1f} KSLOC</strong></div>
            <div class="meta-sep">•</div>
            <div class="meta-chip">Moneda: <strong>{p.moneda}</strong></div>
            <div class="meta-sep">•</div>
            <div class="meta-chip">Costo PM: <strong>${p.c_pm:,.2f} USD</strong></div>
            <div class="meta-sep">•</div>
            <div class="meta-chip">Usuarios con agentes: <strong>{p.n_u} desarrolladores</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navegación por pestañas estructuradas
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
        veredicto = d.veredicto

        # Tarjeta visual de veredicto
        if veredicto == "conviene":
            st.markdown(
                """
                <div class="verdict-card conviene">
                    <div>
                        <div class="verdict-badge conviene">Decisión: Recomendada</div>
                        <div class="verdict-title">Conviene adoptar agentes de IA</div>
                        <p class="verdict-explanation">
                            El ahorro neto económico es estrictamente positivo incluso bajo las condiciones más adversas del escenario pesimista.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.success("### ✔ CONVIENE ADOPTAR AGENTES IA")
        elif veredicto == "no conviene":
            st.markdown(
                """
                <div class="verdict-card no_conviene">
                    <div>
                        <div class="verdict-badge no_conviene">Decisión: No Recomendada</div>
                        <div class="verdict-title">No conviene adoptar agentes de IA</div>
                        <p class="verdict-explanation">
                            El costo de adopción y fricción supera el ahorro bruto incluso bajo los supuestos del escenario más optimista.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.error("### ✖ NO CONVIENE ADOPTAR AGENTES IA")
        else:
            st.markdown(
                """
                <div class="verdict-card no_concluyente">
                    <div>
                        <div class="verdict-badge no_concluyente">Decisión: Sensible a Supuestos</div>
                        <div class="verdict-title">Decisión No Concluyente</div>
                        <p class="verdict-explanation">
                            La viabilidad económica depende críticamente del escenario observado; el ahorro neto cambia de signo entre el caso pesimista y el optimista.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.warning("### ⚠ NO CONCLUYENTE")

        # Fila de métricas clave (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Costo sin agentes (C_trad)", f"{b.C_trad:,.2f} USD")
        col2.metric("Costo con agentes (esperado)", f"{esp.C_ia:,.2f} USD")
        col3.metric("Ahorro neto esperado", f"{esp.ahorro_neto:,.2f} USD")
        rbc_text = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
        col4.metric("Relación Beneficio/Costo (RBC)", rbc_text)

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### Indicadores Operativos y Plazo de Recuperación")
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"**Reducción $r$ frente a umbral $r^*$:**\n\n"
            f"`{d.escenarios[1].valores.r:.4f}` vs `{esp.r_estrella:.4f}`"
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
                f"**Parámetro de mayor impacto:**\n\n`{d.sensibilidad[0].parametro}`"
            )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.info(
            "Los parámetros de agentes provienen de la hoja estudios; "
            "los marcados como supuesto no tienen fuente publicada."
        )

    # 2. Escenarios
    with tabs[1]:
        st.markdown("### Comparación Tripartita de Escenarios")
        st.caption(
            "Análisis comparativo de los tres estados de adopción: pesimista, esperado y optimista."
        )

        col_pes, col_esp, col_opt = st.columns(3)
        rbc_pes_txt = f"{pes.rbc:.4f}" if pes.rbc is not None else "N/A"
        rbc_esp_txt = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
        rbc_opt_txt = f"{opt.rbc:.4f}" if opt.rbc is not None else "N/A"

        with col_pes:
            st.markdown(
                f"""
                <div class="scenario-card pesimista">
                    <div class="scenario-card-header" style="color: var(--danger);">Escenario Pesimista</div>
                    <div class="scenario-card-cost">${pes.C_ia:,.2f}</div>
                    <div class="scenario-card-meta"><span>Ahorro neto:</span> <strong>${pes.ahorro_neto:,.2f}</strong></div>
                    <div class="scenario-card-meta"><span>RBC:</span> <strong>{rbc_pes_txt}</strong></div>
                    <div class="scenario-card-meta"><span>Reducción r:</span> <strong>{pes.r_estrella:.4f}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_esp:
            st.markdown(
                f"""
                <div class="scenario-card esperado">
                    <div class="scenario-card-header" style="color: var(--brand);">Escenario Esperado</div>
                    <div class="scenario-card-cost">${esp.C_ia:,.2f}</div>
                    <div class="scenario-card-meta"><span>Ahorro neto:</span> <strong>${esp.ahorro_neto:,.2f}</strong></div>
                    <div class="scenario-card-meta"><span>RBC:</span> <strong>{rbc_esp_txt}</strong></div>
                    <div class="scenario-card-meta"><span>Reducción r:</span> <strong>{esp.r_estrella:.4f}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_opt:
            st.markdown(
                f"""
                <div class="scenario-card optimista">
                    <div class="scenario-card-header" style="color: var(--success);">Escenario Optimista</div>
                    <div class="scenario-card-cost">${opt.C_ia:,.2f}</div>
                    <div class="scenario-card-meta"><span>Ahorro neto:</span> <strong>${opt.ahorro_neto:,.2f}</strong></div>
                    <div class="scenario-card-meta"><span>RBC:</span> <strong>{rbc_opt_txt}</strong></div>
                    <div class="scenario-card-meta"><span>Reducción r:</span> <strong>{opt.r_estrella:.4f}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        with st.expander(
            "Ver tabla completa de desglose de costos por escenario", expanded=True
        ):
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
            f"Evaluación del impacto individual de cada parámetro sobre el ahorro neto al variar un ±{d.x_pct:.1f}% ceteris paribus."
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

        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
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

            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            st.markdown("#### Métricas de Desviación y Exactitud")
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

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
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

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
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
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
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
        st.markdown("### Exportación y Artefactos Certificados")
        st.caption(
            "Descargue los cuatro artefactos estáticos generados por el modelo con trazabilidad formal completa."
        )

        if st.session_state.reportes:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if "reporte.xlsx" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-card">
                            <div class="download-card-title">Libro Excel Trazable (reporte.xlsx)</div>
                            <div class="download-card-desc">Contiene todas las hojas de cálculo, fuentes y fórmulas de M0 a M8.</div>
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

                st.markdown(
                    "<div style='height: 0.75rem;'></div>", unsafe_allow_html=True
                )
                if "reporte.md" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-card">
                            <div class="download-card-title">Documento Markdown (reporte.md)</div>
                            <div class="download-card-desc">Reporte ejecutivo listo para documentación técnica o Pull Request.</div>
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
                        <div class="download-card">
                            <div class="download-card-title">Esquema JSON Estricto (resultados.json)</div>
                            <div class="download-card-desc">Estructura máquina de datos con identificación unívoca de fórmulas.</div>
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

                st.markdown(
                    "<div style='height: 0.75rem;'></div>", unsafe_allow_html=True
                )
                if "sensibilidad.png" in st.session_state.reportes:
                    st.markdown(
                        """
                        <div class="download-card">
                            <div class="download-card-title">Gráfico de Tornado (sensibilidad.png)</div>
                            <div class="download-card-desc">Visualización estática de alta resolución generada con Matplotlib.</div>
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
    # Pantalla de bienvenida estructurada
    st.markdown(
        """
        <div class="onboarding-grid">
            <div class="onboarding-card">
                <div class="onboarding-step">Paso 01</div>
                <div class="onboarding-title">Carga Contractual</div>
                <div class="onboarding-text">
                    Suba el libro Excel de 9 hojas desde el panel lateral. El motor valida tipos, rangos, fechas y contratos sin admitir cargas parciales.
                </div>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-step">Paso 02</div>
                <div class="onboarding-title">Cálculo Paramétrico</div>
                <div class="onboarding-text">
                    Estimación determinista de esfuerzo base, duración COCOMO II, desglose de actividades y modelado de fricción por agentes.
                </div>
            </div>
            <div class="onboarding-card">
                <div class="onboarding-step">Paso 03</div>
                <div class="onboarding-title">Decisión con Evidencia</div>
                <div class="onboarding-text">
                    Análisis tripartito de escenarios, cálculo de punto de equilibrio, gráfico tornado y exportación certificada a XLSX, MD y JSON.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "Por favor, sube un archivo Excel válido (.xlsx) desde la barra lateral "
        "para comenzar la estimación. (Podés usar el archivo de prueba listo `ENTRADAS_EXCEL_CASO_REAL.xlsx` ubicado en la raíz del proyecto)."
    )
