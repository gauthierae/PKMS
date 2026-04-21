export interface WikiLink {
  raw: string           // full text inside [[ ]]
  target: string        // path/name before # or |
  heading?: string      // fragment after # (not a block ref)
  blockId?: string      // fragment after #^
  alias?: string        // display text after |
  isEmbed: boolean      // true when ![[...]]
  resolvedPath?: string // vault-relative path; undefined = broken link
}

export interface ParsedNote {
  vaultPath: string                      // vault-relative path, e.g. "000-Administration/090-Inbox/alpha.md"
  frontmatter: Record<string, unknown>
  tags: string[]
  links: WikiLink[]
  body: string                           // frontmatter-stripped markdown content
}
