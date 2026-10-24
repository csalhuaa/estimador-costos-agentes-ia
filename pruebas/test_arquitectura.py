"""Structural checks for the pure calculation modules implemented so far."""

import ast
from pathlib import Path


def test_m1_has_no_external_io_or_random_dependencies():
    source = Path(__file__).parents[1] / "modelo" / "cocomo.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    forbidden = {
        "openpyxl",
        "streamlit",
        "matplotlib",
        "random",
        "numpy",
        "scipy",
        "pandas",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not forbidden.intersection(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "input", "round"}
