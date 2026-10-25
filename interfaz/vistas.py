"""Page sections. Each function renders one part of the decision story."""

import streamlit as st

from . import graficos
from .componentes import franja_proyecto, nota, seccion, tabla
from .formato import etiqueta, html, num, pct, usd
from .iconos import svg

_ESTADO = {
    "conviene": ("ec-pos", "Conviene adoptar", "check_circle"),
    "no conviene": ("ec-neg", "No conviene adoptar", "x_circle"),
    "no concluyente": ("ec-mid", "No concluyente", "exclamation_triangle"),
}


# Empty, error and project context ------------------------------------------------


def inicio() -> None:
    st.markdown(
        """
<div class="ec-empty">
<h3>Suba el libro de entradas para empezar</h3>
<p>El archivo es la plantilla de 9 hojas <code>ENTRADAS_EXCEL.xlsx</code> con las
celdas amarillas completas. Con él, el panel responde:</p>
<ul>
<li>cuánto costaría el proyecto sin agentes y con agentes,</li>
<li>si la decisión se sostiene en los escenarios pesimista y optimista,</li>
<li>qué parámetros conviene medir con más cuidado,</li>
<li>y, si hay datos de sprints, qué tan cerca estuvo la estimación del costo real.</li>
</ul>
</div>
""",
        unsafe_allow_html=True,
    )
    st.info(
        "Por favor, sube un archivo Excel válido (.xlsx) en la barra superior para "
        "comenzar la estimación. Para probar, use `ENTRADAS_EXCEL_CASO_REAL.xlsx`.",
        icon=":material/upload_file:",
    )


def problemas(lista) -> None:
    st.error(
        f"Se encontraron {len(lista)} problemas de validación en el archivo Excel. "
        "No se calculó nada para evitar resultados parciales."
    )
    st.caption("Corrija cada celda indicada en el libro y vuelva a subirlo.")
    st.dataframe(
        [
            {
                "Código": p.codigo,
                "Hoja": p.hoja,
                "Celda": p.celda,
                "Problema": p.mensaje,
            }
            for p in lista
        ],
        use_container_width=True,
        hide_index=True,
    )


def contexto(res, archivo: str | None) -> None:
    p, b = res.entradas.proyecto, res.base
    franja_proyecto(
        [
            ("Proyecto", p.nombre or "Sin nombre"),
            ("Tamaño", f"{num(p.size_ksloc, 1)} KSLOC"),
            ("Costo persona-mes", usd(p.c_pm)),
            ("Usuarios con agentes", str(p.n_u)),
            ("Duración estimada", f"{num(b.TDEV, 1)} meses"),
            ("Archivo", archivo or "—"),
        ]
    )


# 1. Decision ----------------------------------------------------------------------


def decision(res) -> None:
    d, b = res.decision, res.base
    pes, esp, opt = (e.resultado for e in d.escenarios)
    clase, estado, icono_nom = _ESTADO[d.veredicto]
    icono_svg = svg(icono_nom, 20)

    if d.veredicto == "conviene":
        titulo = "Conviene adoptar agentes de IA"
        cuerpo = (
            f"Incluso en el escenario pesimista se ahorran "
            f"<b>{usd(pes.ahorro_neto)}</b>. Con el desempeño esperado, el ahorro "
            f"neto es de <b>{usd(esp.ahorro_neto)}</b> sobre un costo tradicional de "
            f"{usd(b.C_trad)}."
        )
    elif d.veredicto == "no conviene":
        titulo = "No conviene adoptar agentes de IA"
        cuerpo = (
            f"Ni siquiera en el escenario optimista se recupera la inversión: el "
            f"resultado es <b>{usd(opt.ahorro_neto)}</b>. Los costos de licencias, "
            f"API, capacitación y fricción superan las horas ahorradas."
        )
    else:
        titulo = "Decisión no concluyente: depende del rendimiento de los agentes"
        cuerpo = (
            f"Con el desempeño esperado se ahorran <b>{usd(esp.ahorro_neto)}</b>, "
            f"pero en el escenario pesimista se pierden "
            f"<b>{usd(abs(pes.ahorro_neto))}</b>. El resultado cambia de signo entre "
            f"escenarios, así que la conveniencia depende de medir con rigor los "
            f"parámetros críticos de fricción y reducción."
        )

    seccion(
        "Decisión Ejecutiva",
        "Balance económico proyectado combinando COCOMO II y costos integrales de adopción.",
    )

    st.markdown(
        f'<div class="ec-verdict"><span class="ec-state {clase}">{icono_svg} {estado}</span>'
        f"<h3>{titulo}</h3><p>{cuerpo}</p></div>",
        unsafe_allow_html=True,
    )

    # 5 Key Metrics Ledger Strip
    c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
    c1.metric(
        "Costo sin agentes (C_trad)",
        usd(b.C_trad),
        help="Esfuerzo COCOMO II × costo persona-mes. Fórmula F7.",
    )
    c2.metric(
        "Costo con agentes (esperado)",
        usd(esp.C_ia),
        help="Costo tradicional menos el ahorro neto esperado. Fórmula F31.",
    )
    c3.metric(
        "Ahorro neto esperado",
        usd(esp.ahorro_neto, signo=True),
        help="Ahorro bruto en horas menos el costo total de adopción. Fórmula F21.",
    )
    c4.metric(
        "Relación Beneficio/Costo (RBC)",
        num(esp.rbc, 2) if esp.rbc is not None else "N/A",
        help="Ahorro bruto dividido entre el costo de adopción. Mayor que 1 conviene. F22.",
    )
    recup_texto = (
        f"{num(esp.recuperacion_meses, 1)} meses"
        if esp.recuperacion_meses is not None
        else "No recupera"
    )
    c5.metric(
        "Recuperación estimada",
        recup_texto,
        help=f"Meses necesarios para amortizar la inversión en agentes (plazo del proyecto T = {num(b.T, 1)} meses).",
    )

    st.write("")
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown(
            '<div class="ec-chart-title">Rango de Ahorro Neto por Escenario (USD)</div>',
            unsafe_allow_html=True,
        )
        st.altair_chart(graficos.rango_decision(d.escenarios), use_container_width=True)
        st.caption(
            "Ahorro neto por escenario. A la derecha de la línea vertical (cero) se ahorra; a la izquierda representa pérdida financiera."
        )
    with col_der:
        st.markdown(
            '<div class="ec-chart-title">Umbral de Equilibrio de Reducción (r vs r*)</div>',
            unsafe_allow_html=True,
        )
        st.altair_chart(graficos.umbral(d.escenarios), use_container_width=True)
        st.caption(
            "Punto: reducción de esfuerzo esperada (r). Marca vertical: reducción mínima indispensable para no perder dinero (r*)."
        )

    r = d.escenarios[1].valores.r
    supera = r >= esp.r_estrella
    lectura = (
        f"Para no perder dinero, los agentes deben eliminar al menos el "
        f"<b>{pct(esp.r_estrella)}</b> del esfuerzo reducible (r*). La evidencia "
        f"indica <b>{pct(r)}</b> en el escenario esperado, "
        + (
            "lo cual supera el umbral de equilibrio."
            if supera
            else "por debajo del mínimo indispensable."
        )
    )
    if esp.recuperacion_meses is not None:
        plazo = "dentro" if esp.recupera_dentro_de_T else "fuera"
        lectura += (
            f"<br><br>La inversión se recupera en "
            f"<b>{num(esp.recuperacion_meses, 1)} meses</b>, {plazo} del plazo de "
            f"{num(b.T, 1)} meses."
        )
    else:
        lectura += "<br><br>Con estos valores la inversión no se recupera en el plazo del proyecto."
    nota("Lectura integrada del umbral de rentabilidad", lectura)


# 2. Scenarios ---------------------------------------------------------------------


def escenarios(res) -> None:
    d = res.decision
    seccion(
        "Comparación de Escenarios (Pesimista · Esperado · Optimista)",
        "Los tres escenarios combinan el mínimo, la mediana y el máximo de cada "
        "parámetro de la hoja parametros_ia. El costo tradicional es el mismo en los tres.",
    )
    e = d.escenarios

    def fila(nombre, valores, clase=""):
        return ([html(nombre), *valores], clase)

    def rbc(x):
        return num(x.resultado.rbc, 2) if x.resultado.rbc is not None else "N/A"

    def recup(x):
        m = x.resultado.recuperacion_meses
        return "No recupera" if m is None else f"{num(m, 1)} meses"

    tabla(
        ["", "Pesimista", "Esperado", "Optimista"],
        [
            fila("Reducción de esfuerzo (r)", [pct(x.valores.r) for x in e]),
            fila(
                "Reducción mínima necesaria (r*)",
                [pct(x.resultado.r_estrella) for x in e],
            ),
            fila(
                "Costo fijo de adopción<small>licencias, capacitación, integración</small>",
                [usd(x.costos.C_fijo) for x in e],
            ),
            fila(
                "Costo variable por hora delegada<small>revisión, retrabajo, API, defectos</small>",
                [usd(x.costos.u, 2) for x in e],
            ),
            fila("Costo total de adopción", [usd(x.resultado.C_adop) for x in e]),
            fila("Ahorro bruto en horas", [usd(x.resultado.ahorro_bruto) for x in e]),
            fila(
                "Ahorro neto",
                [
                    f'<span class="{"ec-pos" if x.resultado.ahorro_neto >= 0 else "ec-neg"}">'
                    f"{usd(x.resultado.ahorro_neto, signo=True)}</span>"
                    for x in e
                ],
                "ec-total",
            ),
            fila("Costo con agentes", [usd(x.resultado.C_ia) for x in e]),
            fila("Relación beneficio/costo", [rbc(x) for x in e]),
            fila("Recuperación de la inversión", [recup(x) for x in e]),
        ],
    )


# 3. Sensitivity -------------------------------------------------------------------


def sensibilidad(res) -> None:
    d = res.decision
    seccion(
        f"Sensibilidad Paramétrica (±{d.x_pct:.0f} %)",
        "Impacto individual en el ahorro neto esperado si un solo parámetro sube o baja, "
        "dejando el resto igual. Ajuste el porcentaje en el control superior.",
    )
    st.info(
        f"**¿Para qué sirve este análisis?** Simula qué ocurriría si las estimaciones "
        f"iniciales se desvían un ±{d.x_pct:.0f}%. No modifica los costos base del caso "
        f"esperado, sino que revela qué parámetros tienen mayor impacto económico "
        f"para priorizar su calibración.",
        icon=":material/tune:",
    )
    grafico, texto = st.columns([7, 4], gap="large")
    with grafico:
        st.altair_chart(
            graficos.tornado(d.sensibilidad, d.x_pct), use_container_width=True
        )
    with texto:
        top = d.sensibilidad[:3]
        items = "".join(
            f"<li><b>{html(etiqueta(f.parametro))}</b>: entre "
            f"{usd(min(f.efecto_bajo, f.efecto_alto), signo=True)} y "
            f"{usd(max(f.efecto_bajo, f.efecto_alto), signo=True)}</li>"
            for f in top
        )
        nota(
            "Factores de mayor apalancamiento",
            "Las barras más largas son los parámetros que más mueven la decisión. "
            "Conviene medir y calibrar estos factores con especial atención:"
            f"<ul style='margin:0.6rem 0 0;padding-left:1.1rem'>{items}</ul>",
        )
    with st.expander("Ver tabla completa de sensibilidad"):
        st.dataframe(
            [
                {
                    "Parámetro": etiqueta(f.parametro),
                    "Símbolo": f.parametro,
                    f"Si baja {d.x_pct:.0f} %": usd(f.efecto_bajo, signo=True),
                    f"Si sube {d.x_pct:.0f} %": usd(f.efecto_alto, signo=True),
                }
                for f in d.sensibilidad
            ],
            use_container_width=True,
            hide_index=True,
        )


# 4. Validation against actual data ------------------------------------------------


def validacion(res) -> None:
    seccion(
        "Validación con datos reales",
        "Compara el presupuesto original del equipo, la estimación de esta "
        "herramienta y lo que realmente se gastó en los sprints.",
    )
    if res.contraste is None or res.costo_real is None:
        st.info(
            "El libro cargado no contiene datos de caso de validación (hojas "
            "presupuesto_inicial y costo_real_sprint vacías). La herramienta operó "
            "en modo puramente predictivo (M0 a M5).",
            icon=":material/analytics:",
        )
        return

    cr, ct = res.costo_real, res.contraste
    esp = res.decision.escenarios[1].resultado
    a, b, c = st.columns(3, gap="medium")
    a.metric("Presupuesto inicial del equipo", usd(cr.C_presup), help="Fórmula F32.")
    b.metric("Estimación con agentes", usd(esp.C_ia), help="Fórmula F31.")
    c.metric("Costo real registrado", usd(cr.C_real), help="Fórmula F33.")

    def marca(ok: bool, si: str, no: str) -> str:
        ico = svg("check_circle", 14) if ok else svg("x_circle", 14)
        txt = si if ok else no
        return f'<span class="{"ec-pos" if ok else "ec-neg"}">{ico} {txt}</span>'

    st.write("")
    tabla(
        ["Criterio", "Valor", "Lectura"],
        [
            (
                [
                    "Error de la estimación frente al costo real<small>F34 · meta ≤ 25 %</small>",
                    pct(ct.err_estimacion_ia),
                    marca(ct.cumple_exactitud, "Cumple", "No cumple"),
                ],
                "",
            ),
            (
                [
                    "Diferencia COCOMO frente al presupuesto<small>F35</small>",
                    pct(ct.err_cocomo_vs_presup),
                    "Referencia",
                ],
                "",
            ),
            (
                [
                    "Desvío del presupuesto frente al real<small>F36</small>",
                    pct(ct.desviacion_presup),
                    "Referencia",
                ],
                "",
            ),
            (
                [
                    "Estabilidad de la decisión",
                    "—",
                    marca(ct.decision_estable, "Estable", "Inestable"),
                ],
                "",
            ),
            (
                [
                    "Verificación de COCOMO II con el caso del manual",
                    "—",
                    marca(ct.verificacion_cocomo_ok, "Correcta", "Fallida"),
                ],
                "",
            ),
        ],
    )


# 5. Evidence ----------------------------------------------------------------------


def evidencia(res) -> None:
    e = res.entradas
    seccion(
        "Evidencia y supuestos",
        "De dónde sale cada parámetro de los agentes. Los supuestos declarados no "
        "tienen un estudio publicado que los respalde y deben leerse con cautela.",
    )
    st.info(
        "Los parámetros de agentes provienen de la hoja estudios; los marcados como "
        "supuesto no tienen fuente publicada.",
        icon=":material/menu_book:",
    )
    par = e.parametros
    nombres = (
        "r",
        "rho_rev",
        "rho_retr",
        "c_api_h",
        "delta",
        "h_def",
        "p_lic",
        "h_cap",
        "h_int",
    )
    st.dataframe(
        [
            {
                "Parámetro": etiqueta(n),
                "Mínimo": getattr(par, n).minimo,
                "Esperado": getattr(par, n).esperado,
                "Máximo": getattr(par, n).maximo,
                "Origen": getattr(par, n).origen,
                "Estudios": "; ".join(getattr(par, n).ids_estudios) or "—",
                "Justificación": getattr(par, n).justificacion,
            }
            for n in nombres
        ],
        use_container_width=True,
        hide_index=True,
    )
    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        st.markdown("**Estudios primarios**")
        if e.estudios:
            st.dataframe(
                [
                    {
                        "Id": s.id,
                        "Autores": s.autores,
                        "Año": s.ano,
                        "Título": s.titulo,
                        "r equivalente": s.r_equivalente,
                        "Cumple criterios": s.cumple,
                        "Enlace": s.doi_url or None,
                    }
                    for s in e.estudios
                ],
                use_container_width=True,
                hide_index=True,
                column_config={"Enlace": st.column_config.LinkColumn("Enlace")},
            )
        else:
            st.caption("La hoja estudios no tiene estudios registrados.")
    with derecha:
        st.markdown("**Avisos del motor**")
        if e.avisos:
            st.dataframe(
                [
                    {
                        "Código": a.codigo,
                        "Celda": f"{a.hoja}!{a.celda}".rstrip("!"),
                        "Aviso": a.mensaje,
                    }
                    for a in e.avisos
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("Sin avisos.")


# 6. Export ------------------------------------------------------------------------

_DESCARGAS = (
    (
        "reporte.xlsx",
        "Libro Excel",
        "Todas las cifras con su fórmula y celda de origen.",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    (
        "reporte.md",
        "Informe en texto",
        "Resumen legible para documentación o revisión.",
        "text/markdown",
    ),
    (
        "resultados.json",
        "Datos estructurados",
        "Para integrar con otras herramientas.",
        "application/json",
    ),
    (
        "sensibilidad.png",
        "Gráfico de sensibilidad",
        "Imagen estática para informes.",
        "image/png",
    ),
)


def exportar(reportes: dict | None) -> None:
    seccion("Exportar", "Los mismos resultados en cuatro formatos estáticos.")
    if not reportes:
        return
    columnas = st.columns(4, gap="medium")
    for columna, (archivo, titulo, detalle, mime) in zip(columnas, _DESCARGAS):
        with columna:
            st.markdown(f"**{titulo}**")
            st.caption(detalle)
            if archivo in reportes:
                st.download_button(
                    f"Descargar {archivo}",
                    data=reportes[archivo],
                    file_name=archivo,
                    mime=mime,
                    icon=":material/download:",
                    use_container_width=True,
                )
