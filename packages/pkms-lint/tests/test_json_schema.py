"""Tests 27-31, plus 23d and 23h deferred from Cycle 2.

Spec: 200-po/sprints/sprint-12.md sections D and F, decision S12-2.
"""
from __future__ import annotations

import json

import pkms_lint

FINDING_KEYS = {
    "failure", "kind", "file", "line", "key",
    "old_path", "new_path", "candidates", "suggestions", "embed", "fixed",
}


def _envelope(result):
    return json.loads(result.stdout)


def test_envelope_carries_every_top_level_key(run, plain_vault):
    doc = _envelope(run(plain_vault, "--json"))
    assert doc["tool"] == "pkms-lint"
    assert doc["version"] == pkms_lint.__version__
    assert doc["schema"] == 1
    assert doc["vault"] == str(plain_vault)
    assert doc["manifest_source"] == "scan"
    assert doc["files_scanned"] == 6
    assert "counts" in doc and "findings" in doc


def test_manifest_source_names_the_three_cases(run, plain_vault, id_vault, tmp_path):
    assert _envelope(run(plain_vault, "--json"))["manifest_source"] == "scan"
    assert _envelope(run(id_vault, "--json"))["manifest_source"] == "file"
    explicit = tmp_path / "manifest.json"
    explicit.write_text("{}", encoding="utf-8")
    doc = _envelope(run(id_vault, "--manifest", explicit, "--json"))
    assert doc["manifest_source"] == "explicit"


def test_both_link_kinds_share_one_findings_array(run, mixed_vault):
    """Criterion 6. counts must sum to len(findings)."""
    doc = _envelope(run(mixed_vault, "--json"))
    kinds = {f["kind"] for f in doc["findings"]}
    assert kinds == {"wikilink"} or kinds == {"ref", "wikilink"}
    assert sum(doc["counts"].values()) == len(doc["findings"])


def test_counts_sum_holds_on_a_vault_with_both_kinds(run, id_vault):
    doc = _envelope(run(id_vault, "--json"))
    assert sum(doc["counts"].values()) == len(doc["findings"])
    assert {f["kind"] for f in doc["findings"]} == {"ref"}


def test_every_finding_has_all_eleven_keys(run, plain_vault, id_vault):
    for vault in (plain_vault, id_vault):
        for finding in _envelope(run(vault, "--json"))["findings"]:
            assert set(finding) == FINDING_KEYS


def test_paths_are_vault_relative_posix(run, plain_vault):
    doc = _envelope(run(plain_vault, "--json"))
    for finding in doc["findings"]:
        assert not finding["file"].startswith("/")
        assert "\\" not in finding["file"]
        for path in finding["candidates"] + finding["suggestions"]:
            assert not path.startswith("/")
            assert "\\" not in path


def test_the_human_report_uses_relative_paths(run, plain_vault):
    """Section F. The heading is a vault-relative path, never an absolute one."""
    stdout = run(plain_vault).stdout
    assert "notes/index.md" in stdout
    assert str(plain_vault) not in stdout


def test_exit_1_on_findings_and_0_when_none(run, plain_vault, bare_vault):
    assert run(plain_vault).exit_code == 1
    assert run(bare_vault).exit_code == 0


# --- 23d and 23h, deferred from Cycle 2 until the envelope existed -----------

def test_a_count_is_not_a_finding(run, bare_vault):
    """Test 23d. Three id counts, and still an empty findings array."""
    doc = _envelope(run(bare_vault, "--json"))
    assert doc["findings"] == []
    assert sum(doc["counts"].values()) == 0


def test_the_envelope_carries_the_three_id_counts(run, bare_vault):
    """Test 23h. They sit at envelope level, never inside counts."""
    doc = _envelope(run(bare_vault, "--json"))
    assert doc["notes_without_frontmatter"] == 1
    assert doc["notes_without_id"] == 1
    assert doc["duplicate_ids"] == 1
    assert "notes_without_id" not in doc["counts"]


def test_assets_skipped_is_carried_and_counted(run, mixed_vault):
    assert _envelope(run(mixed_vault, "--json"))["assets_skipped"] == 1


def test_fixed_flag_is_true_for_repaired_findings(run, id_vault):
    """Test 24. --fix marks what it repaired, and only that."""
    doc = _envelope(run(id_vault, "--fix", "--json"))
    fixed = {f["failure"] for f in doc["findings"] if f["fixed"]}
    unfixed = {f["failure"] for f in doc["findings"] if not f["fixed"]}
    assert fixed == {"STALE_PATH", "MISSING_DEF"}
    assert unfixed == {"UNKNOWN_ID", "UNDEFINED_REF"}
