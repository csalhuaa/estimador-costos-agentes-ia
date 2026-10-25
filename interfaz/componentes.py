"""Small presentational building blocks shared by the views."""

import streamlit as st

from .formato import html


def encabezado() -> None:
    izquierda, derecha = st.columns([5, 1.4], vertical_alignment="bottom")
    with izquierda:
        st.markdown(
            '<div class="ec-mast">'
            "<h1>Estimador de Costo Previo al Proyecto</h1>"
            "<p>¿Conviene incorporar agentes de IA al desarrollo? Compara el costo "
            "estimado con COCOMO II contra el costo con agentes, en tres escenarios "
            "y con la evidencia que lo respalda.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with derecha:
        with st.popover(
            "Cómo leer el panel", icon=":material/help:", use_container_width=True
        ):
            glosario()


def glosario() -> None:
    st.markdown(
        """
**Costo sin agentes** · lo que costaría el proyecto según COCOMO II, sin IA.

**Costo con agentes** · costo tradicional menos el ahorro neto de usar agentes.

**Ahorro neto** · horas ahorradas en codificación y pruebas, menos licencias,
API, capacitación, integración, revisión extra y corrección de defectos.

**RBC** · relación beneficio/costo. Mayor que 1: cada dólar invertido en
agentes devuelve más de un dólar.

**r** · fracción del esfuerzo reducible que los agentes eliminan, según los estudios.

**r\\*** · reducción mínima necesaria para no perder dinero. Si r supera r\\*, se ahorra.

**Escenarios** · pesimista, esperado y optimista usan el mínimo, la mediana y el
máximo de cada parámetro.

**Sensibilidad** · cuánto cambia el ahorro si un parámetro sube o baja un x %,
dejando todo lo demás igual.

El tema claro u oscuro se cambia en el menú ⋮ › *Settings*.
"""
    )


def seccion(titulo: str, descripcion: str = "") -> None:
    texto = f"<p>{html(descripcion)}</p>" if descripcion else ""
    st.markdown(
        f'<div class="ec-sec"><h2>{html(titulo)}</h2>{texto}</div>',
        unsafe_allow_html=True,
    )


def franja_proyecto(pares: list[tuple[str, str]]) -> None:
    celdas = "".join(
        f"<div><span>{html(k)}</span> <b>{html(v)}</b></div>" for k, v in pares
    )
    st.markdown(f'<div class="ec-strip">{celdas}</div>', unsafe_allow_html=True)


def nota(titulo: str, cuerpo_html: str) -> None:
    """Reading note. ``cuerpo_html`` must already be escaped by the caller."""
    st.markdown(
        f'<div class="ec-note-label">{html(titulo)}</div>'
        f'<div class="ec-note">{cuerpo_html}</div>',
        unsafe_allow_html=True,
    )


def tabla(encabezados: list[str], filas: list[tuple[list[str], str]]) -> None:
    """Ledger table. Each row is (cells, css_class); cells must be pre-escaped."""
    cabeza = "".join(f"<th>{html(h)}</th>" for h in encabezados)
    cuerpo = "".join(
        f'<tr class="{clase}">' + "".join(f"<td>{c}</td>" for c in celdas) + "</tr>"
        for celdas, clase in filas
    )
    st.markdown(
        f'<div class="ec-table"><table><thead><tr>{cabeza}</tr></thead>'
        f"<tbody>{cuerpo}</tbody></table></div>",
        unsafe_allow_html=True,
    )
