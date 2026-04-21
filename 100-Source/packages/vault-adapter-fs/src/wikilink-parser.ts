import type { WikiLink } from './types.js'

// Strip regions that must not be parsed for wikilinks, replacing them with
// whitespace of the same length to preserve character offsets (not needed
// here, but good practice for future position tracking).
function stripNonParseable(content: string): string {
  // Fenced code blocks: ```...``` (including language tags, multiline)
  let stripped = content.replace(/```[\s\S]*?```/g, (m) => ' '.repeat(m.length))
  // Inline code spans: `...`
  stripped = stripped.replace(/`[^`\n]+`/g, (m) => ' '.repeat(m.length))
  // Obsidian comments: %% ... %%
  stripped = stripped.replace(/%%[\s\S]*?%%/g, (m) => ' '.repeat(m.length))
  // HTML comments: <!-- ... -->
  stripped = stripped.replace(/<!--[\s\S]*?-->/g, (m) => ' '.repeat(m.length))
  return stripped
}

// Parse a single wikilink inner string (the part between [[ and ]]).
// Examples handled:
//   "Note"                 → target: Note
//   "Note|alias"           → target: Note, alias: alias
//   "Note#Heading"         → target: Note, heading: Heading
//   "Note#^blockid"        → target: Note, blockId: blockid
//   "Note#Heading|alias"   → target: Note, heading: Heading, alias: alias
//   "folder/Note|alias"    → target: folder/Note, alias: alias
function parseInner(raw: string, isEmbed: boolean): WikiLink {
  // Split alias (last | wins, as Obsidian does)
  const pipeIdx = raw.indexOf('|')
  const alias = pipeIdx !== -1 ? raw.slice(pipeIdx + 1).trim() : undefined
  const beforePipe = pipeIdx !== -1 ? raw.slice(0, pipeIdx) : raw

  // Split fragment
  const hashIdx = beforePipe.indexOf('#')
  const target = (hashIdx !== -1 ? beforePipe.slice(0, hashIdx) : beforePipe).trim()
  const fragment = hashIdx !== -1 ? beforePipe.slice(hashIdx + 1).trim() : undefined

  let heading: string | undefined
  let blockId: string | undefined
  if (fragment !== undefined) {
    if (fragment.startsWith('^')) {
      blockId = fragment.slice(1)
    } else {
      heading = fragment
    }
  }

  return { raw, target, heading, blockId, alias, isEmbed }
}

export function parseWikilinks(content: string): WikiLink[] {
  const stripped = stripNonParseable(content)
  const links: WikiLink[] = []
  // Match optional leading ! (embed), then [[ ... ]]
  // Inner content must not contain [ or ] to avoid nested bracket confusion
  const re = /(!?)\[\[([^\[\]]+)\]\]/g
  let match: RegExpExecArray | null
  while ((match = re.exec(stripped)) !== null) {
    const isEmbed = match[1] === '!'
    const inner = match[2]
    const link = parseInner(inner, isEmbed)
    // Skip intra-document heading/block links ([[#Heading]] — no note target)
    if (link.target === '') continue
    links.push(link)
  }
  return links
}
