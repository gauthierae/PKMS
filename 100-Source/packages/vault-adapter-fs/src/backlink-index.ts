import type { ParsedNote } from './types.js'

// Returns a map from vault-relative path → list of vault paths that link to it.
// Only resolved links are indexed; broken/embed links are excluded.
export function buildBacklinkIndex(notes: ParsedNote[]): Map<string, string[]> {
  const index = new Map<string, string[]>()

  for (const note of notes) {
    for (const link of note.links) {
      if (link.isEmbed) continue
      if (!link.resolvedPath) continue
      const existing = index.get(link.resolvedPath) ?? []
      existing.push(note.vaultPath)
      index.set(link.resolvedPath, existing)
    }
  }

  return index
}
