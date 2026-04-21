import type { ContextNode, ContextPackage } from './types.js'

export function assembleContext(nodes: ContextNode[]): ContextPackage {
  const root = nodes[0]
  if (!root || root.relation !== 'root') {
    throw new Error('assembleContext: first node must be the root')
  }

  const tokenEstimate = Math.round(
    nodes.reduce((sum, n) => sum + n.note.body.length, 0) / 4
  )

  return {
    root: root.note,
    nodes,
    tokenEstimate,
  }
}
