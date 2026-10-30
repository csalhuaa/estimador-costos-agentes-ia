"""Binary F30 contract and propagation, without calibrating financial inputs."""

from copy import deepcopy
from dataclasses import fields, replace
from pathlib import Path
from itertools import product
from hashlib import sha256
import os
import subprocess
import sys
from typing import get_args

import pytest

from modelo.escenarios import decidir
from modelo.contraste import contrastar
from modelo.pipeline import ejecutar
from modelo.tipos import CostoReal, Decision, Veredicto
from pruebas.fixtures_excel import guardar_sintetico, resultados_sinteticos


@pytest.fixture
def scenarios(tmp_path):
    return resultados_sinteticos(
        guardar_sintetico(tmp_path / "input.xlsx")
    ).decision.escenarios


@pytest.mark.parametrize(
    "nets, expected",
    [
        ((1, 2, 3), ("conviene", True)),
        ((-3, -2, -1), ("no conviene", True)),
        ((-1, 1, 2), ("conviene", False)),
        ((-1, -1, 2), ("no conviene", False)),
        ((-1, 0, 1), ("no conviene", False)),
        ((-1, 0, 0), ("no conviene", True)),
        ((0, 0, 0), ("no conviene", True)),
        ((-0.0, -0.0, -0.0), ("no conviene", True)),
        ((-0.004999, 0.004999, 0), ("no conviene", True)),
        ((-0.005, 0.005, 0.005), ("conviene", False)),
        ((-0.005, -0.005, 0), ("no conviene", True)),
        ((0.005, 0.005, 0.005), ("conviene", True)),
        ((-39537.45, -3024.73, 19969.92), ("no conviene", False)),
    ],
)
def test_named_decision_preserves_every_raw_number(scenarios, nets, expected, capsys):
    cases = tuple(
        replace(s, resultado=replace(s.resultado, ahorro_neto=n))
        for s, n in zip(scenarios, nets)
    )
    before = deepcopy(cases)
    assert decidir(cases) == expected
    assert decidir(tuple(reversed(cases))) == expected
    assert cases == before
    assert tuple(s.resultado.ahorro_neto for s in cases) == nets
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("nets", list(product((-1, 0, 1), repeat=3)))
def test_all_sign_combinations_agree_on_effective_recommendations(scenarios, nets):
    cases = tuple(
        replace(s, resultado=replace(s.resultado, ahorro_neto=n))
        for s, n in zip(scenarios, nets)
    )
    assert decidir(cases) == (
        "conviene" if nets[1] > 0 else "no conviene",
        len({n > 0 for n in nets}) == 1,
    )


@pytest.mark.parametrize(
    "names",
    [
        (),
        ("pesimista",),
        ("pesimista", "esperado"),
        ("pesimista", "esperado", "esperado"),
        ("pesimista", "esperado", "otro"),
        ("pesimista", "esperado", "optimista", "optimista"),
    ],
)
def test_missing_duplicate_or_unknown_scenarios_are_programmer_errors(scenarios, names):
    cases = tuple(replace(scenarios[0], nombre=name) for name in names)
    before = deepcopy(cases)
    with pytest.raises(ValueError):
        decidir(cases)
    assert cases == before


def test_binary_contract_requires_canonical_boolean():
    assert get_args(Veredicto) == ("conviene", "no conviene")
    assert [f.name for f in fields(Decision)][-2:] == ["veredicto", "robusta"]
    with pytest.raises(TypeError):
        Decision((), (), 20, "conviene")


@pytest.mark.parametrize("robust", [False, True])
@pytest.mark.parametrize("verified", [False, True])
@pytest.mark.parametrize("agent, accurate", [(100, True), (50, False)])
def test_m7_transports_boolean_without_gating_independent_flags(
    robust, verified, agent, accurate
):
    result = contrastar(
        100, agent, CostoReal(100, 100, 1, 0, None, 1), robust, verified
    )
    assert result.decision_estable is robust
    assert result.verificacion_cocomo_ok is verified
    assert result.cumple_exactitud is accurate
    assert (
        result.err_estimacion_ia,
        result.err_cocomo_vs_presup,
        result.desviacion_presup,
    ) == (0 if accurate else 0.5, 0, 0)


def test_unchanged_synthetic_pipeline_transports_one_boolean(tmp_path):
    result = ejecutar(guardar_sintetico(tmp_path / "input.xlsx"))
    assert result.decision.escenarios[1].resultado.ahorro_neto == pytest.approx(
        7400.1115, abs=0.0001
    )
    assert (result.decision.veredicto, result.decision.robusta) == ("conviene", False)
    assert result.contraste.decision_estable is result.decision.robusta


@pytest.mark.parametrize(
    "verdict, robust", [("conviene", False), ("no conviene", True)]
)
def test_cli_success_is_independent_of_verdict_and_keeps_input(
    tmp_path, monkeypatch, capsys, verdict, robust
):
    import cli

    monkeypatch.chdir(tmp_path)
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = sha256(path.read_bytes()).digest()
    result = ejecutar(path)
    changed = replace(
        result, decision=replace(result.decision, veredicto=verdict, robusta=robust)
    )
    monkeypatch.setattr(cli, "ejecutar", lambda ruta, x_pct: changed)
    assert cli.main([str(path)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert (
        f"Veredicto          : {verdict.upper()}\nRobustez           : {'robusta' if robust else 'sensible a los parámetros'}\n"
        in output.out
    )
    assert sha256(path.read_bytes()).digest() == before
    assert set(tmp_path.iterdir()) == {path, tmp_path / "salidas"}


def test_cli_subprocess_preserves_positive_synthetic_reference(tmp_path):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = sha256(path.read_bytes()).digest()
    run = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path(__file__).resolve().parents[1] / "cli.py"),
            str(path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
    )
    assert run.returncode == 0
    assert run.stderr == ""
    assert (
        "Veredicto          : CONVIENE\nRobustez           : sensible a los parámetros\n"
        in run.stdout
    )
    assert "7,400.11 USD" in run.stdout
    assert sha256(path.read_bytes()).digest() == before
    assert set(tmp_path.iterdir()) == {path, tmp_path / "salidas"}


def test_maintained_text_has_no_retired_term():
    root = Path(__file__).resolve().parents[1]
    excluded = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".codegraph",
        "salidas",
    }
    pattern = "con" + "cluyente"
    matches = [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.suffix in {".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml"}
        and not excluded.intersection(p.relative_to(root).parts)
        and pattern in p.read_text(encoding="utf-8").lower()
    ]
    assert matches == []
