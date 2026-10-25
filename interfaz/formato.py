"""Display formatting only. No arithmetic beyond presentation scaling."""

from html import escape

ETIQUETAS = {
    "r": "Reducción de esfuerzo (r)",
    "rho_rev": "Horas extra de revisión",
    "rho_retr": "Horas extra de retrabajo",
    "c_api_h": "Costo de API por hora",
    "delta": "Defectos extra por hora",
    "h_def": "Horas por defecto",
    "p_lic": "Licencia mensual",
    "h_cap": "Horas de capacitación",
    "h_int": "Horas de integración",
    "size_ksloc": "Tamaño (KSLOC)",
    "c_pm": "Costo persona-mes",
    "f": "Fracción reducible (f)",
    "n_u": "Usuarios con agentes",
    "T_meses": "Duración prevista",
}


def etiqueta(nombre: str) -> str:
    return ETIQUETAS.get(nombre, nombre)


def usd(valor: float | None, decimales: int = 0, signo: bool = False) -> str:
    if valor is None:
        return "—"
    texto = f"US$ {abs(valor):,.{decimales}f}"
    if valor < 0:
        return f"−{texto}"
    return f"+{texto}" if signo and valor > 0 else texto


def pct(valor: float | None, decimales: int = 1) -> str:
    return "—" if valor is None else f"{valor * 100:,.{decimales}f} %"


def num(valor: float | None, decimales: int = 2) -> str:
    return "—" if valor is None else f"{valor:,.{decimales}f}"


def html(texto: object) -> str:
    return escape(str(texto))
