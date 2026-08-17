# pkms-lint

Find broken links in a Markdown vault. Wikilinks and reference-style ID links.

Point it at any folder of Markdown files. It reads `[[Wikilinks]]` the way Obsidian, Logseq, Foam and
Dendron write them, and it also reads the reference-style `[text][KEY]` form. It needs no index file,
no plugin, and no configuration. It never writes to your notes unless you pass `--fix`.

## Install

```sh
pipx install pkms-lint
```

Or, inside a virtual environment:

```sh
pip install pkms-lint
```

Requires Python 3.11 or later. The only dependency is [Typer](https://typer.tiangolo.com/).

## Use

```sh
pkms-lint ~/my-vault                 # human-readable report
pkms-lint ~/my-vault --json          # machine-readable report
pkms-lint ~/my-vault --fix           # repair the two fixable kinds
pkms-lint ~/my-vault --fix --dry-run # show the repairs, write nothing
```

Example output:

```
pkms-lint 0.3.1 — 5 files — index: built by scan (no .pkms-index.json)

notes/index.md
  2  BROKEN_WIKILINK      Ghost note  did you mean: notes/Ghost notes.md
  3  AMBIGUOUS_WIKILINK   Archive  matches: notes/Archive.md, notes/old/Archive.md

Summary: 0 STALE_PATH · 0 MISSING_DEF · 0 UNKNOWN_ID · 0 UNDEFINED_REF ·
         1 BROKEN_WIKILINK · 1 AMBIGUOUS_WIKILINK

5 notes carry no frontmatter block.
```

### What it reports

| Code | Meaning | Example | Fixable |
|---|---|---|---|
| `BROKEN_WIKILINK` | The target matches no file | `[[Ghost note]]` and no such note exists | no |
| `AMBIGUOUS_WIKILINK` | Two or more files match the target | `[[Archive]]` with `notes/Archive.md` and `notes/old/Archive.md` | no |
| `UNDEFINED_REF` | An inline reference with no definition anywhere | `[text][nope]` and no `[nope]: …` line | no |
| `STALE_PATH` | The definition points somewhere other than the indexed path | `[K-0001]: old/note.md` while the index says `new/note.md` | **yes** |
| `MISSING_DEF` | An inline reference whose key is indexed but undefined in the file | `[text][K-0001]` with no `[K-0001]: …` line | **yes** |
| `UNKNOWN_ID` | The key looks like an id but is absent from the index | `[text][K-9999]` with no such entry | no |

A reference key that **has** a definition is correct Markdown and is never reported. `[docs][python-docs]`
with a matching `[python-docs]: https://…` line stays silent.

### The index

`pkms-lint` needs a map from id to path only for the three reference-style codes. It finds one in three
ways, and the first line of every report says which:

| Line | Meaning |
|---|---|
| `index: built by scan` | No index file. Ids were read from the `id:` field in each note's frontmatter. |
| `index: .pkms-index.json` | An index file was found in the vault root. |
| `index: <path>` | You passed `--manifest <path>`. |

A vault with no ids at all works. The report ends with up to three count lines that describe it:

```
12 notes carry no frontmatter block.
3 notes carry frontmatter with no id: field.
2 duplicate ids (first file in sorted order kept).
```

These are **counts, not problems**. They never change the exit code. Most Markdown vaults have no ids
and that is fine — the wikilink checks do not need them. Add `--show-duplicates` to name each duplicate.

## What it does not do

- **It never repairs a wikilink.** `--fix` touches `STALE_PATH` and `MISSING_DEF` only.
- **It does not validate a heading or a block id.** `[[Note#Heading]]` and `[[Note#^abc]]` are checked
  on `Note` alone.
- **It does not check non-Markdown embeds.** `![[diagram.png]]` is counted and skipped, never reported
  broken.
- **It does not score your vault.** No orphan detection, no staleness, no connectivity score.
- **It reads YAML frontmatter only.** Logseq writes properties as `id:: <uuid>` in the first block
  rather than in a `---` block, so a Logseq note counts under "no frontmatter block". That affects the
  count lines only; it never produces a finding.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | The run completed and found nothing to report |
| 1 | The run completed and reported at least one finding |
| 2 | Usage error: the vault is not a directory, or an explicit `--manifest` path does not exist |

Exit 1 on findings makes the tool usable in a pre-commit hook or a CI job.

## JSON output

`--json` emits one object:

```json
{
  "tool": "pkms-lint",
  "version": "0.3.1",
  "schema": 1,
  "vault": "/home/you/my-vault",
  "manifest_source": "scan",
  "files_scanned": 5,
  "assets_skipped": 0,
  "notes_without_frontmatter": 5,
  "notes_without_id": 0,
  "duplicate_ids": 0,
  "counts": { "BROKEN_WIKILINK": 1, "AMBIGUOUS_WIKILINK": 1 },
  "findings": [
    {
      "failure": "BROKEN_WIKILINK",
      "kind": "wikilink",
      "file": "notes/index.md",
      "line": 2,
      "key": "Ghost note",
      "old_path": null,
      "new_path": null,
      "candidates": [],
      "suggestions": ["notes/Ghost notes.md"],
      "embed": false,
      "fixed": false
    }
  ]
}
```

`schema` is an integer. It rises whenever a change to `findings` would break a reader that worked
before, so you can pin against it. Every finding carries all eleven keys; the ones a given failure does
not use are `null` or `[]`. Every path is relative to the vault and uses `/` on every platform.

## Skipped folders

Any folder whose name starts with a dot, plus `node_modules` and `logseq/bak`. This is deliberate: a
note you deleted still exists inside `.trash/`, and Logseq keeps a backup of every edit under
`logseq/bak/`. Scanning either would let a deleted note resolve a link and report it as healthy.

## License

MIT. See [LICENSE](https://github.com/gauthierae/PKMS/blob/main/LICENSE).

## About

`pkms-lint` is the first released module of PKMS, a set of local-first tools for maintaining a Markdown
vault readable by a human and by a language model alike. The other modules are not released yet.

Source and issues: https://github.com/gauthierae/PKMS
