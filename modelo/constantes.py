"""Defaults transcribed from ENTRADAS_EXCEL.xlsx, constantes!B5:B16."""

from .tipos import Constantes

NOMBRES_EM = (
    "RELY",
    "DATA",
    "CPLX",
    "RUSE",
    "DOCU",
    "TIME",
    "STOR",
    "PVOL",
    "ACAP",
    "PCAP",
    "PCON",
    "APEX",
    "PLEX",
    "LTEX",
    "TOOL",
    "SITE",
)


def constantes_predeterminadas() -> Constantes:
    """Return nominal II.2000 values with an independent factor dictionary."""
    return Constantes(
        A=2.94,
        B=0.91,
        C=3.67,
        D=0.28,
        horas_por_pm=152,
        sf_nominal={
            "PREC": 3.72,
            "FLEX": 3.04,
            "RESL": 4.24,
            "TEAM": 3.29,
            "PMAT": 4.68,
        },
        em_nominal=1,
        sced_pct_nominal=100,
    )
