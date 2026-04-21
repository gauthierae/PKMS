import matter from 'gray-matter'

export interface FrontmatterResult {
  data: Record<string, unknown>
  tags: string[]
  body: string  // content with frontmatter stripped (for wikilink parsing)
}

export function parseFrontmatter(raw: string): FrontmatterResult {
  const parsed = matter(raw)
  const data = parsed.data as Record<string, unknown>

  // Normalize tags — may be a string, string[], or absent
  let tags: string[] = []
  if (Array.isArray(data.tags)) {
    tags = data.tags.map((t) => String(t))
  } else if (typeof data.tags === 'string') {
    tags = [data.tags]
  }

  return { data, tags, body: parsed.content }
}
