"""Interfaz interactiva Streamlit para el estimador de costos COCOMO II con agentes IA.

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

st.set_page_config(
    page_title="Estimador de Costo con Agentes IA",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Estimador de Costo Previo al Proyecto (COCOMO II + Agentes IA)")
st.caption(
    "Herramienta previa al proyecto: evalúa viabilidad económica y contraste empírico sin fórmulas en interfaz."
)

# Barra lateral
st.sidebar.header("Configuración de Entrada")
uploaded_file = st.sidebar.file_uploader(
    "Subir archivo Excel del proyecto (.xlsx)",
    type=["xlsx"],
    help="Debe seguir la plantilla establecida en el contrato de entradas.",
)

x_pct = st.sidebar.slider(
    "Variación para análisis de sensibilidad (±x %)",
    min_value=5.0,
    max_value=50.0,
    value=20.0,
    step=1.0,
    help="Porcentaje para evaluar impacto individual de parámetros sobre el ahorro neto.",
)

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

# Visualización
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
        st.subheader("Veredicto de Decisión")
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
                "La conveniencia depende de los supuestos del escenario; el ahorro neto cambia de signo."
            )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Costo sin agentes (C_trad)", f"{b.C_trad:,.2f} USD")
        col2.metric("Costo con agentes (esperado)", f"{esp.C_ia:,.2f} USD")
        col3.metric("Ahorro neto esperado", f"{esp.ahorro_neto:,.2f} USD")
        rbc_text = f"{esp.rbc:.4f}" if esp.rbc is not None else "N/A"
        col4.metric("Relación Beneficio/Costo (RBC)", rbc_text)

        st.markdown("---")
        st.subheader("Parámetros y Recuperación")
        c1, c2, c3 = st.columns(3)
        c1.write(
            f"**Reducción r vs umbral r\\*:** `{d.escenarios[1].valores.r:.4f}` frente a `{esp.r_estrella:.4f}`"
        )
        if esp.recuperacion_meses is not None:
            dentro_txt = (
                "Sí (dentro de T)" if esp.recupera_dentro_de_T else "No (fuera de T)"
            )
            c2.write(
                f"**Recuperación de inversión:** `{esp.recuperacion_meses:.1f} meses` ({dentro_txt})"
            )
        else:
            c2.write(
                "**Recuperación de inversión:** `No recupera (RBC ≤ 0 o C_adop = 0)`"
            )

        if d.sensibilidad:
            c3.write(f"**Parámetro de mayor efecto:** `{d.sensibilidad[0].parametro}`")

        st.info(
            "ℹ **Aviso**: Los parámetros de agentes provienen de la hoja estudios; "
            "los marcados como supuesto no tienen fuente publicada."
        )

    # 2. Escenarios
    with tabs[1]:
        st.subheader("Comparación de Escenarios")
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
        st.subheader(f"Análisis de Sensibilidad (±{d.x_pct:.1f} %)")
        if (
            st.session_state.reportes
            and "sensibilidad.png" in st.session_state.reportes
        ):
            st.image(
                st.session_state.reportes["sensibilidad.png"],
                caption=f"Impacto sobre ahorro neto al variar cada parámetro en ±{d.x_pct:.1f}%",
                use_container_width=True,
            )

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
        st.subheader("Validación y Contraste Empírico")
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

            st.markdown("---")
            st.write("#### Errores y Criterios de Éxito")
            e1, e2, e3 = st.columns(3)
            e1.write(
                f"**Error estimación IA (F34):** `{ct.err_estimacion_ia * 100:.1f} %`"
            )
            e2.write(
                f"**Error COCOMO vs Presupuesto (F35):** `{ct.err_cocomo_vs_presup * 100:.1f} %`"
            )
            e3.write(
                f"**Desviación presupuestaria (F36):** `{ct.desviacion_presup * 100:.1f} %`"
            )

            ok_exact = (
                "✔ Cumple (≤ 25%)" if ct.cumple_exactitud else "✖ No cumple (> 25%)"
            )
            ok_est = "✔ Decisión estable" if ct.decision_estable else "✖ No estable"
            ok_cocomo = (
                "✔ Verificación COCOMO OK"
                if ct.verificacion_cocomo_ok
                else "✖ Verificación fallida"
            )

            st.write(f"- **Criterio de exactitud (F34 ≤ 0,25):** {ok_exact}")
            st.write(f"- **Criterio de estabilidad de decisión:** {ok_est}")
            st.write(f"- **Verificación COCOMO II con constantes:** {ok_cocomo}")
        else:
            st.info(
                "El libro cargado no contiene datos de caso de validación "
                "(hojas `presupuesto_inicial` y `costo_real_sprint` vacías). "
                "La herramienta operó en modo puramente predictivo (M0 a M5)."
            )

    # 5. Supuestos y fuentes
    with tabs[4]:
        st.subheader("Supuestos Declarados")
        if res.entradas.supuestos:
            for s in res.entradas.supuestos:
                st.write(
                    f"- `{s}`: parámetro basado en supuesto declarado sin respaldo en estudio publicado."
                )
        else:
            st.write(
                "No se registraron supuestos declarados; todos los parámetros provienen de estudios primarios."
            )

        st.markdown("---")
        st.subheader("Estudios Primarios Identificados")
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
            st.markdown("---")
            st.subheader("Avisos del Sistema")
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
        st.subheader("Descarga de Reportes e Instantáneas")
        st.write("Descargue los cuatro artefactos estáticos generados por el modelo:")
        if st.session_state.reportes:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if "reporte.xlsx" in st.session_state.reportes:
                    st.download_button(
                        "📥 Descargar reporte.xlsx (Excel con trazabilidad)",
                        data=st.session_state.reportes["reporte.xlsx"],
                        file_name="reporte.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                if "reporte.md" in st.session_state.reportes:
                    st.download_button(
                        "📥 Descargar reporte.md (Markdown)",
                        data=st.session_state.reportes["reporte.md"],
                        file_name="reporte.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
            with col_d2:
                if "resultados.json" in st.session_state.reportes:
                    st.download_button(
                        "📥 Descargar resultados.json (JSON estricto con fórmulas)",
                        data=st.session_state.reportes["resultados.json"],
                        file_name="resultados.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                if "sensibilidad.png" in st.session_state.reportes:
                    st.download_button(
                        "📥 Descargar sensibilidad.png (Gráfico de barras)",
                        data=st.session_state.reportes["sensibilidad.png"],
                        file_name="sensibilidad.png",
                        mime="image/png",
                        use_container_width=True,
                    )

else:
    st.info(
        "👈 Por favor, sube un archivo Excel válido (.xlsx) desde la barra lateral "
        "para comenzar la estimación."
    )
