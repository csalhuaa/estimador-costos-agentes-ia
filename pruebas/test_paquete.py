"""Retained verifier probe: build and use the wheel outside the source tree."""

from email.parser import Parser
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile


def test_wheel_contains_only_the_package_and_runs_the_documented_example(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "source"
    shutil.copytree(
        root,
        source,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
            "build",
            "dist",
            "*.egg-info",
            "salidas",
        ),
    )
    output = tmp_path / "wheels"
    output.mkdir()
    build = (
        "from setuptools.build_meta import build_wheel; build_wheel("
        + repr(str(output))
        + ")"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", build],
        cwd=source,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    wheels = list(output.glob("*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]
    expected_modules = {
        "modelo/" + path.name for path in (root / "modelo").glob("*.py")
    }
    metadata_root = "estimador_costos-0.1.0.dist-info/"
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        assert {
            name for name in names if name.startswith("modelo/")
        } == expected_modules
        assert all(
            name in expected_modules or name.startswith(metadata_root) for name in names
        )
        for name in expected_modules:
            assert archive.read(name) == (root / name).read_bytes()
        metadata = Parser().parsestr(archive.read(metadata_root + "METADATA").decode())
        assert metadata["Name"] == "estimador-costos"
        assert metadata["Version"] == "0.1.0"
        assert metadata["Requires-Python"] == ">=3.11"
        assert set(metadata.get_all("Requires-Dist")) == {
            'pytest==8.4.1; extra == "test"',
            'setuptools==80.9.0; extra == "test"',
        }

    outside = tmp_path / "outside"
    outside.mkdir()
    readme = (root / "README.md").read_text(encoding="utf-8")
    example = readme.split("```python", 1)[1].split("```", 1)[0]
    code = "import sys; sys.path.insert(0, sys.argv[1]); import modelo\n"
    code += example + "\nassert modelo.__file__.startswith(sys.argv[1])"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, str(wheel)],
        cwd=outside,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "PM=132.9109, TDEV=17.3712, USD=132910.95\n",
        "",
    )
