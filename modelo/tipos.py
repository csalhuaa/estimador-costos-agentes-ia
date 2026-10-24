"""Data-only contracts from IMPLEMENTACION_MODELO.docx, section 5.

Field names intentionally match the specification. Frozen dataclasses prevent
field reassignment, not mutation of nested dictionaries; consumers must not
modify their arguments.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal

NombreEscenario = Literal["pesimista", "esperado", "optimista"]
Veredicto = Literal["conviene", "no conviene", "no concluyente"]


@dataclass(frozen=True)
class Constantes:
    A: float
    B: float
    C: float
    D: float
    horas_por_pm: float
    sf_nominal: dict[str, float]
    em_nominal: float
    sced_pct_nominal: float


@dataclass(frozen=True)
class Proyecto:
    nombre: str
    moneda: str
    size_ksloc: float
    sf: dict[str, float]
    em: dict[str, float]
    sced_em: float
    sced_pct: float
    c_pm: float
    f: float
    T_meses: float | None
    n_u: int


@dataclass(frozen=True)
class Trio:
    minimo: float
    esperado: float
    maximo: float
    origen: str
    ids_estudios: tuple[str, ...]
    justificacion: str


@dataclass(frozen=True)
class ParametrosIA:
    r: Trio
    rho_rev: Trio
    rho_retr: Trio
    c_api_h: Trio
    delta: Trio
    h_def: Trio
    p_lic: Trio
    h_cap: Trio
    h_int: Trio


@dataclass(frozen=True)
class ValoresIA:
    r: float
    rho_rev: float
    rho_retr: float
    c_api_h: float
    delta: float
    h_def: float
    p_lic: float
    h_cap: float
    h_int: float


@dataclass(frozen=True)
class Estudio:
    id: str
    autores: str
    ano: str
    titulo: str
    doi_url: str
    r_equivalente: float | None
    cumple: str


@dataclass(frozen=True)
class Rubro:
    concepto: str
    horas: float | None
    costo_usd: float
    en_alcance: bool


@dataclass(frozen=True)
class Sprint:
    numero: int
    inicio: date | None
    fin: date | None
    horas_totales: float
    horas_4_actividades: float | None
    licencias: float
    api: float
    capacitacion: float
    integracion: float
    hubo_programacion: bool


@dataclass(frozen=True)
class CasoValidacion:
    rubros: tuple[Rubro, ...]
    sprints: tuple[Sprint, ...]


@dataclass(frozen=True)
class Aviso:
    codigo: str
    hoja: str
    celda: str
    mensaje: str


@dataclass(frozen=True)
class Entradas:
    constantes: Constantes
    proyecto: Proyecto
    parametros: ParametrosIA
    estudios: tuple[Estudio, ...]
    caso: CasoValidacion | None
    avisos: tuple[Aviso, ...]
    supuestos: tuple[str, ...]


@dataclass(frozen=True)
class EstimacionBase:
    sum_sf: float
    E: float
    PM_ns: float
    PM: float
    phi: float
    TDEV: float
    t_h: float
    C_trad: float
    H_trad: float
    T: float


@dataclass(frozen=True)
class CostosAdopcion:
    C_lic: float
    C_cap: float
    C_int: float
    C_fijo: float
    u: float


@dataclass(frozen=True)
class ResultadoEconomico:
    C_adop: float
    ahorro_bruto: float
    ahorro_neto: float
    rbc: float | None
    r_estrella: float
    umbral_global: float
    c_adop_max: float
    margen: float
    recuperacion_meses: float | None
    recupera_dentro_de_T: bool
    C_ia: float


@dataclass(frozen=True)
class Escenario:
    nombre: NombreEscenario
    valores: ValoresIA
    costos: CostosAdopcion
    resultado: ResultadoEconomico


@dataclass(frozen=True)
class FilaSensibilidad:
    parametro: str
    efecto_bajo: float
    efecto_alto: float


@dataclass(frozen=True)
class Decision:
    escenarios: tuple[Escenario, ...]
    sensibilidad: tuple[FilaSensibilidad, ...]
    x_pct: float
    veredicto: Veredicto


@dataclass(frozen=True)
class CostoReal:
    C_presup: float
    C_real: float
    horas_totales: float
    costo_ia_real: float
    H_real_4: float | None
    n_sprints: int


@dataclass(frozen=True)
class Contraste:
    err_estimacion_ia: float
    err_cocomo_vs_presup: float
    desviacion_presup: float
    cumple_exactitud: bool
    decision_estable: bool
    verificacion_cocomo_ok: bool


@dataclass(frozen=True)
class Resultados:
    entradas: Entradas
    base: EstimacionBase
    decision: Decision
    costo_real: CostoReal | None
    contraste: Contraste | None
