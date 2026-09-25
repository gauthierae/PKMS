from __future__ import annotations

import json
import os
import posixpath
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import typer

INLINE_REF   = re.compile(r'\[([^\]]+)\]\[([^\]]+)\]')
DEFINITION   = re.compile(
    r'^\[([^\]]+)\]:\s+(?:<([^>]+)>|(\S+))(?:\s+"([^"]*)")?',
    re.MULTILINE,
)
FRONTMATTER  = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
ID_LINE      = re.compile(r'^id:\s*["\']?(\S+?)["\']?\s*$', re.MULTILINE)
ID_PATTERN   = re.compile(r'^[A-Z]-\d{4}$')
ULID_PATTERN = re.compile(r'^[0-9A-HJKMNP-TV-Z]{26}$')

FENCE        = re.compile(r'```.*?```', re.DOTALL)
INLINE_CODE  = re.compile(r'`[^`\n]+`')
OBS_COMMENT  = re.compile(r'%%.*?%%', re.DOTALL)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
WIKILINK     = re.compile(r'(!?)\[\[([^\[\]]+)\]\]')
# A real extension, not any dot in a name. PurePosixPath("v1.2 notes").suffix
# is ".2 notes", which would skip a note as if it were an asset.
ASSET_EXT    = re.compile(r'\.[A-Za-z0-9]{1,5}$')
WIN_DRIVE    = re.compile(r'^[A-Za-z]:[\\/]')

STALE_PATH         = "STALE_PATH"
MISSING_DEF        = "MISSING_DEF"
UNKNOWN_ID         = "UNKNOWN_ID"
UNDEFINED_REF      = "UNDEFINED_REF"
BROKEN_WIKILINK    = "BROKEN_WIKILINK"
AMBIGUOUS_WIKILINK = "AMBIGUOUS_WIKILINK"


@dataclass
class Issue:
    failure: str
    key: str
    file: Path
    old: str | None
    new: str | None
    kind: str = "ref"
    line: int | None = None
    candidates: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    embed: bool = False


def strip_non_parseable(text: str) -> str:
    """Blank every region a link cannot live in.

    Each region becomes spaces of the same length, so an offset into this
    string still indexes the original text and line numbers stay true.
    """
    def blank(match: re.Match[str]) -> str:
        return " " * len(match.group(0))

    for pattern in (FRONTMATTER, FENCE, INLINE_CODE, OBS_COMMENT, HTML_COMMENT):
        text = pattern.sub(blank, text)
    return text


@dataclass
class IdStats:
    no_frontmatter: int = 0
    no_id: int = 0
    duplicates: int = 0
    duplicate_detail: list[tuple[str, str, str]] = field(default_factory=list)


def _is_pkms_id(key: str) -> bool:
    return bool(ID_PATTERN.match(key) or ULID_PATTERN.match(key))


def discover_files(vault: Path) -> list[Path]:
    files = []
    for f in vault.rglob("*.md"):
        parts = f.relative_to(vault).parts
        if any(p.startswith(".") for p in parts) or "node_modules" in parts:
            continue
        # Logseq backs up every edited note under logseq/bak/, a folder with no
        # dot. Match the pair, so a user folder named bak/ keeps its notes.
        if any(a == "logseq" and b == "bak" for a, b in zip(parts, parts[1:])):
            continue
        files.append(f)
    return sorted(files)


def build_manifest(vault: Path, md_files: list[Path]) -> tuple[dict[str, str], IdStats]:
    manifest: dict[str, str] = {}
    stats = IdStats()
    for f in md_files:
        rel = f.relative_to(vault).as_posix()
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        block = FRONTMATTER.match(text)
        if not block:
            stats.no_frontmatter += 1
            continue
        found = ID_LINE.search(block.group(1))
        if not found:
            stats.no_id += 1
            continue
        key = found.group(1)
        if key in manifest:
            stats.duplicates += 1
            stats.duplicate_detail.append((key, rel, manifest[key]))
            continue
        manifest[key] = rel
    return manifest, stats


def _encode_path(rel: str) -> str:
    return f"<{rel}>" if " " in rel else rel


def _canon_relpath(target: Path, from_file: Path) -> str:
    return _encode_path(os.path.relpath(target, from_file.parent))


def scan_file(file: Path, vault: Path, manifest: dict[str, str]) -> list[Issue]:
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    # The same mask the wikilink parse uses. A [a][b] inside a code span is
    # not a link in CommonMark, so it must not be a finding here either.
    body = strip_non_parseable(text)
    # Keep the first occurrence of each key so every finding carries a line.
    # Masking preserves offsets, so the count runs against the original text.
    inline_keys: dict[str, int] = {}
    for m in INLINE_REF.finditer(body):
        inline_keys.setdefault(m.group(2), text[: m.start()].count("\n") + 1)
    defined: dict[str, tuple[str, str | None]] = {
        m.group(1): (m.group(2) or m.group(3), m.group(4))
        for m in DEFINITION.finditer(body)
    }
    issues: list[Issue] = []
    for key in sorted(inline_keys):
        line = inline_keys[key]
        if not _is_pkms_id(key):
            # A non-PKMS key with a definition is legal Markdown, so it stays
            # silent. Without one it points at nothing and was invisible before.
            if key not in defined:
                issues.append(Issue(UNDEFINED_REF, key, file, None, None, line=line))
            continue
        if key not in manifest:
            issues.append(Issue(UNKNOWN_ID, key, file, None, None, line=line))
        elif key not in defined:
            new_path = _canon_relpath(vault / manifest[key], file)
            issues.append(Issue(MISSING_DEF, key, file, None, new_path, line=line))
        else:
            def_path, _ = defined[key]
            try:
                resolved = (file.parent / def_path).resolve()
                vault_rel = str(resolved.relative_to(vault.resolve()))
            except (ValueError, OSError):
                vault_rel = ""
            if vault_rel != manifest[key]:
                new_path = _canon_relpath(vault / manifest[key], file)
                issues.append(Issue(STALE_PATH, key, file, def_path, new_path, line=line))
    return issues


def _stem(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    return (name[:-3] if name.endswith(".md") else name).lower()


def _escapes_vault(target: str) -> bool:
    """Port of safeResolveUnderVault. An escaping target is never resolved."""
    if target.startswith("/") or WIN_DRIVE.match(target):
        return True
    normalized = posixpath.normpath(target)
    return normalized == ".." or normalized.startswith("../")


def _edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[len(b)]


def suggest_names(target: str, rel_paths: list[str], limit: int = 3) -> list[str]:
    stem = _stem(target)
    if not stem:
        return []
    threshold = max(3, len(stem) // 2)
    scored = []
    for rel in rel_paths:
        candidate = _stem(rel)
        # The distance cannot fall under the threshold when the lengths differ
        # by more than it, so skip the O(n*m) comparison entirely.
        if abs(len(candidate) - len(stem)) > threshold:
            continue
        distance = _edit_distance(stem, candidate)
        if 0 < distance <= threshold:
            scored.append((distance, rel))
    scored.sort()
    return [rel for _, rel in scored[:limit]]


def scan_wikilinks(file: Path, vault: Path, rel_paths: list[str]) -> tuple[list[Issue], int]:
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], 0
    masked = strip_non_parseable(text)
    issues: list[Issue] = []
    assets_skipped = 0
    for match in WIKILINK.finditer(masked):
        embed = match.group(1) == "!"
        inner = match.group(2)
        # An alias is display text only; a fragment is a heading or a block id.
        # Neither is validated in 0.3.x.
        target = inner.split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            continue
        if ASSET_EXT.search(target) and not target.lower().endswith(".md"):
            assets_skipped += 1
            continue
        line = text[: match.start()].count("\n") + 1
        if _escapes_vault(target):
            issues.append(Issue(BROKEN_WIKILINK, target, file, None, None,
                                kind="wikilink", line=line, embed=embed))
            continue
        normalized = target[:-3] if target.endswith(".md") else target
        exact = [r for r in rel_paths if (r[:-3] if r.endswith(".md") else r) == normalized]
        if exact:
            continue
        matches = sorted(r for r in rel_paths if _stem(r) == _stem(normalized))
        if len(matches) == 1:
            continue
        if matches:
            issues.append(Issue(AMBIGUOUS_WIKILINK, target, file, None, None,
                                kind="wikilink", line=line, candidates=matches, embed=embed))
        else:
            issues.append(Issue(BROKEN_WIKILINK, target, file, None, None,
                                kind="wikilink", line=line,
                                suggestions=suggest_names(normalized, rel_paths), embed=embed))
    return issues, assets_skipped


def _apply_fixes(issues: list[Issue], text: str) -> str:
    for issue in [i for i in issues if i.failure == STALE_PATH]:
        title = None
        for m in DEFINITION.finditer(text):
            if m.group(1) == issue.key:
                title = m.group(4)
                break
        replacement = f'[{issue.key}]: {issue.new}'
        if title:
            replacement += f' "{title}"'
        text = re.compile(
            rf'^\[{re.escape(issue.key)}\]:.*$', re.MULTILINE
        ).sub(replacement, text, count=1)

    for issue in [i for i in issues if i.failure == MISSING_DEF]:
        if not text.endswith('\n'):
            text += '\n'
        text += f'[{issue.key}]: {issue.new}\n'

    return text


def _atomic_write(file: Path, text: str) -> None:
    tmp = file.with_suffix(file.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, file)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


__version__ = "0.3.2"

app = typer.Typer(help="Find broken links in a Markdown vault.")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pkms-lint {__version__}")
        raise typer.Exit(0)


@app.command()
def main(
    vault: Path = typer.Argument(..., help="Vault root directory"),
    manifest: Optional[Path] = typer.Option(
        None, "--manifest", help="Manifest path (default: <vault>/.pkms-index.json)"
    ),
    fix: bool = typer.Option(False, "--fix", help="Repair STALE_PATH and MISSING_DEF issues"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would change; write nothing"
    ),
    json_out: bool = typer.Option(False, "--json", help="JSON output"),
    show_duplicates: bool = typer.Option(
        False, "--show-duplicates", help="Print one warning line per duplicate id"
    ),
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Print the version and exit"
    ),
) -> None:
    vault = vault.resolve()
    if not vault.is_dir():
        typer.echo(f"Error: vault '{vault}' is not a directory", err=True)
        raise typer.Exit(2)

    md_files = discover_files(vault)
    scanned, stats = build_manifest(vault, md_files)

    mdata: dict[str, str]
    if manifest is not None:
        manifest_path = manifest.resolve()
        if not manifest_path.is_file():
            typer.echo(f"Error: manifest '{manifest_path}' not found", err=True)
            raise typer.Exit(2)
        mdata = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_source = "explicit"
        index_label = f"index: {manifest_path}"
    elif (vault / ".pkms-index.json").is_file():
        mdata = json.loads((vault / ".pkms-index.json").read_text(encoding="utf-8"))
        manifest_source = "file"
        index_label = "index: .pkms-index.json"
    else:
        mdata = scanned
        manifest_source = "scan"
        index_label = "index: built by scan (no .pkms-index.json)"

    if not json_out:
        typer.echo(f"pkms-lint {__version__} — {len(md_files)} files — {index_label}")

    rel_paths = [f.relative_to(vault).as_posix() for f in md_files]
    all_issues: list[Issue] = []
    assets_skipped = 0
    for f in md_files:
        all_issues.extend(scan_file(f, vault, mdata))
        wiki, skipped_here = scan_wikilinks(f, vault, rel_paths)
        all_issues.extend(wiki)
        assets_skipped += skipped_here

    all_issues.sort(key=lambda i: (
        i.file.relative_to(vault).as_posix(), i.line or 0, i.failure, i.key
    ))
    by_file: dict[Path, list[Issue]] = {}
    for issue in all_issues:
        by_file.setdefault(issue.file, []).append(issue)

    fixed: set[tuple[Path, str]] = set()
    if fix and not dry_run:
        for file, issues in by_file.items():
            fixable = [i for i in issues if i.failure in (STALE_PATH, MISSING_DEF)]
            if not fixable:
                continue
            text = file.read_text(encoding="utf-8")
            new_text = _apply_fixes(fixable, text)
            if new_text != text:
                _atomic_write(file, new_text)
                for i in fixable:
                    fixed.add((i.file, i.key))

    counts = {
        STALE_PATH: 0, MISSING_DEF: 0, UNKNOWN_ID: 0,
        UNDEFINED_REF: 0, BROKEN_WIKILINK: 0, AMBIGUOUS_WIKILINK: 0,
    }
    for issue in all_issues:
        counts[issue.failure] += 1

    if json_out:
        findings = [
            {
                "file": issue.file.relative_to(vault).as_posix(),
                "kind": issue.kind,
                "key": issue.key,
                "failure": issue.failure,
                "line": issue.line,
                "old_path": issue.old,
                "new_path": issue.new,
                "candidates": issue.candidates,
                "suggestions": issue.suggestions,
                "embed": issue.embed,
                "fixed": (issue.file, issue.key) in fixed,
            }
            for issue in all_issues
        ]
        typer.echo(json.dumps({
            "tool": "pkms-lint",
            "version": __version__,
            "schema": 1,
            "vault": str(vault),
            "manifest_source": manifest_source,
            "files_scanned": len(md_files),
            "assets_skipped": assets_skipped,
            "notes_without_frontmatter": stats.no_frontmatter,
            "notes_without_id": stats.no_id,
            "duplicate_ids": stats.duplicates,
            "counts": counts,
            "findings": findings,
        }, indent=2))
    else:
        if by_file:
            typer.echo("")
        for file, issues in by_file.items():
            typer.echo(file.relative_to(vault).as_posix())
            for issue in issues:
                was_fixed = (issue.file, issue.key) in fixed
                tag = "  [fixed]" if was_fixed else ""
                if issue.failure == STALE_PATH:
                    typer.echo(f"  STALE_PATH   {issue.key}  old: {issue.old}  →  new: {issue.new}{tag}")
                elif issue.failure == MISSING_DEF:
                    typer.echo(f"  MISSING_DEF  {issue.key}  inject: {issue.new}{tag}")
                elif issue.failure == UNDEFINED_REF:
                    typer.echo(f"  UNDEFINED_REF  {issue.key}  no definition, no manifest entry")
                elif issue.failure == BROKEN_WIKILINK:
                    hint = (
                        f"  did you mean: {', '.join(issue.suggestions)}"
                        if issue.suggestions else ""
                    )
                    typer.echo(f"  {issue.line}  BROKEN_WIKILINK      {issue.key}{hint}")
                elif issue.failure == AMBIGUOUS_WIKILINK:
                    typer.echo(
                        f"  {issue.line}  AMBIGUOUS_WIKILINK   {issue.key}"
                        f"  matches: {', '.join(issue.candidates)}"
                    )
                else:
                    typer.echo(f"  UNKNOWN_ID   {issue.key}  not in manifest")

    if not json_out:
        fixed_count = len(fixed)
        fixable_total = counts[STALE_PATH] + counts[MISSING_DEF]
        skipped = (
            fixable_total - fixed_count + counts[UNKNOWN_ID] + counts[UNDEFINED_REF]
        )
        summary = (
            f"\nSummary: {counts[STALE_PATH]} STALE_PATH · "
            f"{counts[MISSING_DEF]} MISSING_DEF · "
            f"{counts[UNKNOWN_ID]} UNKNOWN_ID · "
            f"{counts[UNDEFINED_REF]} UNDEFINED_REF ·\n"
            f"         {counts[BROKEN_WIKILINK]} BROKEN_WIKILINK · "
            f"{counts[AMBIGUOUS_WIKILINK]} AMBIGUOUS_WIKILINK"
        )
        if fix or dry_run:
            summary += f"  ({fixed_count} fixed, {skipped} skipped)"
        typer.echo(summary)
        if assets_skipped:
            typer.echo(
                f"{assets_skipped} asset embeds not checked "
                f"(pkms-lint indexes Markdown only)."
            )
        _report_id_stats(stats, show_duplicates)

    if all_issues:
        raise typer.Exit(1)


def _report_id_stats(stats: IdStats, show_duplicates: bool) -> None:
    lines = []
    if stats.no_frontmatter:
        noun = "note carries" if stats.no_frontmatter == 1 else "notes carry"
        lines.append(f"{stats.no_frontmatter} {noun} no frontmatter block.")
    if stats.no_id:
        noun = "note carries" if stats.no_id == 1 else "notes carry"
        lines.append(f"{stats.no_id} {noun} frontmatter with no id: field.")
    if stats.duplicates:
        noun = "duplicate id" if stats.duplicates == 1 else "duplicate ids"
        lines.append(
            f"{stats.duplicates} {noun} (first file in sorted order kept)."
        )
    if not lines:
        return
    typer.echo("")
    for line in lines:
        typer.echo(line)

    if not stats.duplicates:
        return
    listing = show_duplicates
    # A prompt on a pipe or in CI would hang the run, so only a terminal is asked.
    if not listing and sys.stdin.isatty() and sys.stdout.isatty():
        answer = typer.prompt("List them? [y/N]", default="N", show_default=False)
        listing = answer.strip().lower() == "y"
    if listing:
        for key, duplicate, kept in stats.duplicate_detail:
            typer.echo(f"warning: duplicate id {key} in {duplicate} (kept {kept})")


if __name__ == "__main__":
    app()
