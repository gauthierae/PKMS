import type { NoteInput, ContextPackage } from './types.js'

export function singleNotePrompt(note: NoteInput): string {
  return [
    '# Knowledge Base Context',
    '',
    `## ${note.title}`,
    `Source: ${note.id}`,
    '',
    note.body.trim(),
  ].join('\n')
}

export function graphAwarePrompt(pkg: ContextPackage): string {
  const maxDepth = Math.max(...pkg.nodes.map((n) => n.depth))
  const lines: string[] = [
    '# Knowledge Base Context',
    `(Graph-aware — ${pkg.nodes.length} note${pkg.nodes.length !== 1 ? 's' : ''}, depth ${maxDepth})`,
  ]

  for (const node of pkg.nodes) {
    lines.push('', '---')

    const depthLabel =
      node.depth === 0
        ? ' ← starting note'
        : ` (depth ${node.depth}, linked from ${node.viaLink})`

    lines.push(`## ${node.note.title}${depthLabel}`)
    lines.push(`Source: ${node.note.id}`)
    lines.push('')
    lines.push(node.note.body.trim())
  }

  return lines.join('\n')
}
