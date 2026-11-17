# MCP servers

A catalogue of Model Context Protocol servers you can wire into n8n. Two n8n nodes consume this
world, and they point in opposite directions:

| Node | Direction | Use it when |
|---|---|---|
| **MCP Client Tool** (`@n8n/n8n-nodes-langchain.mcpClientTool`) | n8n calls an external MCP server | you want an AI Agent to use someone else's tools — a database, a browser, a filesystem |
| **MCP Server Trigger** (`@n8n/n8n-nodes-langchain.mcpTrigger`) | n8n *is* the MCP server | you want to expose workflows as tools to Claude Desktop, Cursor, or another agent |

This directory indexes what exists on the other side of the first case.

---

## What is in the index

| Field | Value |
|---|---|
| Servers listed (`servers`) | **4,978** |
| Official reference servers | 7 |
| From the curated community list | 4,971 |
| With an npm package and download count | 141 |
| Keyword-only packages (`keyword_only_packages`) | 802 |

Built by `tools/build_mcp_index.py` from three sources, merged by repository slug so a server
appears once with every source that listed it:

1. **`modelcontextprotocol/servers`** — the official reference servers: `fetch`, `filesystem`,
   `git`, `memory`, `sequentialthinking`, `time`, `everything`.
2. **`punkpeye/awesome-mcp-servers`** — the largest curated community list, ~5,000 entries
   across ~60 categories.
3. **npm, keyword `mcp-server`** — 1,000 packages scanned; those matching a listed repository
   contribute a download count, the rest are kept separately.

The split matters. A curated-list entry was at least read by a human. A package that only
matched the npm keyword **self-declared** that it is an MCP server — `yahoo-finance2` and
`agent-device` carry the keyword and are libraries, not servers. `keyword_only_packages` is
therefore kept out of default search results, and `search_mcp_servers` only includes them when
you ask with `include_keyword_only: true`.

---

## Using the index

```bash
# what is there for databases?
jq -r '.servers[] | select(.category|test("database";"i")) | "\(.name)\t\(.description[:60])"' \
   mcp-servers/index.json | head -10

# the most-downloaded servers that are also on the curated list
jq -r '.servers | sort_by(-(.downloads_last_month // 0))[:10][] | "\(.downloads_last_month // 0)\t\(.name)"' \
   mcp-servers/index.json
```

Or through the MCP server itself:

```json
{"query": "postgres", "limit": 5}
{"query": "browser", "category": "Browser Automation"}
{"include_keyword_only": true, "query": "excel"}
```

---

## Trust model

An MCP server is **not** a passive integration. It runs code, usually with whatever access you
give it, and an agent decides when to call it. Before you attach one:

1. **Prefer official.** `trust: "official"` means published by the MCP project.
2. **Read the source** of anything in `keyword_only_packages`, and of any community server that
   wants a filesystem path, a shell, or a database connection.
3. **Scope the credential** to the narrowest thing that works — a read-only database user, a
   token limited to one repository.
4. **Watch what it can reach.** A filesystem server with `~` as its root is a filesystem server
   with your SSH keys.
5. **Pin the version.** `npx -y pkg@1.4.2`, never a floating tag.

n8n side: the MCP Client Tool node keeps credentials in n8n, so a server that needs a token gets
it as a header — never paste a token into a prompt.

---

## Rebuilding

```bash
git clone --depth 1 https://github.com/modelcontextprotocol/servers.git vendor/mcp-servers
git clone --depth 1 https://github.com/punkpeye/awesome-mcp-servers.git vendor/awesome-mcp-servers
python3 tools/build_mcp_index.py --pages 4 --enrich 300
```

`--offline` re-merges from the two clones without touching npm. The npm downloads endpoint rate
limits scoped packages, so a rebuild can return fewer counts than the previous run — the numbers
are a snapshot, not a contract.

---

## Known gaps

- **No live registry feed.** `registry.modelcontextprotocol.io` is the canonical source and it is
  not reachable from this build environment, so the index is assembled from GitHub and npm.
- **No transport or auth metadata.** The curated list does not record whether a server speaks
  stdio or HTTP, or what auth it needs; check the server's own README.
- **No security review.** Listing is not endorsement. `sources` tells you who listed it, nothing
  more.
- **Descriptions are the list author's words**, truncated at 400 characters.
