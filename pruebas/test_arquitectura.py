"""Structural checks for the pure calculation modules implemented so far."""

import ast
from pathlib import Path

import pytest


@pytest.mark.parametrize("module", ["cocomo", "parametros_ia", "adopcion", "economia"])
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
