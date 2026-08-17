"""Tests 2-5, 10, 10a, 10b, 23, 23a-23c, 23e-23g, 23i-23j.

Spec: 200-po/sprints/sprint-12.md sections C, E.1, E.2, and Need 8.
Every assertion reads the command output, never an internal function.
"""
from __future__ import annotations


# --- Manifest resolution and exit codes (tests 2-5) -------------------------

def test_no_manifest_builds_index_by_scan(run, plain_vault):
    result = run(plain_vault)
    assert "index: built by scan (no .pkms-index.json)" in result.stdout
    assert "not found" not in result.stdout


def test_existing_manifest_file_is_named(run, id_vault):
    result = run(id_vault)
    assert "index: .pkms-index.json" in result.stdout


def test_missing_explicit_manifest_exits_2(run, id_vault, tmp_path):
    missing = tmp_path / "nope.json"
    result = run(id_vault, "--manifest", missing)
    assert result.exit_code == 2
    assert str(missing) in result.output


def test_vault_that_is_a_file_exits_2(run, id_vault):
    result = run(id_vault / "a.md")
    assert result.exit_code == 2


def test_clean_vault_exits_0_with_zero_summary(run, bare_vault):
    """bare_vault is the clean one. id_vault carries a case of every failure."""
    result = run(bare_vault)
    assert result.exit_code == 0
    assert "0 STALE_PATH · 0 MISSING_DEF · 0 UNKNOWN_ID · 0 UNDEFINED_REF" in result.stdout


# --- File discovery (tests 10, 10a, 10b) ------------------------------------

def _files_in(result):
    import json
    return {f["file"] for f in json.loads(result.stdout)["findings"]}


def _broken(result):
    import json
    return {
        f["key"] for f in json.loads(result.stdout)["findings"]
        if f["failure"] == "BROKEN_WIKILINK"
    }


def test_dot_directories_are_not_scanned(run, plain_vault):
    """.trash/Ghost note.md must not rescue the broken link."""
    result = run(plain_vault, "--json")
    assert not [p for p in _files_in(result) if p.startswith(".")]
    assert "Ghost note" in _broken(result)


def test_logseq_bak_is_not_scanned(run, plain_vault):
    """Same proof: the backup copy must not resolve [[Ghost note]]."""
    result = run(plain_vault, "--json")
    assert not [p for p in _files_in(result) if p.startswith("logseq/")]
    assert "Ghost note" in _broken(result)


def test_a_root_bak_folder_is_still_scanned(run, plain_vault):
    """Only the logseq/bak pair is excluded. A user folder named bak/ is a vault."""
    result = run(plain_vault)
    # 5 notes + bak/Note.md; the dot dirs and logseq/bak are out.
    assert "6 files" in result.stdout


# --- Need 8, the three counts (tests 23, 23a-23c, 23e-23g) ------------------

def test_no_frontmatter_count(run, bare_vault):
    result = run(bare_vault)
    assert "1 note carries no frontmatter block." in result.stdout


def test_frontmatter_without_id_count(run, bare_vault):
    result = run(bare_vault)
    assert "1 note carries frontmatter with no id: field." in result.stdout


def test_duplicate_id_count(run, bare_vault):
    """Two files on one id give a count of 1, not 2."""
    result = run(bare_vault)
    assert "1 duplicate id (first file in sorted order kept)." in result.stdout


def test_counts_do_not_change_the_exit_code(run, bare_vault):
    """Criterion 9. Every link is correct, so three counts still exit 0."""
    result = run(bare_vault)
    assert result.exit_code == 0


def test_a_zero_count_prints_no_line(run, id_vault):
    result = run(id_vault)
    assert "no frontmatter block" not in result.stdout
    assert "no id: field" not in result.stdout
    assert "duplicate id" not in result.stdout


def test_a_foreign_id_format_stays_silent(run, bare_vault):
    """A Dendron nanoid counts as an id. The linter judges presence, not format."""
    (bare_vault / "five.md").write_text(
        "---\nid: 8f3k2n1p0qra\ntype: note\n---\n\nDendron-shaped.\n", encoding="utf-8"
    )
    result = run(bare_vault)
    assert result.exit_code == 0
    assert "1 note carries frontmatter with no id: field." in result.stdout
    assert "8f3k2n1p0qra" not in result.stdout


# --- The duplicate detail is opt-in (tests 23i, 23j) ------------------------

def test_duplicate_detail_is_absent_by_default(run, bare_vault):
    result = run(bare_vault)
    assert "warning: duplicate id" not in result.stdout


def test_show_duplicates_prints_the_detail(run, bare_vault):
    """Sorted order is alphabetical, so four.md precedes three.md and is kept.

    The fixture names are deliberately out of alphabetical order. A rule of
    "first file encountered by the walk" would keep three.md and pass a
    reading-order assertion, so this ordering is what proves the sort.
    """
    result = run(bare_vault, "--show-duplicates")
    assert "warning: duplicate id K-0001 in three.md (kept four.md)" in result.stdout


def test_no_prompt_without_a_terminal(run, bare_vault):
    """CliRunner is not a tty. The run must return rather than wait on stdin."""
    result = run(bare_vault)
    assert result.exit_code == 0
    assert "List them?" not in result.stdout


def test_json_prints_no_count_lines(run, bare_vault):
    import json

    result = run(bare_vault, "--json")
    assert "List them?" not in result.stdout
    assert "no frontmatter block" not in result.stdout
    json.loads(result.stdout)
