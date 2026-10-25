"""Altair charts that inherit the active Streamlit theme (light or dark)."""

import altair as alt
import pandas as pd

from .formato import etiqueta, usd

GANA = "#2F9E6E"
PIERDE = "#D0453B"
BAJA = "#D9822B"
SUBE = "#4C7BD9"
ORDEN = ["Pesimista", "Esperado", "Optimista"]


def rango_decision(escenarios) -> alt.LayerChart:
    """Net savings per scenario around zero: the core of the decision."""
    filas = [
        {
            "Escenario": e.nombre.capitalize(),
            "Ahorro neto": e.resultado.ahorro_neto,
            "Resultado": "Ahorra" if e.resultado.ahorro_neto >= 0 else "Pierde",
            "Etiqueta": usd(e.resultado.ahorro_neto, signo=True),
        }
        for e in escenarios
    ]
    datos = pd.DataFrame(filas)
    escala = alt.Scale(domain=["Ahorra", "Pierde"], range=[GANA, PIERDE])

    # Dynamic domain margin to keep value labels from colliding with Y-axis scenario names
    valores = [f["Ahorro neto"] for f in filas]
    min_b = min(0.0, min(valores))
    max_b = max(0.0, max(valores))
    span = max(max_b - min_b, 1000.0)
    pad = span * 0.28
    dominio_x = [min_b - pad, max_b + pad]

    base = alt.Chart(datos).encode(
        y=alt.Y(
            "Escenario:N",
            sort=ORDEN,
            title=None,
            axis=alt.Axis(labelFontSize=12, labelPadding=10),
        )
    )
    barras = base.mark_bar(height=20).encode(
        x=alt.X(
            "Ahorro neto:Q",
            title="Ahorro neto frente a no usar agentes (USD)",
            scale=alt.Scale(domain=dominio_x),
            axis=alt.Axis(format=",.0f", tickCount=5),
        ),
        color=alt.Color("Resultado:N", scale=escala, legend=None),
        tooltip=[
            alt.Tooltip("Escenario:N"),
            alt.Tooltip("Etiqueta:N", title="Ahorro neto"),
        ],
    )
    cero = (
        alt.Chart(pd.DataFrame({"x": [0]}))
        .mark_rule(strokeWidth=1.5, opacity=0.8, color="#94A3B8")
        .encode(x="x:Q")
    )
    texto_pos = (
        base.transform_filter(alt.datum["Ahorro neto"] >= 0)
        .mark_text(
            align="left",
            dx=6,
            fontSize=12,
            fontWeight=600,
            font="IBM Plex Mono, monospace",
        )
        .encode(
            x="Ahorro neto:Q",
            text="Etiqueta:N",
            color=alt.Color("Resultado:N", scale=escala, legend=None),
        )
    )
    texto_neg = (
        base.transform_filter(alt.datum["Ahorro neto"] < 0)
        .mark_text(
            align="right",
            dx=-6,
            fontSize=12,
            fontWeight=600,
            font="IBM Plex Mono, monospace",
        )
        .encode(
            x="Ahorro neto:Q",
            text="Etiqueta:N",
            color=alt.Color("Resultado:N", scale=escala, legend=None),
        )
    )
    return (barras + cero + texto_pos + texto_neg).properties(height=170)


def umbral(escenarios) -> alt.LayerChart:
    """Achieved reduction r versus the break-even reduction r* per scenario."""
    filas = [
        {
            "Escenario": e.nombre.capitalize(),
            "r": e.valores.r,
            "r*": e.resultado.r_estrella,
            "Resultado": "Ahorra"
            if e.valores.r >= e.resultado.r_estrella
            else "Pierde",
        }
        for e in escenarios
    ]
    datos = pd.DataFrame(filas)
    base = alt.Chart(datos).encode(y=alt.Y("Escenario:N", sort=ORDEN, title=None))
    tooltip = [
        alt.Tooltip("Escenario:N"),
        alt.Tooltip("r:Q", title="Reducción esperada", format=".1%"),
        alt.Tooltip("r*:Q", title="Reducción mínima necesaria", format=".1%"),
    ]
    escala = alt.Scale(domain=["Ahorra", "Pierde"], range=[GANA, PIERDE])
    tramo = base.mark_rule(strokeWidth=3).encode(
        x=alt.X(
            "r*:Q",
            title="Reducción del esfuerzo reducible",
            axis=alt.Axis(format=".0%"),
            scale=alt.Scale(zero=False, padding=20),
        ),
        x2="r:Q",
        color=alt.Color("Resultado:N", scale=escala, legend=None),
        tooltip=tooltip,
    )
    minimo = base.mark_tick(
        thickness=2.5, size=24, opacity=0.9, color="#94A3B8"
    ).encode(x="r*:Q", tooltip=tooltip)
    logrado = base.mark_point(filled=True, size=110, opacity=1).encode(
        x="r:Q",
        color=alt.Color("Resultado:N", scale=escala, legend=None),
        tooltip=tooltip,
    )
    return (tramo + minimo + logrado).properties(height=170)


def tornado(sensibilidad, x_pct: float) -> alt.Chart:
    """Signed change in net savings when each parameter moves ±x %."""
    orden = [etiqueta(f.parametro) for f in sensibilidad]
    bajar, subir = f"Baja {x_pct:.0f} %", f"Sube {x_pct:.0f} %"
    filas = []
    for fila in sensibilidad:
        for direccion, efecto in ((bajar, fila.efecto_bajo), (subir, fila.efecto_alto)):
            filas.append(
                {
                    "Parámetro": etiqueta(fila.parametro),
                    "Si el parámetro…": direccion,
                    "Cambio": efecto,
                    "Etiqueta": usd(efecto, signo=True),
                }
            )
    datos = pd.DataFrame(filas)
    return (
        alt.Chart(datos)
        .mark_bar(height=11)
        .encode(
            y=alt.Y("Parámetro:N", sort=orden, title=None),
            yOffset=alt.YOffset("Si el parámetro…:N", sort=[bajar, subir]),
            x=alt.X(
                "Cambio:Q",
                title="Cambio en el ahorro neto esperado (USD)",
                axis=alt.Axis(format=",.0f", tickCount=6),
            ),
            color=alt.Color(
                "Si el parámetro…:N",
                scale=alt.Scale(domain=[bajar, subir], range=[BAJA, SUBE]),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip("Parámetro:N"),
                alt.Tooltip("Si el parámetro…:N"),
                alt.Tooltip("Etiqueta:N", title="Cambio en ahorro neto"),
            ],
        )
        .properties(height=max(260, 30 * len(orden)))
    )
