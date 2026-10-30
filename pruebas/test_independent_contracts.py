"""Retained independent decision, propagation and CLI regressions."""

from dataclasses import asdict, replace
from itertools import permutations, product
from pathlib import Path
import subprocess
import sys

import pytest

from modelo.contraste import contrastar
from modelo.escenarios import decidir
from modelo.pipeline import ejecutar

ROOT = Path(__file__).resolve().parents[1]


def test_independent_decision_matrix_and_raw_invariance():
    template = ejecutar(ROOT / "datos/ejemplo_dorado.xlsx").decision.escenarios
    cases = [
        (-1, False),
        (-0.005, False),
        (-0.004999, False),
        (0, False),
        (0.004999, False),
        (0.005, True),
        (1, True),
    ]
    for triple in product(cases, repeat=3):
        scenarios = tuple(
            replace(s, resultado=replace(s.resultado, ahorro_neto=value))
            for s, (value, _) in zip(template, triple)
        )
        before = [asdict(s) for s in scenarios]
        expected = (
            "conviene" if triple[1][1] else "no conviene",
            len({positive for _, positive in triple}) == 1,
        )
        for order in permutations(scenarios):
            assert decidir(order) == expected
        assert [asdict(s) for s in scenarios] == before
    for invalid in [(), template[:2], (template[0], template[0], template[2])]:
        with pytest.raises(
            ValueError, match="^Expected exactly one scenario of each canonical name$"
        ):
            decidir(invalid)


def test_published_unit_golden_pipeline_and_m7_transport():
    r = ejecutar(ROOT / "datos/ejemplo_dorado.xlsx")
    assert (r.decision.veredicto, r.decision.robusta) == ("conviene", False)
    assert round(r.decision.escenarios[1].resultado.ahorro_neto, 2) == 7400.11
    published = tuple(
        replace(s, resultado=replace(s.resultado, ahorro_neto=value))
        for s, value in zip(r.decision.escenarios, (-39537.45, -3024.73, 19969.92))
    )
    assert decidir(published) == ("no conviene", False)
    for robust, verified in product((False, True), repeat=2):
        c = contrastar(
            r.base.C_trad,
            r.decision.escenarios[1].resultado.C_ia,
            r.costo_real,
            robust,
            verified,
        )
        assert c.decision_estable is robust
        assert c.verificacion_cocomo_ok is verified
        assert c.err_estimacion_ia == r.contraste.err_estimacion_ia


def test_standalone_verification_and_rejected_input_preservation(tmp_path):
    def run(*args):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "cli.py"), *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

    result = run("--verificar")
    assert (result.returncode, result.stdout, result.stderr) == (0, "ok\n", "")
    assert not list(tmp_path.iterdir())
    input_file = tmp_path / "input.xlsx"
    original = (ROOT / "datos/ejemplo_dorado.xlsx").read_bytes()
    input_file.write_bytes(original)
    result = run(str(input_file), "--entrada", str(input_file))
    assert result.returncode == 2 and result.stdout == ""
    assert result.stderr.splitlines()[-1] == (
        "cli.py: error: Use una entrada posicional o --entrada, no ambas."
    )
    assert input_file.read_bytes() == original
    assert list(tmp_path.iterdir()) == [input_file]
