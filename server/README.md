# MCP server

A Model Context Protocol server that turns the knowledge base into a **workflow engineering
assistant**: it plans a workflow from a request, retrieves real node schemas, generates
importable JSON, validates it against those schemas, audits it for security problems, traces
data flow, diagnoses failures — and, if you configure an n8n instance, tests it for real.

Standard library only. No dependencies, no build step, no network at runtime except the
optional n8n API.

---

## 1. Tools

Twenty tools in five groups. Full contracts and examples: [`../docs/mcp-tools.md`](../docs/mcp-tools.md).

### Discovery

| Tool | Answers |
|---|---|
| `search_operations` | "which node appends a row to a sheet?" — hybrid search with internal values |
| `search_nodes` | discovery without pinning an operation |
| `get_node` | one record; opt into `operations`, `schema`, `params`, `events`, `issues`, `examples` |
| `get_operation` | one operation's parameters and options |
| `list_triggers` | how a workflow can start (107 trigger nodes) |
| `resolve_enum` | "Append Row" → `append` |
| `search_community_nodes` | third-party packages, with a trust warning |
| `search_templates` / `get_template` | reusable patterns, with verification status |

### Validation and analysis

| Tool | Answers |
|---|---|
| `validate_workflow` | is it correctly configured against the node schemas? |
| `audit_workflow` | is it safe? secrets, dangerous nodes, plain HTTP, open webhooks, TLS |
| `analyze_data_flow` | does each expression read a field the upstream node produces? |
| `debug_workflow` | why did it fail, and what is the fix? |

### Authoring

| Tool | Answers |
|---|---|
| `plan_workflow` | turn a request into trigger + steps + credentials + risks + open questions |
| `generate_workflow` | produce importable JSON, validated, with marked placeholders |

### Live n8n (optional)

| Tool | Does |
|---|---|
| `test_workflow` | validates, then creates an **inactive** draft |
| `execute_workflow` | runs a workflow by id (opt-in, confirmed) |
| `get_execution_status` | status, per-node timings, error |
| `get_execution_data` | execution data, trimmed unless `include_items` |
| `get_execution_error` | the failure plus a diagnosis |

### Resources

`n8n://guide/agent`, `n8n://guide/knowledge-base`, `n8n://guide/workflow-conventions`,
`n8n://guide/security`, `n8n://guide/mcp-tools`, and the template `n8n://node/{id}`.

---

## 2. Run it

```bash
python3 server/mcp_server.py          # stdio JSON-RPC
python3 server/test_server.py         # 52 protocol and tool checks
python3 -m unittest discover -s tests # 79 unit, integration and regression tests
```

Install as a command:

```bash
pip install -e .                      # provides `n8n-hub-mcp`
```

Nothing but protocol messages is written to stdout; logs go to stderr. Tool results are capped
at 60 000 characters and also returned as `structuredContent` for clients that support it.

---

## 3. Configuration

Everything except the live tools works with no configuration at all.

| Variable | Default | Purpose |
|---|---|---|
| `N8N_BASE_URL` | — | e.g. `https://n8n.example.com` |
| `N8N_API_KEY` | — | Settings → n8n API → create key |
| `N8N_ALLOW_EXECUTE` | `false` | `1` enables `execute_workflow` |
| `N8N_KB_OUT` | `./knowledge-base` | alternate knowledge base location |

```bash
export N8N_BASE_URL="https://n8n-staging.example.com"
export N8N_API_KEY="…"          # never commit this
export N8N_ALLOW_EXECUTE=0      # leave off until you trust the target
python3 server/mcp_server.py
```

The key is sent only in the `X-N8N-API-KEY` header, is redacted from every error message, and
never appears in tool output.

### What the public API actually supports

The n8n public API v1 exposes `/workflows` and `/executions`. Running a workflow by id
(`POST /workflows/{id}/execute`) is newer than most deployed versions, so the client probes for
it: when the endpoint is missing, `execute_workflow` returns an explanation and the
alternatives (Webhook trigger, schedule, or `n8n execute --id <id>` on the host) instead of
pretending it worked.

### Safety model

| Rule | How it is enforced |
|---|---|
| Off by default | no URL/key → tools return `configured: false` with instructions |
| Never activate | the client only creates workflows; it never calls an activate endpoint |
| Never delete or overwrite | no delete or update call exists in the client |
| Execution is opt-in | `N8N_ALLOW_EXECUTE=1` **and** `confirm: true` |
| No credentials travel | credential references are stripped before upload and reported |
| No secrets in output | keys redacted, evidence truncated, item data omitted by default |

---

## 4. Client configuration

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "n8n-automation-hub": {
      "command": "python3",
      "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"],
      "env": { "N8N_BASE_URL": "https://n8n.example.com", "N8N_API_KEY": "…" }
    }
  }
}
```

### Cursor — `.cursor/mcp.json`

```json
{"mcpServers": {"n8n-automation-hub": {
  "command": "python3",
  "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"]}}}
```

### VS Code — `.vscode/mcp.json`

```json
{"servers": {"n8n-automation-hub": {
  "type": "stdio",
  "command": "python3",
  "args": ["/absolute/path/to/n8n-automation-hub/server/mcp_server.py"]}}}
```

### n8n itself

An **MCP Client Tool** node (`@n8n/n8n-nodes-langchain.mcpClientTool`) can attach this server to
an AI Agent, so a workflow can plan, generate and validate while it runs.

---

## 5. The loop this enables

```
request
  → plan_workflow            trigger, steps, operations, credentials, risks, open questions
  → search_operations        confirm each node exists and get internal values
  → get_operation            parameters and options for that operation
  → resolve_enum             labels → internal values
  → generate_workflow        importable JSON, placeholders marked, validated
  → validate_workflow        schema-aware report with suggestions
  → audit_workflow           secrets, dangerous nodes, exposure
  → analyze_data_flow        expression ↔ upstream field check
  → test_workflow            inactive draft on a real instance (optional)
  → execute_workflow         run it (opt-in, confirmed)
  → get_execution_error      failure → diagnosis → corrected proposal
```

---

## 6. Module map

| Module | Responsibility |
|---|---|
| `mcp_server.py` | protocol, tool registry, response envelope |
| `kb.py` | knowledge base access: records, indexes, enums, community packages |
| `search.py` | hybrid ranking, intent classification, fallback |
| `schema.py` | parameter visibility (`displayOptions`), types, enum values, required checks |
| `validation.py` | the schema-aware validator |
| `expressions.py` | quote-aware `{{ … }}` parser and reference extraction |
| `planner.py` | request → plan |
| `generator.py` | plan → workflow JSON, with repairs |
| `analysis.py` | data-flow simulation |
| `debugger.py` | error classification and repair proposals |
| `audit.py` | security and reliability findings |
| `n8n_api.py` | optional public-API client |
| `templates.py` | template library access |

Two deliberate couplings: the validator is the only thing that decides `valid`, and the
generator calls it rather than re-implementing checks. `audit.py` reuses
`tools/security_scan.py`, so the MCP audit and CI can never disagree.

---

## 7. Known limits

- **Static ≠ executed.** `validate_workflow`, `audit_workflow` and `analyze_data_flow` are
  analysis. Only `execute_workflow` runs anything, and only when configured.
- **Field shapes are inferred.** An HTTP response or a database query has an unknowable shape,
  so data-flow analysis marks it unknown rather than guessing.
- **No community node schemas.** Third-party packages are searchable but their parameters are
  not in the knowledge base.
- **10 documented nodes have no package schema** (`node_schema: null`) and cannot be
  parameter-validated.
- **`typeVersion` is a snapshot** (2026-11-17). Refresh the knowledge base to move forward.
- **Stdio only.** No HTTP transport and no multi-user auth; it is a local tool.
