import { readFile } from 'node:fs/promises'
import { join, relative } from 'node:path'
import { glob } from 'glob'
import { parseFrontmatter } from './frontmatter-parser.js'
import { parseWikilinks } from './wikilink-parser.js'
import { resolve } from './resolve.js'
import type { ParsedNote } from './types.js'

const EXCLUDED_DIRS = [
  '.obsidian',
  '.claude',
  '.vscode',
  '.git',
  'node_modules',
  '.bun',
  '.config',
  '.cache',
  '.local',
  '.npm',
  '.linkedin_agent',
  '.dotnet',
  '.fly',
  '.copilot',
  '.pki',
]

export async function scanVault(
  root: string
): Promise<{ notes: ParsedNote[]; warnings: string[] }> {
  const warnings: string[] = []

  const ignore = EXCLUDED_DIRS.map((d) => `**/${d}/**`)

  const filePaths = await glob('**/*.md', {
    cwd: root,
    ignore,
    absolute: false,
  })

  // Parse all notes — forward links only (unresolved)
  const notes: ParsedNote[] = await Promise.all(
    filePaths.map(async (relPath) => {
      const absPath = join(root, relPath)
      const raw = await readFile(absPath, 'utf-8')
      const { data, tags, body } = parseFrontmatter(raw)
      const links = parseWikilinks(body)
      return { vaultPath: relPath, frontmatter: data, tags, links, body }
    })
  )

  // Resolve all links now that we have the full note list
  for (const note of notes) {
    for (const link of note.links) {
      link.resolvedPath = resolve(link.target, notes, warnings)
    }
  }

  return { notes, warnings }
}
