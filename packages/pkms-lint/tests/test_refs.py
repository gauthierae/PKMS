"""Tests 18-22 — reference-style ID links and Need 3.

Spec: 200-po/sprints/sprint-12.md section E.3, decision S12-5.
"""
from __future__ import annotations

import hashlib

from conftest import ULID_B, ULID_C, ULID_MISSING


def _fingerprint(root):
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*.md"))
    }


def test_stale_path_is_detected(run, id_vault):
    result = run(id_vault)
    assert "STALE_PATH" in result.stdout
    assert ULID_B in result.stdout


def test_missing_def_is_detected(run, id_vault):
    result = run(id_vault)
    assert "MISSING_DEF" in result.stdout
    assert ULID_C in result.stdout


def test_unknown_id_is_detected_and_never_fixed(run, id_vault):
    """An id shape absent from the manifest is reported and left alone."""
    result = run(id_vault, "--fix")
    assert "UNKNOWN_ID" in result.stdout
    assert ULID_MISSING in result.stdout
    after = (id_vault / "a.md").read_text(encoding="utf-8")
    assert f"[x][{ULID_MISSING}]" in after
    assert f"[{ULID_MISSING}]:" not in after


def test_undefined_ref_is_reported(run, id_vault):
    """Need 3. [text][nope] has no definition and no manifest entry."""
    result = run(id_vault)
    assert "UNDEFINED_REF" in result.stdout
    assert "nope" in result.stdout


def test_a_legal_reference_link_stays_silent(run, id_vault):
    """[docs][python-docs] with a definition is correct Markdown, not silence."""
    result = run(id_vault)
    assert "python-docs" not in result.stdout


def test_findings_exit_1(run, id_vault):
    assert run(id_vault).exit_code == 1


def test_fix_repairs_only_the_two_fixable_codes(run, id_vault):
    before = _fingerprint(id_vault)
    run(id_vault, "--fix")
    after = _fingerprint(id_vault)
    # a.md holds every case, so only it may change.
    assert after["b.md"] == before["b.md"]
    assert after["c.md"] == before["c.md"]
    assert after["a.md"] != before["a.md"]
    text = (id_vault / "a.md").read_text(encoding="utf-8")
    assert f"[{ULID_B}]: b.md" in text          # STALE_PATH repaired
    assert f"[{ULID_C}]: c.md" in text          # MISSING_DEF injected
    assert "[nope]:" not in text                # UNDEFINED_REF never repaired


def test_dry_run_writes_nothing(run, id_vault):
    before = _fingerprint(id_vault)
    result = run(id_vault, "--fix", "--dry-run")
    assert _fingerprint(id_vault) == before
    assert "STALE_PATH" in result.stdout
