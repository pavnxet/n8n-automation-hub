# MCP tool reference

Twenty-four tools in five groups. Every tool returns the same envelope:

- `content[0].text` — pretty-printed JSON (for clients that only read text);
- `structuredContent` — the same object, for clients that support structured output;
- `isError` — `true` when the tool failed or the thing being checked is invalid.

Nothing here invents n8n behaviour. Node types, operations, parameter names and enum values all
come from `knowledge-base/`, which is generated from the n8n docs and the published node
packages. Where the server cannot know something it says so — `executed: false`,
`simulated: true`, `node_schema: null`, `open_questions: [...]`.

---

## Discovery

### `search_operations`

Hybrid search for "which node does X". Ranks exact node names above aliases above operation
names above fuzzy terms, routes by intent (trigger / operation / node / pattern), and drops
weak matches instead of padding the list.

| Input | Type | Notes |
|---|---|---|
| `query` | string, required | What you want to do |
| `limit` | int, default 8 | 1–50 |
| `category` | enum | `app-node`, `trigger-node`, `core-node`, `cluster-root-node`, `cluster-sub-node` |
| `trigger_only` | bool | Only workflow entry points |
| `min_confidence` | float, default 0.28 | Results below this are omitted |

```json
{"query": "append row to a spreadsheet", "limit": 3}
```

```json
{
  "query": "append row to a spreadsheet",
  "intent": {"intent": "operation", "is_trigger_query": false},
  "count": 3,
  "results": [
    {
      "node": "n8n-nodes-base.googlesheets",
      "workflow_type": "n8n-nodes-base.googleSheets",
      "name": "Google Sheets",
      "category": "app-node",
      "type_version": 4.7,
      "match": "operation",
      "confidence": 0.44,
      "confidence_band": "medium",
      "operation": {"resource": "Sheet Within Document", "operation": "Append Row",
                    "resource_value": "sheet", "operation_value": "append"},
      "why": ["operation 'Sheet Within Document / Append Row' covers 60% of the terms"],
      "doc": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets"
    }
  ]
}
```

### `search_nodes`

Same ranking, node-level results only. Useful when you know the node but not the operation.

### `get_node`

Read one record. Defaults to a compact summary; `sections` opts into depth.

```json
{"node": "Gmail", "sections": ["operations", "issues"]}
```

| Section | Adds |
|---|---|
| `operations` | every documented operation with parameters and options |
| `schema` | the exact parameter schema: names, types, defaults, option values, `displayOptions` |
| `params` | node-level parameters as documented |
| `events` | trigger events and trigger methods |
| `issues` | common errors with fixes |
| `examples` | example workflows bundled with the docs |

### `get_operation`

```json
{"node": "n8n-nodes-base.gmail", "operation": "Send"}
```

Returns the matching operation(s) with `parameters`, `options`, internal values and a doc link.

### `list_triggers`

```json
{"query": "slack", "limit": 10}
```

### `resolve_enum`

```json
{"node": "n8n-nodes-base.googleSheets", "label": "Append Row"}
```

```json
{"matched": [{"resource_value": "sheet", "operation": "Append Row",
              "operation_value": "append"}],
 "resources": [{"name": "Document", "value": "spreadsheet"},
               {"name": "Sheet Within Document", "value": "sheet"}],
 "has_resource_parameter": true}
```

### `search_community_nodes`

Third-party npm packages. Always carries an unverified-code warning.

### `search_mcp_servers`

Find an external MCP server to attach to an AI Agent through the **MCP Client Tool** node — or to
mirror with an **MCP Server Trigger**.

```json
{"query": "postgres", "limit": 3}
```

```json
{
  "query": "postgres", "count": 3,
  "counts": {"servers": 4978, "official": 7, "from_curated_list": 4971,
             "on_npm": 141, "keyword_only": 802},
  "results": [{"id": "antonorlov/mcp-postgres-server", "name": "antonorlov/mcp-postgres-server",
               "category": "Databases", "trust": "community",
               "sources": ["punkpeye/awesome-mcp-servers"], "keyword_only": false}],
  "categories": ["Developer Tools", "Finance & Fintech", "…"]
}
```

| Input | Notes |
|---|---|
| `query` | required; empty string returns the most-downloaded entries |
| `category` | e.g. `Databases`, `Browser Automation` |
| `min_downloads` | filter on last-30-day npm downloads |
| `include_keyword_only` | also return packages that only *claim* the npm keyword `mcp-server` — unreviewed, excluded by default |

### `get_mcp_server`

```json
{"name": "modelcontextprotocol/servers/fetch"}
```

Accepts an id, a display name, a repository slug or an npm package.

### `search_reference`

Search the reference layer — the knowledge the node records cannot carry: expression variables
and functions, environment variables, release history, and breaking changes.

```json
{"query": "$fromAI", "limit": 3}
```

```json
{
  "query": "$fromAI",
  "count": 1,
  "counts": {"expressions": 243, "env-vars": 364, "releases": 609, "breaking-changes": 46},
  "results": [
    {"kind": "expressions", "score": 8, "name": "$fromAI()", "section": "root",
     "kind_detail": "function",
     "description": "Generate a value with an AI model, with a description of what it should be",
     "doc_url": "https://docs.n8n.io/build/work-with-data/transform-data/expression-reference"}
  ]
}
```

| `kind` | Contents | Example query |
|---|---|---|
| `expressions` | 243 documented variables, properties and methods | `$jmespath`, `toDateTime`, `base64Decode` |
| `env-vars` | 364 self-hosting variables with type, default, category | `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` |
| `releases` | 609 releases with date and summary | `2.29`, `1.100` |
| `breaking-changes` | 46 categorised entries from the v2 and v3 pages | `removed nodes`, `expression helpers` |

Omit `kind` to search all four.

### `get_reference`

Exact lookup by name, version or title:

```json
{"kind": "env-vars", "name": "N8N_PORT"}
```

```json
{"kind": "env-vars", "name": "N8N_PORT", "type": "Number", "default": "5678",
 "description": "The port n8n listens on.", "category": "deployment",
 "doc_url": "https://docs.n8n.io/deploy/…/use-environment-variables"}
```

Two of these files are wired into validation rather than being read-only reference: an unknown
`$global` in an expression is checked against `expressions.json`, and an unknown node type is
matched against documented removals, producing `node_removed_in_version` with the version that
removed it.

### `search_templates` / `get_template`

Reusable patterns. Every entry states its verification level:

| `status` | Meaning |
|---|---|
| `validated` | passed this repository's static schema validation |
| `documented` | shipped by n8n as an example; not executed here |
| `executed` | ran successfully on a real instance (none yet) |

---

## Validation and analysis

### `validate_workflow`

Schema-aware validation. The important part is that it checks **parameters**, not just
structure: a node whose schema marks `url` as required fails when `url` is missing.

```json
{"workflow": {"name": "t", "nodes": [
  {"parameters": {}, "id": "1", "name": "HTTP Request",
   "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.4, "position": [0, 0]}],
  "connections": {}}}
```

```json
{
  "valid": false,
  "errors": [
    {"severity": "error",
     "code": "missing_required_parameter",
     "message": "The URL parameter is required.",
     "node": "HTTP Request",
     "node_type": "n8n-nodes-base.httpRequest",
     "parameter": "url",
     "suggestion": "Provide a value for 'url' — The URL to make the request to.",
     "doc": "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest"}
  ],
  "warnings": [],
  "info": [],
  "stats": {"nodes": 1, "errors": 1, "warnings": 0},
  "checked": {"structure": true, "node_types": true, "versions": true,
              "required_parameters": true, "types_and_enums": true,
              "connections": true, "expressions": true, "credentials": true},
  "summary": "Invalid: 1 error(s) in 1 node(s).\n- HTTP Request: The URL parameter is required."
}
```

Error codes: `missing_required_parameter`, `invalid_enum`, `wrong_type`,
`invalid_resource_locator`, `empty_resource_locator` (warning), `invalid_json`,
`unsupported_type_version`, `missing_type_version`, `deprecated_type_version` (warning),
`duplicate_node_name`, `duplicate_node_id`, `unknown_node_type`, `connection_unknown_target`,
`connection_unknown_source`, `connection_invalid_index`, `expression_unknown_node`,
`expression_syntax`, `unknown_global`, `invalid_credential_structure`,
`missing_credential_reference` (warning), `orphan_node` (warning), `no_trigger` (warning).

Optional `checks` object toggles individual passes.

### `audit_workflow`

Security and reliability. Findings carry `severity` (`critical` / `high` / `medium` / `low` /
`info`), a `rule`, redacted `evidence` and a `remediation`.

```json
{"risk": "high", "passed": false,
 "findings": [{"severity": "high", "category": "dangerous_node", "rule": "SEC004",
               "node": "Run", "message": "uses n8n-nodes-base.executeCommand, which runs shell commands on the host",
               "remediation": "Remove the node, or restrict who can edit this workflow."}]}
```

### `analyze_data_flow`

What each node receives and emits, which expressions it uses, and where an expression reads a
field the upstream node does not produce. Optional `fixtures` supply sample items.

```json
{"workflow": {...}, "fixtures": {"HTTP Request": [{"title": "hello"}]}}
```

Returns `simulated: true`, `execution_order`, per-node `input_fields` / `output_fields` /
`expressions` / `fixture_resolved`, and `findings` (`field_not_upstream`,
`loop_without_close`, `message_without_body`, `aggregate_without_fields`).

An upstream node whose shape is unknowable (an HTTP response, a database query) is treated as
unknown and produces no false "missing field" warnings.

### `debug_workflow`

```json
{"workflow": {...}, "error_text": "NodeApiError: 401 Unauthorized", "node": "Post"}
```

Classifies the failure (authentication, rate limit, network, expression data, data format,
query, file, configuration), gives the evidence, the fix, and — when the repair is mechanical —
a `corrected_workflow` with `requires_approval: true`. Nothing is applied automatically.

---

## Authoring

### `plan_workflow`

```json
{"request": "Get Hacker News stories, filter out previously processed stories, summarize new "
            "stories using an API, save them to a database, and send the results to Telegram."}
```

```json
{
  "objective": "Get Hacker News stories, …",
  "trigger": {"node_type": "n8n-nodes-base.manualTrigger",
              "reason": "no schedule, webhook or app event was described", "confidence": 0.35},
  "steps": [
    {"order": 1, "node_type": "n8n-nodes-base.hackerNews", "node_name": "Hacker News",
     "operation": {"resource": "Article", "operation": "Get a Hacker News article"},
     "confidence": 0.8, "why": ["the request names 'hacker news'"]},
    {"order": 2, "node_type": "n8n-nodes-base.removeDuplicates",
     "note": "Cross-run deduplication needs a stable key and stored history", "confidence": 0.75},
    {"order": 3, "node_type": "n8n-nodes-base.httpRequest", "confidence": 0.45},
    {"order": 4, "node_type": "n8n-nodes-base.postgres",
     "operation": {"operation_value": "insert"}, "confidence": 0.65},
    {"order": 5, "node_type": "n8n-nodes-base.telegram",
     "operation": {"operation_value": "sendMessage"}, "confidence": 0.65}
  ],
  "credentials": [{"type": "postgres", "used_by": ["Postgres"]},
                  {"type": "telegramApi", "used_by": ["Telegram"]}],
  "risks": ["HTTP calls need a timeout and retry policy; add an error workflow."],
  "open_questions": ["Which API or service should 'summarize new stories using an API' call?",
                     "Which database should 'save them to a database' write to?"],
  "status": "proposed"
}
```

The planner only names nodes that exist in the knowledge base and operations that node
documents. When a request implies something with no dedicated node, it says so in
`open_questions` instead of inventing one.

### `generate_workflow`

```json
{"request": "Every morning at 8 fetch the weather from an API and post it to Slack"}
```

Returns:

| Field | Meaning |
|---|---|
| `workflow` | importable JSON: nodes, connections, positions, settings, sticky note |
| `validation` | the full report from `validate_workflow` |
| `placeholders` | required values the request did not supply, with the reason |
| `fixes_applied` | mechanical repairs the generator made (enum values, missing typeVersion) |
| `importable` | `true` when validation has no errors |
| `executed` | always `false` — generation is not execution |

Parameter values come from schema defaults, resolved operation values, and marked
placeholders. Credentials are never fabricated: the sticky note lists the credential types to
attach.

---

## Live n8n (optional)

All five tools need `N8N_BASE_URL` and `N8N_API_KEY`. Without them they return
`configured: false` and a `how_to_configure` hint — nothing else breaks.

| Tool | Does | Safety |
|---|---|---|
| `test_workflow` | validates, then creates an **inactive** draft | strips credentials, never activates |
| `execute_workflow` | runs a workflow by id | needs `N8N_ALLOW_EXECUTE=1` **and** `confirm: true` |
| `get_execution_status` | status, per-node timings, error summary | read-only |
| `get_execution_data` | execution data, trimmed to counts unless `include_items` | read-only |
| `get_execution_error` | just the failure plus a diagnosis | read-only |

```json
{"workflow_id": "123", "confirm": true}
```

```json
{"executed": false, "reason": "endpoint not available",
 "detail": "This n8n version's public API has no POST /workflows/{id}/execute endpoint. Trigger the workflow another way: add a Webhook trigger and call it, use a schedule, or run `n8n execute --id <id>` on the host."}
```

`test_workflow` on a workflow that fails validation uploads nothing:

```json
{"validation": {"valid": false, "...": "..."}, "created": false,
 "note": "Not uploaded: fix the validation errors first."}
```

---

## Resources

| URI | Contents |
|---|---|
| `n8n://guide/agent` | how to turn the knowledge base into a workflow |
| `n8n://guide/knowledge-base` | field-by-field record reference |
| `n8n://guide/workflow-conventions` | repository rules for workflow JSON |
| `n8n://guide/security` | secret handling and import safety |
| `n8n://guide/mcp-tools` | this document |
| `n8n://reference/index` | counts and file map for the reference layer |
| `n8n://mcp-servers` | the MCP server catalogue guide and trust model |
| `n8n://node/{id}` | full Markdown reference for one node |

---

## Error behaviour

| Situation | Response |
|---|---|
| Unknown tool | JSON-RPC error `-32602` with the list of available tools |
| Unknown method | JSON-RPC error `-32601` |
| Bad arguments | JSON-RPC error `-32602` naming the missing argument |
| Unknown node / template | tool result with `isError: true` and a hint |
| Invalid workflow JSON | tool result with `isError: true` and the parse error |
| Internal exception | tool result with `isError: true`; the traceback goes to stderr only |

Tool results are capped at 60 000 characters. Filesystem paths and stack traces are never
returned to the client.
