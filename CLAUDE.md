---
project: true
---

# PKMS Middleware — Local-First LLM Context Orchestrator

## What This Project Is

This is a local-first middleware that sits between a user's personal knowledge base (Markdown vault) and any LLM. It does two things: it analyzes the knowledge base structure, and it guides the user in crafting prompts and metaprompts that make their knowledge base usable as persistent LLM context — without manual copy-paste, and without data leaving the machine.

The product is built around a PKM framework with four interdependent activities:

| Activity | What it means in the middleware |
|----------|--------------------------------|
| **Harvest** | Guided selection and ingestion of knowledge sources into the vault |
| **Embed** | Structuring captured information with function, address, and retrieval intent |
| **Weave** | Building typed relationships between knowledge elements — semantic (idea→idea) and functional (research→decision) |
| **Activate** | Generating prompts, metaprompts, outputs, and feedback loops from the connected knowledge base |

These are not sequential steps. The middleware surfaces which activity is most needed at a given moment, based on the current state of the vault.

## Primary User

**Independent researchers and PhD students outside institutions** — managing their own literature review, synthesis pipeline, and writing outputs (papers, Substack, reports). They have already built the vault; they are manually pasting vault content into LLM prompts every session. This product removes that friction.

Secondary: solo strategy consultants who cannot use cloud AI tools due to client confidentiality constraints. Local-first is a requirement, not a preference.

## Key Constraints

- **Local-first**: No user data leaves the machine by default. API mode is opt-in and uses the user's own keys.
- **LLM-agnostic**: Works with any LLM via API or local model (Ollama, LM Studio).
- **Markdown-native**: No proprietary format. The vault is owned by the user.
- **License**: AGPL v3.

## Current State

**Design thinking:** Empathize ✓ — Define ✓ — Ideate ✓ — **Prototype** (active) — Test

Prototype shortlist: **I3** (schema-first vault interface) → **I4** (side context panel) → **I7** (draft-to-vault), sequential. Design thinking artifacts in `po/design-thinking/`.

Two validated personas: **Independent Researcher** (primary) and **Solo Consultant** (secondary, confidentiality-constrained).

Strategic and research foundation in `po/`: `niche-research.md`, `market-strategy.md`, `privacy-policy.md`, `architecture-notes.md`.

PKM framework documented in `pkms-essai-personnel-v3.md` (French).

---

## Root-level file exemptions

The following files at project root are monorepo tooling config and must stay there. They are not GO810 orphans:

`package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `turbo.json`, `tsconfig.base.json`, `eslint.config.js`, `node_modules/`

---

## Sprint Governance

Follows the shared dev cycle: `~/000-Administration/010-Claude/dev-cycle.md`.

**Project-specific paths:**
- Sprint files: `000-Administration/020-Sprints/sprint-N.md`
- Decision log: `200-po/decisions.md`

---

## Sprint History

All sprint bundles (spec + QA + UAT) in `000-Administration/020-Sprints/sprint-N.md`. See `200-po/decisions.md` for the full Decision Log.

| Sprint | Goal | Status |
|--------|------|--------|
| Sprint 1 | I3: `getNote` + MCP scaffold | ✅ Done — 2026-04-13 |
| Sprint 2 | I3: `search` | ✅ Done — 2026-04-13 |
| Sprint 3 | I3: search truncation + `getBacklinks` | ✅ Done — 2026-04-21 |

## Current Sprint

_(none — awaiting Sprint 4 planning)_

## Rules

- If something is not clear, always ask questions.
- When planning, never propose to delete files. Suggest an archive path inferred from context instead.
