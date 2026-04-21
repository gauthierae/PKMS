// VaultReader — typed capability set for vault access.
// Protocol adapters (MCP, OpenAI function calling, REST) consume this interface.
// Implementations live in vault-adapter-* packages.

export interface NoteResult {
  path: string                          // vault-relative path, e.g. "PKMS/CLAUDE.md"
  title: string                         // frontmatter title, or filename stem as fallback
  body: string                          // markdown content with frontmatter stripped
  tags: string[]
  frontmatter: Record<string, unknown>
}

export interface SearchResult {
  note: NoteResult
  score: number                         // relevance score — higher is more relevant
}

export interface VaultReader {
  /** Retrieve a note by its vault-relative path. Returns null if not found. */
  getNote(path: string): Promise<NoteResult | null>

  /** Full-text search across all notes. Returns top matches ranked by score. */
  search(query: string, limit?: number): Promise<SearchResult[]>

  /** Get all notes that link to the given vault-relative path. */
  getBacklinks(path: string): Promise<NoteResult[]>

  /** Filter notes by a YAML frontmatter property key and value. */
  queryByProperty(key: string, value: unknown): Promise<NoteResult[]>

  /** Get all notes that carry the given tag. */
  getByTag(tag: string): Promise<NoteResult[]>
}
