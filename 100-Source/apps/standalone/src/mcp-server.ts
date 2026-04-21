import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { z } from 'zod'
import { homedir } from 'node:os'
import { FsVaultReader } from '@pkms/vault-adapter-fs/src/fs-vault-reader.js'

const vaultRoot = process.env.PKMS_VAULT_ROOT ?? homedir()
const reader = new FsVaultReader(vaultRoot)

const server = new McpServer({
  name: 'pkms',
  version: '0.1.0',
})

server.tool(
  'get_note',
  'Retrieve a vault note by its vault-relative path. Returns the note title, body, tags, and frontmatter. Returns null if the note does not exist.',
  { path: z.string().describe('Vault-relative path to the note, e.g. "PKMS/CLAUDE.md"') },
  async ({ path }) => {
    try {
      const note = await reader.getNote(path)
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(note, null, 2) }],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [{ type: 'text' as const, text: `Error: ${message}` }],
        isError: true,
      }
    }
  }
)

server.tool(
  'search_notes',
  'Search vault notes by keyword or phrase. Returns up to `limit` results ranked by relevance score (higher = more relevant). Each result contains path, title, score, tags, and a short excerpt. Use get_note to retrieve the full body of any result.',
  {
    query: z.string().min(1).describe('Keywords or phrase to search for across all vault notes'),
    limit: z.number().int().positive().optional().describe('Maximum results to return (default 10)'),
  },
  async ({ query, limit }) => {
    try {
      const results = await reader.search(query, limit)
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [{ type: 'text' as const, text: `Error: ${message}` }],
        isError: true,
      }
    }
  }
)

server.tool(
  'get_backlinks',
  'Find all vault notes that contain a [[wikilink]] pointing to the given note. Returns a list of { path, title } objects. Use get_note to retrieve the full content of any result. Returns an error if the target path does not exist in the vault.',
  {
    path: z.string().min(1).describe('Vault-relative path of the target note, e.g. "PKMS/CLAUDE.md"'),
  },
  async ({ path }) => {
    try {
      const results = await reader.getBacklinks(path)
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [{ type: 'text' as const, text: `Error: ${message}` }],
        isError: true,
      }
    }
  }
)

const transport = new StdioServerTransport()
await server.connect(transport)
