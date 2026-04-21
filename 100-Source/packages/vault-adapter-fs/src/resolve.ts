import type { ParsedNote } from './types.js'

// Mirrors Obsidian's shortest-unique-path resolution:
// 1. Exact vault-relative path match (with or without .md extension)
// 2. Filename stem match — if unique, resolve; if multiple, warn + return undefined
// 3. No match → undefined (broken link)
export function resolve(
  target: string,
  allNotes: ParsedNote[],
  warnings: string[]
): string | undefined {
  // Normalise: strip trailing .md if present
  const normalizedTarget = target.endsWith('.md') ? target.slice(0, -3) : target

  // 1. Exact vault-relative path match
  for (const note of allNotes) {
    const notePath = note.vaultPath.endsWith('.md')
      ? note.vaultPath.slice(0, -3)
      : note.vaultPath
    if (notePath === normalizedTarget) return note.vaultPath
  }

  // 2. Filename stem match (last path segment, case-insensitive to match Obsidian on case-insensitive FS)
  const targetStem = normalizedTarget.split('/').pop()!.toLowerCase()
  const matches = allNotes.filter((note) => {
    const stem = note.vaultPath
      .split('/')
      .pop()!
      .replace(/\.md$/, '')
      .toLowerCase()
    return stem === targetStem
  })

  if (matches.length === 1) return matches[0].vaultPath

  if (matches.length > 1) {
    warnings.push(
      `Ambiguous link "[[${target}]]" — matches: ${matches.map((n) => n.vaultPath).join(', ')}`
    )
    return undefined
  }

  // 3. No match
  return undefined
}
