"""On-disk fixture vaults.

Every fixture asserts its own contract before a test runs. A malformed fixture
gives a green result that proves nothing, so it must fail here instead.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pkms_lint import app


@pytest.fixture
def run():
    runner = CliRunner()
    return lambda *args: runner.invoke(app, [str(a) for a in args])


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _assert_vault(root: Path, expected: set[str]) -> None:
    found = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert found == expected, f"fixture mismatch: {found ^ expected}"


@pytest.fixture
def plain_vault(tmp_path: Path) -> Path:
    """No frontmatter, no manifest. Obsidian-shaped."""
    root = tmp_path / "plain"
    # The notes sit under notes/, as the UAT fixture does. At the vault root
    # [[Archive]] would match Archive.md exactly and resolve, so the ambiguity
    # this fixture exists to prove would never fire.
    _write(root, "notes/index.md", "Link to [[Meeting notes]].\nAlso [[Ghost note]].\nAnd [[Archive]].\n")
    _write(root, "notes/Meeting notes.md", "A meeting.\n")
    # Distance 1 from "Ghost note", so it is the suggestion. Without a near
    # name no suggestion is possible: "Meeting notes" is at distance 8 and the
    # threshold for a 10-character stem is 5.
    _write(root, "notes/Ghost notes.md", "The near name.\n")
    _write(root, "notes/Archive.md", "One archive.\n")
    _write(root, "notes/old/Archive.md", "Another archive.\n")
    _write(root, ".obsidian/workspace.json", "{}\n")
    _write(root, ".trash/Ghost note.md", "Deleted.\n")
    _write(root, "logseq/bak/Ghost note.md", "A Logseq backup.\n")
    _write(root, "bak/Note.md", "A real note in a folder named bak.\n")
    _assert_vault(root, {
        "notes/index.md", "notes/Meeting notes.md", "notes/Ghost notes.md",
        "notes/Archive.md", "notes/old/Archive.md", ".obsidian/workspace.json",
        ".trash/Ghost note.md", "logseq/bak/Ghost note.md", "bak/Note.md",
    })
    return root


@pytest.fixture
def mixed_vault(tmp_path: Path) -> Path:
    """Masking, aliases, fragments, embeds, assets, and a path escape."""
    root = tmp_path / "mixed"
    _write(root, "Target.md", "The target.\n")
    _write(root, "masked.md", (
        "---\n"
        "id: K-0002\n"
        "front: [[Frontmatter]]\n"
        "---\n"
        "\n"
        "```\n[[Fenced]]\n```\n"
        "Inline `[[InlineCode]]` here.\n"
        "%% [[ObsidianComment]] %%\n"
        "<!-- [[HtmlComment]] -->\n"
    ))
    _write(root, "links.md", (
        "---\n"
        "id: K-0003\n"
        "type: note\n"
        "tags: []\n"
        "---\n"
        "\n"
        "[[Nowhere]]\n"                 # line 7, after a 5-line frontmatter
        "[[Target|display text]]\n"
        "[[Target#Some heading]]\n"
        "[[Target#^abc123]]\n"
        "![[Target]]\n"
        "![[diagram.png]]\n"
        "[[../../etc/passwd]]\n"
    ))
    _assert_vault(root, {"Target.md", "masked.md", "links.md"})
    return root


ULID_A = "01HZY0PMKQ7X4N8V2R6TBWJ3CD"
ULID_B = "01HZY0PMKQ7X4N8V2R6TBWJ3CE"
ULID_C = "01HZY0PMKQ7X4N8V2R6TBWJ3CF"
ULID_MISSING = "01HZY0PMKQ7X4N8V2R6TBWJ3CG"  # a valid id shape, absent from the manifest


@pytest.fixture
def id_vault(tmp_path: Path) -> Path:
    """ULID frontmatter, a manifest, and one instance of each reference failure."""
    root = tmp_path / "ids"
    _write(root, "a.md", (
        f"---\nid: {ULID_A}\ntype: note\n---\n\n"
        f"Stale: [b][{ULID_B}].\n"          # definition points at wrong.md
        f"Missing: [c][{ULID_C}].\n"        # in the manifest, no definition here
        f"Unknown: [x][{ULID_MISSING}].\n"  # id shape, absent from the manifest
        f"Undefined: [text][nope].\n"       # no definition, no manifest entry
        f"Legal: [docs][python-docs].\n\n"  # correct Markdown, must stay silent
        f"[{ULID_B}]: wrong.md\n"
        f"[python-docs]: https://docs.python.org\n"
    ))
    _write(root, "b.md", f"---\nid: {ULID_B}\ntype: note\n---\n\nNothing here.\n")
    _write(root, "c.md", f"---\nid: {ULID_C}\ntype: note\n---\n\nNothing here either.\n")
    _write(root, ".pkms-index.json", json.dumps(
        {ULID_A: "a.md", ULID_B: "b.md", ULID_C: "c.md"}
    ))
    _assert_vault(root, {"a.md", "b.md", "c.md", ".pkms-index.json"})
    return root


@pytest.fixture
def bare_vault(tmp_path: Path) -> Path:
    """Every link correct, so the run has zero findings. Only id counts differ."""
    root = tmp_path / "bare"
    _write(root, "one.md", "No frontmatter at all.\n")
    _write(root, "two.md", "---\ntype: note\n---\n\nFrontmatter with no id.\n")
    _write(root, "three.md", "---\nid: K-0001\ntype: note\n---\n\nFirst K-0001.\n")
    _write(root, "four.md", "---\nid: K-0001\ntype: note\n---\n\nSecond K-0001.\n")
    _assert_vault(root, {"one.md", "two.md", "three.md", "four.md"})
    return root
