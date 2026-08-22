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


def test_the_docs_never_name_a_stale_version():
    """The monorepo docs must not cache a version that has drifted from __version__.

    Root CLAUDE.md § Ownership says the version is owned by the manifest and every
    other file carries "a pointer without cached value". Three docs cached one
    anyway, and all three still read 0.3.0 six days after 0.3.1 shipped. Prose did
    not hold the rule, so this test does.

    Sprint files under 200-po/sprints/ are excluded on purpose: they are a historical
    record. sprint-12.md narrates the 0.3.0 upload failing and the pivot to 0.3.1;
    rewriting those numbers would destroy the reason 0.3.1 exists.
    """
    import re

    repo_root = Path(pkms_lint.__file__).parents[2]
    docs = [
        repo_root / "README.md",
        repo_root / "docs" / "pipeline.md",
        repo_root / "packages" / "pkms-lint" / "README.md",
        repo_root / "public" / "README.md",
    ]
    semver = re.compile(r"\b\d+\.\d+\.\d+\b")

    stale = []
    for doc in docs:
        if not doc.exists():
            continue
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if "pkms-lint" not in line:
                continue
            for found in semver.findall(line):
                if found != pkms_lint.__version__:
                    rel = doc.relative_to(repo_root).as_posix()
                    stale.append(f"{rel}:{lineno} names {found}, package is {pkms_lint.__version__}")

    assert not stale, "stale version in the docs:\n  " + "\n  ".join(stale)
