"""Structural checks for the pure calculation modules implemented so far."""

import ast
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "module", ["cocomo", "parametros_ia", "adopcion", "economia", "escenarios"]
)
def test_pure_modules_have_no_external_io_or_random_dependencies(module):
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
    # M6/M7 consume case contracts; the M1–M5 no-case guard above stays unchanged.
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
