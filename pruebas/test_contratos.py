"""Contracts from IMPLEMENTACION_MODELO.docx, sections 5 and 8."""

from dataclasses import FrozenInstanceError, is_dataclass
from importlib import import_module

import pytest


def test_all_specified_contracts_are_frozen_dataclasses():
    tipos = import_module("modelo.tipos")
    names = (
        "Constantes",
        "Proyecto",
        "Trio",
        "ParametrosIA",
        "ValoresIA",
        "Estudio",
        "Rubro",
        "Sprint",
        "CasoValidacion",
        "Aviso",
        "Entradas",
        "EstimacionBase",
        "CostosAdopcion",
        "ResultadoEconomico",
        "Escenario",
        "FilaSensibilidad",
        "Decision",
        "CostoReal",
        "Contraste",
        "Resultados",
    )
    for name in names:
        contract = getattr(tipos, name)
        assert is_dataclass(contract), name
        assert contract.__dataclass_params__.frozen, name

    aviso = tipos.Aviso("A01", "proyecto", "C32", "Assumption to document")
    with pytest.raises(FrozenInstanceError):
        aviso.codigo = "A99"


def test_nominal_defaults_match_workbook_constants():
    module = import_module("modelo.constantes")
    c = module.constantes_predeterminadas()
    assert (c.A, c.B, c.C, c.D, c.horas_por_pm) == (2.94, 0.91, 3.67, 0.28, 152)
    assert c.sf_nominal == {
        "PREC": 3.72,
        "FLEX": 3.04,
        "RESL": 4.24,
        "TEAM": 3.29,
        "PMAT": 4.68,
    }
    assert c.em_nominal == 1
    assert c.sced_pct_nominal == 100
    assert module.NOMBRES_EM == (
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


def test_default_factor_dictionaries_are_not_shared():
    module = import_module("modelo.constantes")
    first = module.constantes_predeterminadas()
    first.sf_nominal["PREC"] = 99
    assert module.constantes_predeterminadas().sf_nominal["PREC"] == 3.72


def test_error_transports_every_problem_with_its_location():
    module = import_module("modelo.errores")
    problems = [
        module.Problema(
            "E01", "proyecto", "C31", "Campo obligatorio vacío (valor: None)."
        ),
        module.Problema(
            "E03", "proyecto", "C32", "f debe estar entre 0 y 1 (valor: 2)."
        ),
    ]
    expected = tuple(problems)
    with pytest.raises(module.ErrorDeEntrada) as caught:
        raise module.ErrorDeEntrada(problems)

    problems.clear()
    assert caught.value.problemas == expected
    assert str(caught.value) == (
        "[E01] Hoja proyecto, celda C31: Campo obligatorio vacío (valor: None).\n"
        "[E03] Hoja proyecto, celda C32: f debe estar entre 0 y 1 (valor: 2)."
    )
    with pytest.raises(FrozenInstanceError):
        expected[0].celda = "C99"
