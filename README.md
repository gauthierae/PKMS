# PKMS Modules

Small command-line tools for Markdown vaults. Each tool installs on its own and runs on your machine.

---

## Status

**Nothing is released here yet.** This repo holds no working module today. The first one arrives soon.

This repo held **PKMS v1**, a TypeScript MCP server. That project stopped on 2026-05-30. I took the
code off this branch. It stays in the git history if you want to look.

The previous README promised an MCP server with three tools: `get_note`, `search_notes`, and
`get_backlinks`. **That promise is void.** I removed the claim rather than leave it to mislead you.

---

## What comes here

Modules with the `pkms-` prefix. Each module:

- does one job
- works on a plain Markdown vault
- installs on its own — no other module required
- runs on your machine and sends nothing anywhere

### First module — `pkms-lint`

A link checker for a Markdown vault. It finds:

- broken wikilinks — `[[Target]]` with no matching file
- ambiguous wikilinks — two or more files match the same name
- a near name for a broken target, so you can see the likely typo
- broken reference-style links — stale paths and absent definitions

It reports by default. It repairs only what you ask it to repair.

---

## What this is not

**PKMS itself is not public.** PKMS is a local-first tool between a Markdown vault and an LLM. It stays
private for now. This repo holds the modules only.

If you want the modules, you do not need PKMS. That is the point of this repo.

---

## License

Modules: **MIT**. See [LICENSE](LICENSE).

---

## Author

Alain Gauthier — https://github.com/gauthierae

I build local tools for people who want to use an LLM with their notes and keep their data private.
