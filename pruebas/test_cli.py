"""CLI processes run in isolated directories and preserve rejected inputs."""

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from pruebas.fixtures_excel import guardar_sintetico, libro_sintetico

CLI = Path(__file__).resolve().parents[1] / "cli.py"
FILES = {"reporte.xlsx", "reporte.md", "resultados.json", "sensibilidad.png"}


def run_cli(cwd, *args):
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *map(str, args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
        timeout=60,
    )


def test_standalone_verification_needs_no_workbook_and_creates_nothing(tmp_path):
    result = run_cli(tmp_path, "--verificar")
    assert (result.returncode, result.stdout, result.stderr) == (0, "ok\n", "")
    assert list(tmp_path.iterdir()) == []


def test_failed_nominal_verification_reports_revisar(tmp_path, monkeypatch, capsys):
    import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "verificar_cocomo", lambda constants: False, raising=False)
    assert cli.main(["--verificar"]) == 2
    assert capsys.readouterr() == ("revisar\n", "")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "options",
    [("input.xlsx",), ("--entrada", "input.xlsx"), ("--salida", "out"), ("--x", "20")],
)
def test_verification_rejects_explicit_normal_options(tmp_path, options):
    result = run_cli(tmp_path, "--verificar", *options)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "--verificar no admite entradas, salidas ni sensibilidad." in result.stderr
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("same", [False, True])
def test_positional_and_flagged_inputs_are_mutually_exclusive(tmp_path, same):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = sha256(path.read_bytes()).digest()
    result = run_cli(tmp_path, path, "--entrada", path if same else "other.xlsx")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Use una entrada posicional o --entrada, no ambas." in result.stderr
    assert sha256(path.read_bytes()).digest() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("value", ["4", "51", "nan", "inf", "-inf"])
def test_sensitivity_is_finite_and_inclusive_before_pipeline(tmp_path, value):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = path.read_bytes()
    result = run_cli(tmp_path, path, f"--x={value}")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "La sensibilidad debe ser finita y estar entre 5 y 50." in result.stderr
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "input_flag,output_flag,x_flag,percent",
    [
        ("--entrada", "--salida", "--x", 5),
        ("--entradas", "--salidas", "--x_pct", 50),
        ("-e", "-s", "-x", 20),
        ("-e", "-o", "-x", 25),
    ],
)
def test_explicit_aliases_export_four_reports_and_keep_inputs(
    tmp_path, input_flag, output_flag, x_flag, percent
):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = path.read_bytes()
    out = tmp_path / "reports"
    result = run_cli(tmp_path, input_flag, path, output_flag, out, x_flag, percent)
    assert result.returncode == 0
    assert result.stderr == ""
    assert (
        "Veredicto          : CONVIENE\nRobustez           : sensible a los parámetros\n"
        in result.stdout
    )
    assert {p.name for p in out.iterdir()} == FILES
    data = json.loads((out / "resultados.json").read_text(encoding="utf-8"))
    assert data["resumen"]["x_pct"]["valor"] == percent
    assert data["resumen"]["robusta"]["valor"] is False
    assert path.read_bytes() == before


def test_default_exports_and_collision_leave_every_existing_byte_unchanged(tmp_path):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    before = path.read_bytes()
    first = run_cli(tmp_path, path)
    assert first.returncode == 0
    assert first.stderr == ""
    out = tmp_path / "salidas"
    assert {p.name for p in out.iterdir()} == FILES
    saved = {p.name: p.read_bytes() for p in out.iterdir()}
    second = run_cli(tmp_path, path)
    assert second.returncode == 2
    assert "Destino existente o protegido" in second.stderr
    assert {p.name: p.read_bytes() for p in out.iterdir()} == saved
    assert path.read_bytes() == before


def test_valid_rejection_still_returns_zero(tmp_path):
    workbook = libro_sintetico(caso=False)
    for cell in ("D6", "E6", "F6"):
        workbook["parametros_ia"][cell] = 0
    path = tmp_path / "rejection.xlsx"
    workbook.save(path)
    workbook.close()
    before = path.read_bytes()
    result = run_cli(tmp_path, path)
    assert result.returncode == 0
    assert result.stderr == ""
    assert (
        "Veredicto          : NO CONVIENE\nRobustez           : robusta\n"
        in result.stdout
    )
    assert path.read_bytes() == before
    assert {p.name for p in (tmp_path / "salidas").iterdir()} == FILES


def test_workbook_validation_returns_one_without_reports(tmp_path):
    path = guardar_sintetico(tmp_path / "input.xlsx")
    invalid = tmp_path / "bad.xlsx"
    invalid.write_bytes(b"invalid workbook")
    result = run_cli(tmp_path, invalid)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "[E12]" in result.stderr
    assert invalid.read_bytes() == b"invalid workbook"
    assert set(tmp_path.iterdir()) == {path, invalid}


@pytest.mark.parametrize(
    "args", [(), ("--entr", "input.xlsx"), ("--sal", "out"), ("--x_p", "20")]
)
def test_usage_errors_do_not_create_outputs(tmp_path, args):
    result = run_cli(tmp_path, *args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr
    assert list(tmp_path.iterdir()) == []
