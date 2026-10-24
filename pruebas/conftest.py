"""Synthetic/reference inputs; never observations from the actual project."""

import pytest

from modelo.constantes import NOMBRES_EM, constantes_predeterminadas
from modelo.tipos import Constantes, Proyecto


@pytest.fixture
def constantes() -> Constantes:
    return constantes_predeterminadas()


@pytest.fixture
def proyecto(constantes: Constantes) -> Proyecto:
    return Proyecto(
        nombre="32 KSLOC reference fixture",
        moneda="USD",
        size_ksloc=32,
        sf=dict(constantes.sf_nominal),
        em=dict.fromkeys(NOMBRES_EM, constantes.em_nominal),
        sced_em=1,
        sced_pct=100,
        c_pm=1000,
        f=0.59,
        T_meses=None,
        n_u=10,
    )
