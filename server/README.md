# MCP server

Exposes the knowledge base to any Model Context Protocol client — Claude Desktop, Cursor,
VS Code, an n8n AI agent — so an agent can look up nodes and **validate the workflow it just
wrote** instead of guessing.

Standard library only: no dependencies, no build step, no network access at runtime.

---

## 1. Tools

| Tool | Answers | Why it exists |
|---|---|---|
| `search_operations` | "which node appends a row to a sheet?" | Returns ranked resource/operation pairs **with the internal values** workflow JSON needs |
| `search_nodes` | "what does n8n have for Slack?" | Discovery without pinning an operation |
| `get_node` | "tell me about Gmail" | Compact summary; opt into `operations`, `schema`, `params`, `events`, `issues`, `examples` |
| `get_operation` | "what are the fields for Gmail → Send?" | One operation's parameters and options, nothing else |
| `list_triggers` | "how can this workflow start?" | The 91 trigger nodes, filterable |
| `resolve_enum` | "'Append Row' → ?" | Label → internal value, plus the whole option table |
| `validate_workflow` | "will this import?" | Runs the **same lint as CI** on the JSON before a human sees it |

Resources: `n8n://guide/agent`, `n8n://guide/knowledge-base`,
`n8n://guide/workflow-conventions`, `n8n://guide/security`, plus the template
`n8n://node/{id}` for a node's full Markdown page.

---

## 2. Run it

```bash
python3 server/mcp_server.py          # speaks JSON-RPC on stdio
python3 server/test_server.py         # 20 protocol + tool assertions
```

Install as a command (optional):

```bash
pip install -e .                      # provides `n8n-hub-mcp`
```

Nothing is printed to stdout except protocol messages; logs go to stderr. A tool result is
capped at 60 000 characters so a greedy call cannot flood a context window.

---

## 3. Client configuration

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "n8n-automation-hub": {
      "command": "python3",
      "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"]
    }
  }
}
```

### Cursor

`.cursor/mcp.json` in your project, or the global equivalent:

```json
{
  "mcpServers": {
    "n8n-automation-hub": {
      "command": "python3",
      "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"]
    }
  }
}
```

### VS Code

`.vscode/mcp.json`:

```json
{
  "servers": {
    "n8n-automation-hub": {
      "type": "stdio",
      "command": "python3",
      "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"]
    }
  }
}
```

### n8n itself

An **MCP Client Tool** node (`@n8n/n8n-nodes-langchain.mcpClientTool`) can attach this server
to an AI Agent, so a workflow can look up nodes and validate JSON while it runs. Point the
node at the server over stdio, or wrap it in a small HTTP bridge if your instance is remote —
the server deliberately speaks stdio only.

---

## 4. The loop this enables

```
user asks for an automation
        │
        ▼
search_operations "post message to slack"      → n8n-nodes-base.slack, message / post
        │
        ▼
get_operation "n8n-nodes-base.slack" "Send"    → parameters: channel, text, ...
        │
        ▼
resolve_enum "n8n-nodes-base.slack" "Send"     → operation_value: "post"
        │
        ▼
agent writes workflow JSON
        │
        ▼
validate_workflow { ... }                      → valid: true, warnings: [...]
        │
        ▼
hand the user JSON that already passed CI
```

Without the server, steps 1–3 are a filesystem search and step 5 does not exist.

---

## 5. Protocol notes

- Transport: stdio, newline-delimited JSON-RPC 2.0 — one message per line.
- Protocol version: echoes the client's `protocolVersion`, defaulting to `2024-11-05`.
- Capabilities advertised: `tools` (list, call) and `resources` (list, read, templates).
- Errors: unknown method → `-32601`; unknown tool or bad arguments → `-32602`; a tool that
  fails returns `isError: true` with a message rather than a transport error, so the agent can
  read the reason.
- `validate_workflow` imports `tools/validate_repo.py` directly, so the server and CI can
  never disagree about what "valid" means.

---

## 6. Known limits

- **Stdio only.** No HTTP transport, no auth, no multi-user story. It is a local tool.
- **Read-only.** Nothing here writes to the repository or to an n8n instance.
- **Snapshot-bound.** Results reflect the knowledge base committed alongside it; refresh the
  KB (`tools/build_kb.py`, `tools/enrich_kb.py`) to move forward.
- **No community nodes in lookups.** They are indexed separately in
  `community-nodes/index.json` and are not searchable through these tools.
