import { homedir } from 'node:os'
import MiniSearch from 'minisearch'
import { scanVault } from './vault-scanner.js'
import type { ParsedNote } from './types.js'
import { buildBacklinkIndex } from './backlink-index.js'
import type { VaultReader, NoteResult, SearchResult, BacklinkResult } from '@pkms/core/src/vault-reader.js'

class NotImplementedError extends Error {
  constructor(method: string, sprint: number) {
    super(`FsVaultReader.${method} not implemented — available in Sprint ${sprint}`)
    this.name = 'NotImplementedError'
  }
}

interface SearchDoc {
  id: string     // = ParsedNote.vaultPath — used as MiniSearch document id
  title: string
  body: string
  tags: string   // note.tags joined with spaces for tokenisation
}

interface VaultCache {
  notes: ParsedNote[]
  index: MiniSearch<SearchDoc>
  backlinks: Map<string, string[]>   // target vaultPath → [source vaultPaths]
}

function stemOf(vaultPath: string): string {
  return vaultPath.split('/').pop()!.replace(/\.md$/, '')
}

// CR2: single source of truth for title derivation — used by both toNoteResult and buildIndex.
function titleOf(note: ParsedNote): string {
  return typeof note.frontmatter.title === 'string' ? note.frontmatter.title : stemOf(note.vaultPath)
}

function toNoteResult(note: ParsedNote): NoteResult {
  return {
    path: note.vaultPath,
    title: titleOf(note),
    body: note.body,
    tags: note.tags,
    frontmatter: note.frontmatter,
  }
}

// SR1+SR2: use /\s\S*$/ to trim at any whitespace boundary (not just spaces); maxLen=299
// so the result with the appended '…' is always ≤ 300 chars including the degenerate case.
function excerptOf(body: string, maxLen = 299): string {
  if (body.length <= maxLen) return body
  const cut = body.slice(0, maxLen)
  const lastWS = cut.search(/\s\S*$/)
  return (lastWS > 0 ? cut.slice(0, lastWS).trimEnd() : cut) + '…'
}

function buildIndex(notes: ParsedNote[]): MiniSearch<SearchDoc> {
  // SR1: storeFields omitted — id is returned automatically; no extra fields needed.
  const ms = new MiniSearch<SearchDoc>({
    fields: ['title', 'tags', 'body'],
    searchOptions: {
      boost: { title: 3, tags: 2, body: 1 },
      fuzzy: 0.2,
    },
  })
  const docs: SearchDoc[] = notes.map((n) => ({
    id: n.vaultPath,
    title: titleOf(n),
    body: n.body,
    tags: n.tags.join(' '),
  }))
  ms.addAll(docs)
  return ms
}

// CR2: cache TTL — vault is re-scanned after this interval so in-flight edits are picked up.
// CR3: loadPromise singleton — concurrent calls share one in-flight scan instead of starting N.
const CACHE_TTL_MS = 60_000 // 60 seconds

export class FsVaultReader implements VaultReader {
  private readonly root: string
  private cache: VaultCache | null = null
  private cacheTimestamp = 0
  private loadPromise: Promise<VaultCache> | null = null

  constructor(root?: string) {
    this.root = root ?? homedir()
  }

  private load(): Promise<VaultCache> {
    const now = Date.now()

    // Cache is valid — return immediately without allocating a Promise.
    if (this.cache && now - this.cacheTimestamp < CACHE_TTL_MS) {
      return Promise.resolve(this.cache)
    }

    // A scan is already in flight — share it (CR3).
    if (this.loadPromise) return this.loadPromise

    // Start a fresh scan and build the search index atomically.
    this.loadPromise = scanVault(this.root)
      .then(({ notes }) => {
        const index = buildIndex(notes)
        const backlinks = buildBacklinkIndex(notes)
        const cache: VaultCache = { notes, index, backlinks }
        this.cache = cache
        this.cacheTimestamp = Date.now()
        this.loadPromise = null
        return cache
      })
      .catch((err: unknown) => {
        this.loadPromise = null // clear so the next call retries
        throw err
      })

    return this.loadPromise
  }

  async getNote(path: string): Promise<NoteResult | null> {
    const { notes } = await this.load()
    const note = notes.find((n) => n.vaultPath === path)
    return note ? toNoteResult(note) : null
  }

  async search(query: string, limit = 10): Promise<SearchResult[]> {
    const { notes, index } = await this.load()
    // MiniSearch v7 SearchOptions has no `limit` field — slice after retrieval.
    const hits = index.search(query).slice(0, limit)
    return hits.map((hit) => {
      // CR1: String() cast makes the string assumption on hit.id explicit and future-safe.
      const note = notes.find((n) => n.vaultPath === String(hit.id))!
      return {
        path: note.vaultPath,
        title: titleOf(note),
        score: hit.score,
        tags: note.tags,
        excerpt: excerptOf(note.body),
      }
    })
  }

  async getBacklinks(path: string): Promise<BacklinkResult[]> {
    const { notes, backlinks } = await this.load()
    const target = notes.find((n) => n.vaultPath === path)
    if (!target) throw new Error(`Note not found: ${path}`)
    const sourcePaths = backlinks.get(path) ?? []
    return sourcePaths
      .map((sp) => notes.find((n) => n.vaultPath === sp))
      .filter((n): n is ParsedNote => n !== undefined)
      .map((n) => ({ path: n.vaultPath, title: titleOf(n) }))
  }

  async queryByProperty(_key: string, _value: unknown): Promise<NoteResult[]> {
    throw new NotImplementedError('queryByProperty', 4)
  }

  async getByTag(_tag: string): Promise<NoteResult[]> {
    throw new NotImplementedError('getByTag', 5)
  }
}
