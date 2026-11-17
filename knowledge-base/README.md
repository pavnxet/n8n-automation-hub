# n8n built-in node knowledge base

> This is the knowledge-base component of the **n8n Automation Hub** repository.
> Start at [`../README.md`](../README.md) for the whole picture, and
> [`../docs/architecture.md`](../docs/architecture.md) for how this directory is built.
> Build and validation scripts live in [`../tools/`](../tools/).

A machine-readable, agent-friendly split of the n8n built-in node documentation
(<https://docs.n8n.io/integrations/builtin>), built for one job: letting an AI agent
find the right node, learn its exact operations and parameters, and assemble a valid
n8n workflow.

**Contents:** 531 node records — 275 app nodes, 91 trigger nodes, 69 core nodes,
24 AI cluster root nodes, 72 AI cluster sub-nodes — plus 3,848 parsed operations and
322 credential types. 521 of the node records are enriched with the authoritative
parameter schema from the published packages (`n8n-nodes-base@2.15.1`,
`@n8n/n8n-nodes-langchain@2.48.3`). Snapshot: **2026-11-17**.

> **Read `AGENT-GUIDE.md` before generating a workflow.** It maps this KB onto n8n's
> workflow JSON: `type` = `workflow_type`, `typeVersion` = `type_version`, and the internal
> `resource`/`operation` values that the JSON actually needs.

---

## 1. Start here (3 steps)

**Step 1 — find candidate nodes.** Search the operation index, not the prose:

```bash
grep -i "append row" indexes/operations.jsonl | head -20
python3 tools/search.py "send whatsapp message"          # BM25, ranked
python3 tools/search.py "append row" --ops               # operations only
python3 tools/search.py "new email" --trigger            # trigger nodes only
```

**Step 2 — read the node record.**

```
nodes/<category>/<id>.json     structured: operations, exact parameter schema, credentials
nodes/<category>/<id>.md       the same documentation as clean readable markdown
```

**Step 3 — get the values the workflow JSON needs.**

```bash
jq '.workflow_type, .type_version, .credential_types' nodes/app-node/n8n-nodes-base.gmail.json
jq '.nodes["n8n-nodes-base.googleSheets"]' indexes/resources-operations.json
```

---

## 2. File map

| Path | What it is | Use it for |
|---|---|---|
| `AGENT-GUIDE.md` | KB → workflow JSON walkthrough, with two full examples | Read once before building |
| `catalog.json` | All 531 nodes, one compact entry each | Load the whole node list into a prompt |
| `manifest.json` | Build metadata, counts, coverage | Versioning / provenance |
| `indexes/operations.jsonl` | One JSON line per operation (3,848) | **Best file for "which node can do X"** |
| `indexes/resources-operations.json` | Internal `resource` / `operation` / `authentication` values per node (521 nodes) | Writing valid `parameters` in workflow JSON |
| `indexes/nodes.jsonl` | One line per node: id, type, typeVersion, ops, description | Grep / cheap keyword search |
| `indexes/keywords.json` | keyword → node ids (2,604 keywords) | Fast term → node lookup |
| `indexes/by-category.json` | category → node ids | Enumerate a category |
| `indexes/triggers.json` | All 91 trigger nodes | Picking the workflow start node |
| `indexes/ai-tools.json` | Nodes usable as AI Agent tools | Building agent workflows |
| `indexes/credentials.json` | 322 credential types + auth methods | Auth planning |
| `nodes/<category>/<id>.json` | Full node record | The authoritative per-node data |
| `nodes/<category>/<id>.md` | Clean markdown reference | Human/LLM reading, RAG chunks |
| `credentials/<id>.json` / `.md` | Credential type records | Auth setup |
| `examples/index.json` | 12 real n8n workflows shipped with the docs, with the node types each uses | Structural templates |
| `examples/workflows/` | The workflow JSON files themselves | Copy/adapt a working workflow |
| `schema.json` | JSON Schema for a node record | Validation |
| `tools/search.py` | BM25 CLI over the indexes (stdlib only) | Ranked search (mirror of `../tools/search.py`) |
| `../tools/build_kb.py` | Step 1 generator (docs → KB) | Rebuild from a newer docs snapshot |
| `../tools/enrich_kb.py` | Step 2 enricher (package → KB) | Rebuild the schema layer |

Categories: `app-node`, `trigger-node`, `core-node`, `cluster-root-node`, `cluster-sub-node`.

---

## 3. Node record schema

`nodes/app-node/n8n-nodes-base.gmail.json` (abridged):

```json
{
  "id": "n8n-nodes-base.gmail",
  "name": "Gmail",
  "category": "app-node",
  "workflow_type": "n8n-nodes-base.gmail",
  "type_version": 2.2,
  "type_versions": [2, 2.1, 2.2],
  "package": "n8n-nodes-base",
  "is_trigger": false,
  "is_ai_tool": true,
  "usable_as_tool": true,
  "description": "Use the Gmail node to automate work in Gmail, and integrate Gmail with other applications...",
  "doc_url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gmail",
  "credential_types": ["googleApi", "gmailOAuth2"],
  "credentials": {"name": "Google", "slug": "google", "json_file": "credentials/google.json"},
  "operations": [
    {
      "resource": "Message",
      "operation": "Send",
      "resource_value": "message",
      "operation_value": "send",
      "description": "a message",
      "doc": ".../gmail/message-operations#send-a-message",
      "parameters": [{"name": "To", "description": "Enter the email address you want the email sent to"}],
      "options": [{"name": "Attachments", "description": "..."}]
    }
  ],
  "operation_count": 25,
  "node_schema": {
    "parameter_count": 63,
    "parameters": [
      {"name": "resource", "displayName": "Resource", "type": "options", "default": "message",
       "options": [{"name": "Message", "value": "message"}, {"name": "Draft", "value": "draft"}]}
    ]
  },
  "events": [],
  "trigger_methods": [],
  "common_issues": [{"title": "401 unauthorized error", "summary": "..."}],
  "keywords": ["gmail", "draft", "message", "send", "thread"],
  "files": {"json": "nodes/app-node/n8n-nodes-base.gmail.json",
            "markdown": "nodes/app-node/n8n-nodes-base.gmail.md"}
}
```

| Field | Meaning |
|---|---|
| `workflow_type` | **The `type` string for workflow JSON.** Usually equals `id`, but not always — `n8n-nodes-base.emailimap` is really `n8n-nodes-base.emailReadImap`, and AI nodes live under `@n8n/n8n-nodes-langchain.` |
| `type_version` | The `typeVersion` to emit |
| `category` | `app-node`, `trigger-node`, `core-node`, `cluster-root-node`, `cluster-sub-node` |
| `is_trigger` | Starts a workflow (no input) |
| `is_ai_tool` / `usable_as_tool` | Can be attached to an AI Agent's Tools input |
| `operations[]` | Documented resource/operation pairs, with `*_value` internal values where the package provides them |
| `node_schema.parameters[]` | Exact parameter keys, types, defaults, option values and `displayOptions` |
| `parameters` | Node-level parameters as *documented* (mainly core and AI cluster nodes) |
| `events` | Trigger events |
| `trigger_methods` | `polling`, `webhook`, `schedule` where the docs indicate |
| `examples[]` | Complete example workflows embedded in the node's docs page |
| `common_issues` | Known errors with fixes |

---

## 4. Search recipes

```bash
# every operation that mentions "webhook"
jq -c 'select(.operation|test("webhook";"i"))' indexes/operations.jsonl

# nodes that touch sheets
jq -r 'select(.name|test("sheet";"i")) | "\(.type)\t\(.name)"' indexes/nodes.jsonl

# triggers for a given app
jq -r '.triggers[] | select(.name|test("slack";"i")) | .id' indexes/triggers.json

# nodes usable as AI agent tools
jq -r '.ai_tools[].id' indexes/ai-tools.json

# keyword lookup
jq -r '.keywords["invoice"][]' indexes/keywords.json

# internal values for a node's resource/operation dropdowns
jq '.nodes["n8n-nodes-base.slack"].operations' indexes/resources-operations.json
```

Python (ranked, no dependencies):

```bash
python3 tools/search.py "convert pdf to text" --limit 5
python3 tools/search.py "vector store" --category cluster-sub-node
```

---

## 5. Building a workflow

1. **Trigger** — `indexes/triggers.json`, or a core trigger (`scheduleTrigger`, `webhook`,
   `manualTrigger`, `formTrigger`, `chatTrigger`).
2. **Actions** — one `indexes/operations.jsonl` hit per step. Prefer a dedicated app node over
   `HTTP Request`, and `HTTP Request` over nothing.
3. **Parameters** — copy keys from `node_schema.parameters`, values from
   `indexes/resources-operations.json`.
4. **Credentials** — read `credential_types` and `credentials/<slug>.json`; tell the user which
   credential to create instead of inventing one.
5. **Emit JSON** — `nodes[]` with `id`, `name`, `type`, `typeVersion`, `position`, `parameters`;
   `connections{}` keyed by node name; AI sub-nodes connect with `ai_*` types.

Full walkthrough, two worked examples and a pre-flight checklist: **`AGENT-GUIDE.md`**.
When you need a structural reference, open `examples/index.json` and copy the closest
real workflow from `examples/workflows/`.

---

## 6. Coverage and limitations

- **Docs + package, two layers.** Prose, operations and credentials come from the docs; exact
  parameter schemas and internal enum values come from the published node packages. Where the
  two disagree, the package wins for JSON generation and the docs win for intent.
- **521 of 531 nodes have a `node_schema`.** Ten are documented but not present in the two
  packages at these versions: `confluence`, `kitemaker`, `microsoftdataverse`,
  `microsoftexcelsharepoint`, `databrickstrigger`, `microsoftsharepointtrigger`,
  `activationtrigger`, `messageanagent`, `n8n-mcp-registry.databricksgenie`,
  `n8n-nodes-langchain.embeddingsgooglepalm`. They carry docs only, with `node_schema: null`.
- **Built-in nodes only.** Community nodes are out of scope.
- **Version drift.** n8n ships weekly; this snapshot is dated 2026-11-17 against
  `n8n-nodes-base@2.15.1`. Verify anything critical against the live `doc_url`.
- **Docs text** is reproduced from the n8n docs repository, published under n8n's Sustainable
  Use License. Keep that attribution if you redistribute this KB.

---

## 7. Rebuilding

```bash
git clone --depth 1 https://github.com/n8n-io/n8n-docs.git
npm pack n8n-nodes-base @n8n/n8n-nodes-langchain      # or curl the tarballs
python3 ../tools/build_kb.py      # docs -> nodes/, catalog.json, indexes, examples
python3 ../tools/enrich_kb.py     # packages -> node_schema, resources-operations.json
```

Edit the path constants at the top of each script first. Both scripts preserve hand-written
files here (`README.md`, `AGENT-GUIDE.md`, `schema.json`) and delete only what they generate. Both steps are deterministic:
same inputs in, same KB out.
