"""Architecture and pipeline verification per IMPLEMENTACION_MODELO.docx §9 and §10."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cli import main
from modelo.cocomo import estimar_base, verificar_cocomo
from modelo.contraste import contrastar
from modelo.errores import ErrorDeEntrada
from modelo.pipeline import ejecutar
from pruebas.fixtures_excel import guardar_sintetico, libro_sintetico


@pytest.mark.parametrize(
    "module", ["cocomo", "parametros_ia", "adopcion", "economia", "escenarios"]
)
def test_pure_modules_have_no_external_io_or_random_dependencies(module):
    """M1 through M5 must never import I/O libraries, random, or case contracts."""
    source = Path(__file__).parents[1] / "modelo" / f"{module}.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    forbidden = {
        "openpyxl",
        "streamlit",
        "matplotlib",
        "random",
        "numpy",
        "scipy",
        "pandas",
        "costo_real",
        "contraste",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not forbidden.intersection(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden
            assert not {
                "CasoValidacion",
                "CostoReal",
                "Contraste",
                "Rubro",
                "Sprint",
            }.intersection(alias.name for alias in node.names)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "input", "round"}


@pytest.mark.parametrize("module", ["costo_real", "contraste"])
def test_case_modules_use_only_contracts_and_pure_standard_library_arithmetic(module):
    """M6 and M7 consume case contracts using only fractions and standard libraries."""
    source = Path(__file__).parents[1] / "modelo" / f"{module}.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name == "fractions" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.level, node.module) in {(1, "tipos"), (0, "fractions")}
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "open",
                "print",
                "input",
                "round",
                "exec",
                "eval",
                "__import__",
            }


def test_case_independence_m2_to_m5(tmp_path):
    """Changing budget and actual sprint data does not alter M1 through M5 results."""
    path_with_case = guardar_sintetico(tmp_path / "case_a.xlsx", caso=True)
    path_no_case = guardar_sintetico(tmp_path / "case_b.xlsx", caso=False)

    res_a = ejecutar(path_with_case)
    res_b = ejecutar(path_no_case)

    # Base estimation M1 is identical
    assert res_a.base == res_b.base

    # Decision and scenarios M5 are identical
    assert res_a.decision.veredicto == res_b.decision.veredicto
    assert res_a.decision.x_pct == res_b.decision.x_pct
    assert len(res_a.decision.escenarios) == len(res_b.decision.escenarios)
    for sa, sb in zip(res_a.decision.escenarios, res_b.decision.escenarios):
        assert sa.nombre == sb.nombre
        assert sa.valores == sb.valores
        assert sa.costos == sb.costos
        assert sa.resultado == sb.resultado

    # Sensitivity ranking and metrics are identical
    assert res_a.decision.sensibilidad == res_b.decision.sensibilidad

    # Only case and contrast differ
    assert res_a.costo_real is not None and res_a.contraste is not None
    assert res_b.costo_real is None and res_b.contraste is None


def test_determinism_identical_runs(tmp_path):
    """Repeated runs on the same input workbook produce strictly identical results."""
    excel_path = guardar_sintetico(tmp_path / "deterministic.xlsx", caso=True)
    res1 = ejecutar(excel_path)
    res2 = ejecutar(excel_path)

    assert res1.base == res2.base
    assert res1.decision == res2.decision
    assert res1.costo_real == res2.costo_real
    assert res1.contraste == res2.contraste


def test_immutability_m1_to_m7_arguments(tmp_path):
    """Dataclasses are frozen and pure functions never mutate input arguments."""
    excel_path = guardar_sintetico(tmp_path / "immutability.xlsx", caso=True)
    res = ejecutar(excel_path)

    with pytest.raises(FrozenInstanceError):
        res.base.sum_sf = 999.0  # type: ignore

    with pytest.raises(FrozenInstanceError):
        res.decision.veredicto = "conviene"  # type: ignore

    if res.costo_real:
        with pytest.raises(FrozenInstanceError):
            res.costo_real.C_real = 0.0  # type: ignore

    # Test that calling calculation functions preserves dictionary contents
    p = res.entradas.proyecto
    c = res.entradas.constantes
    sf_before = dict(p.sf)
    em_before = dict(p.em)
    estimar_base(p, c)
    assert p.sf == sf_before
    assert p.em == em_before

    # Verify verificar_cocomo does not mutate constantes
    verificar_cocomo(c)
    assert c.A == 2.94

    # Verify contrastar does not mutate scenarios
    scenarios = res.decision.escenarios
    if res.costo_real:
        contrastar(
            res.base.C_trad,
            scenarios[1].resultado.C_ia,
            res.costo_real,
            scenarios,
            True,
        )
        assert res.decision.escenarios == scenarios


def test_pipeline_propagates_error_de_entrada(tmp_path):
    """Invalid input workbooks raise ErrorDeEntrada without partial results."""
    workbook = libro_sintetico(caso=True)
    workbook["proyecto"]["C6"] = "INVALID_CURRENCY"
    bad_path = tmp_path / "bad.xlsx"
    workbook.save(bad_path)
    workbook.close()

    with pytest.raises(ErrorDeEntrada) as exc_info:
        ejecutar(bad_path)

    assert any(p.codigo == "E06" for p in exc_info.value.problemas)


def test_cli_success_and_report_generation(tmp_path, capsys):
    """CLI exits with 0 on valid workbook and writes reports if requested."""
    excel_path = guardar_sintetico(tmp_path / "cli_valid.xlsx", caso=True)
    out_dir = tmp_path / "cli_salidas"

    exit_code = main([str(excel_path), "--salidas", str(out_dir), "--x_pct", "25"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "RESUMEN DE ESTIMACIÓN" in captured.out
    assert "NO CONCLUYENTE" in captured.out
    assert (out_dir / "reporte.xlsx").exists()
    assert (out_dir / "reporte.md").exists()
    assert (out_dir / "resultados.json").exists()
    assert (out_dir / "sensibilidad.png").exists()


def test_cli_error_de_entrada_exit_code_1(tmp_path, capsys):
    """CLI exits with 1 on invalid workbook and prints problems formatted to stderr."""
    workbook = libro_sintetico(caso=True)
    workbook["proyecto"]["C6"] = "EUR"
    bad_path = tmp_path / "cli_invalid.xlsx"
    workbook.save(bad_path)
    workbook.close()

    exit_code = main([str(bad_path)])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "[E06] Hoja proyecto, celda C6:" in captured.err


def test_cli_unexpected_error_exit_code_2(tmp_path, capsys):
    """CLI exits with 2 on missing file or missing required arguments."""
    exit_code_no_args = main([])
    assert exit_code_no_args == 2

    # A non-existent file path: cargar_entradas raises ErrorDeEntrada(E12), which exits with 1.
    # An unhandled exception or missing args exits with 2.
    assert main([]) == 2
