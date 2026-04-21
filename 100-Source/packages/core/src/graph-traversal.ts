import type { NoteInput, ContextNode } from './types.js'

export function bfsTraversal(
  notes: NoteInput[],
  startId: string,
  maxDepth: number
): ContextNode[] {
  const index = new Map<string, NoteInput>(notes.map((n) => [n.id, n]))

  const startNote = index.get(startId)
  if (!startNote) return []

  const visited = new Set<string>([startId])
  const result: ContextNode[] = []
  const queue: Array<{ id: string; depth: number; viaLink?: string }> = [
    { id: startId, depth: 0 },
  ]

  while (queue.length > 0) {
    const { id, depth, viaLink } = queue.shift()!
    const note = index.get(id)!

    result.push({
      note,
      depth,
      relation: depth === 0 ? 'root' : 'forward-link',
      viaLink,
    })

    if (depth >= maxDepth) continue

    for (const link of note.links) {
      const targetId = link.targetId
      if (targetId === id) continue        // skip self-links
      if (visited.has(targetId)) continue  // skip already-visited
      if (!index.has(targetId)) continue   // skip broken links

      visited.add(targetId)
      queue.push({ id: targetId, depth: depth + 1, viaLink: id })
    }
  }

  return result
}
