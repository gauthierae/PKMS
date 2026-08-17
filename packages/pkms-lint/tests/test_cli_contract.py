"""Tests 1 and 32 — the guards that keep the package publishable.

Spec: 200-po/sprints/sprint-12.md sections A, B, and C.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pkms_lint


def test_version_prints_the_exact_string(run):
    result = run("--version")
    assert result.stdout.strip() == f"pkms-lint {pkms_lint.__version__}"
    assert result.exit_code == 0


def test_the_version_matches_pyproject():
    pyproject = (Path(pkms_lint.__file__).parent / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{pkms_lint.__version__}"' in pyproject


def test_the_source_never_imports_pkms():
    source = Path(pkms_lint.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("import pkms ")
        assert stripped != "import pkms"
        assert not stripped.startswith("from pkms ")
        assert not stripped.startswith("from pkms.")


def test_importing_pkms_lint_never_pulls_in_pkms():
    """Run in a subprocess: the pkms tests import pkms into this one."""
    result = subprocess.run(
        [sys.executable, "-c", "import pkms_lint, sys; print('pkms' in sys.modules)"],
        capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "False"


def test_the_only_third_party_dependency_is_typer():
    pyproject = (Path(pkms_lint.__file__).parent / "pyproject.toml").read_text(encoding="utf-8")
    assert 'dependencies = ["typer>=0.12"]' in pyproject
