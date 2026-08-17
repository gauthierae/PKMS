"""Tests 6-9 and 11-17 — wikilinks, report only.

Spec: 200-po/sprints/sprint-12.md section E.4, decision S12-6.
Ported from archive/vault-lint-v0.1.ts.
"""
from __future__ import annotations

import json


def _findings(result):
    """--json emits the versioned envelope, not a bare array (S12-2)."""
    return json.loads(result.stdout)["findings"]


def test_broken_wikilink_is_reported(run, plain_vault):
    result = run(plain_vault, "--json")
    broken = [f for f in _findings(result) if f["failure"] == "BROKEN_WIKILINK"]
    assert [f["key"] for f in broken] == ["Ghost note"]
    assert broken[0]["line"] == 2
    assert broken[0]["kind"] == "wikilink"


def test_a_suggestion_names_an_existing_file(run, plain_vault):
    result = run(plain_vault, "--json")
    broken = [f for f in _findings(result) if f["failure"] == "BROKEN_WIKILINK"][0]
    assert broken["suggestions"]
    for name in broken["suggestions"]:
        assert (plain_vault / name).is_file()


def test_ambiguous_wikilink_lists_sorted_candidates(run, plain_vault):
    result = run(plain_vault, "--json")
    ambiguous = [f for f in _findings(result) if f["failure"] == "AMBIGUOUS_WIKILINK"]
    assert len(ambiguous) == 1
    assert ambiguous[0]["key"] == "Archive"
    assert ambiguous[0]["candidates"] == ["notes/Archive.md", "notes/old/Archive.md"]


def test_a_resolved_wikilink_produces_no_finding(run, plain_vault):
    result = run(plain_vault, "--json")
    assert not [f for f in _findings(result) if f["key"] == "Meeting notes"]


def test_masked_regions_are_never_reported(run, mixed_vault):
    """Fenced, inline code, %% %%, HTML comment, frontmatter. Five cases."""
    output = run(mixed_vault, "--json").stdout
    for masked in ("Fenced", "InlineCode", "ObsidianComment", "HtmlComment", "Frontmatter"):
        assert masked not in output


def test_line_number_counts_the_frontmatter(run, mixed_vault):
    """[[Nowhere]] sits on line 7, below a 5-line frontmatter block."""
    result = run(mixed_vault, "--json")
    nowhere = [f for f in _findings(result) if f["key"] == "Nowhere"]
    assert len(nowhere) == 1
    assert nowhere[0]["line"] == 7


def test_an_alias_resolves_on_the_target(run, mixed_vault):
    output = run(mixed_vault, "--json").stdout
    assert "display text" not in output


def test_a_heading_or_block_id_resolves_on_the_target(run, mixed_vault):
    output = run(mixed_vault, "--json").stdout
    assert "Some heading" not in output
    assert "abc123" not in output


def test_an_embed_carries_the_embed_flag(run, mixed_vault):
    """![[Target]] resolves, so use a broken embed to observe the flag."""
    (mixed_vault / "embed.md").write_text("![[Missing target]]\n", encoding="utf-8")
    result = run(mixed_vault, "--json")
    embedded = [f for f in _findings(result) if f["key"] == "Missing target"]
    assert len(embedded) == 1
    assert embedded[0]["embed"] is True


def test_an_asset_embed_is_counted_not_checked(run, mixed_vault):
    """![[diagram.png]] must not be reported broken, and the skip is visible."""
    assert not [f for f in _findings(run(mixed_vault, "--json")) if "diagram" in f["key"]]
    assert "1 asset embeds not checked" in run(mixed_vault).stdout


def test_a_path_escape_is_broken_and_never_resolved(run, mixed_vault):
    result = run(mixed_vault, "--json")
    escape = [f for f in _findings(result) if "passwd" in f["key"]]
    assert len(escape) == 1
    assert escape[0]["failure"] == "BROKEN_WIKILINK"


def test_fix_never_touches_a_wikilink(run, plain_vault):
    """plain_vault has only wikilink findings, so --fix must change nothing."""
    import hashlib

    def fingerprint():
        return {
            p.relative_to(plain_vault).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(plain_vault.rglob("*.md"))
        }

    before = fingerprint()
    run(plain_vault, "--fix")
    assert fingerprint() == before
