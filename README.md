# PKMS

PKMS is a local-first middleware that bridges your Markdown vault and any LLM via MCP. If you spend 5–10 minutes navigating your vault before every LLM session — copy-pasting relevant notes into the context window — this eliminates that: it exposes vault structure (notes, backlinks, full-text search) directly to the AI, so the LLM can navigate your knowledge graph without manual intervention. It runs entirely on your machine; no data leaves, no cloud dependency. Works with any MCP-compatible client and any LLM, including local models via Ollama or LM Studio. AGPL v3. See [Install](#install) to get started.

## Install

**Requirements:** Node.js ≥ 18, pnpm

```bash
git clone https://github.com/gauthierae/PKMS
cd pkms && pnpm install && pnpm build
```

Add to your MCP client config (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pkms": {
      "command": "node",
      "args": ["100-Source/apps/standalone/dist/mcp-server.js"],
      "env": { "VAULT_PATH": "/absolute/path/to/your/vault" }
    }
  }
}
```

Exposes three tools to the LLM: `get_note`, `search_notes`, `get_backlinks`.
