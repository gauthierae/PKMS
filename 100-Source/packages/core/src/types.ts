// Core domain types — no vault-adapter-fs dependency

export interface NoteInput {
  id: string                            // vault-relative path (stable identifier)
  title: string                         // frontmatter title or filename stem
  body: string                          // markdown content (frontmatter stripped)
  tags: string[]
  links: Array<{ targetId: string }>    // resolved forward links only (no embeds)
}

export interface ContextNode {
  note: NoteInput
  depth: number
  relation: 'root' | 'forward-link'
  viaLink?: string                      // id of the note that linked here
}

export interface ContextPackage {
  root: NoteInput
  nodes: ContextNode[]                  // BFS order; root is nodes[0]
  tokenEstimate: number                 // rough estimate: total chars / 4
}
