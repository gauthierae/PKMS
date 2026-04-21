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

## Sprint Governance

Three Claude Code agents collaborate:
- **Architect** (`/architect`) — system design, technical specs, Decision Log entries
- **Developer** (`/developer`) — implements per spec, minimum scope, no gold-plating
- **Quality Analyst** (`/quality-analyst`) — spec review (Phase 2) and code review (Phase 4)

The **Product Owner** (human) drives priorities, validates outcomes, and signs off sprints.

**Sprint cycle — 5 phases + UAT:**

| Phase | Role | Output | Location in sprint file |
|-------|------|--------|------------------------|
| 1 | Architect | Sprint spec | `## Sprint Spec` |
| 2 | QA | Spec review | `## Spec Review` |
| 3 | Developer | Implementation | `## Implementation Notes` |
| 4 | QA | Code review | `## Code Review` |
| 5 | Developer | Fixes | `## Fixes Applied` |
| UAT | PO | End-to-end validation | `## UAT Results` |
| Sign-off | PO | Approval | `## PO Validation` |

**Acceptance thresholds:**
- `[BLOCKER]` — stop; PO resolves before continuing
- `[MAJOR]` — resolved in Phase 5, or explicitly deferred by PO
- `[MINOR]` — developer discretion in Phase 5 or a future sprint

**Git commit convention:** `Sprint N — <short description>` — one commit per sprint, after UAT sign-off.

**Files each agent reads on entry:** `CLAUDE.md`, `000-Administration/decisions.md`, previous sprint file (`000-Administration/020-Sprints/sprint-N-1.md` if it exists), and all source files relevant to deliverables.

---

## Sprint History

All sprint bundles (spec + QA + UAT) in `000-Administration/020-Sprints/sprint-N.md`. See `000-Administration/decisions.md` for the full Decision Log.

| Sprint | Goal | Status |
|--------|------|--------|
| Sprint 1 | I3: `getNote` + MCP scaffold | ✅ Done — 2026-04-13 |

## Current Sprint

**Sprint 2 — I3: `search`**
