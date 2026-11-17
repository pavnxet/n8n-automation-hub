# AGENT-GUIDE — from this knowledge base to a working n8n workflow

Read this once. It explains how the KB maps onto n8n's workflow JSON, so you can go from
a user request to a valid workflow without guessing.

---

## 1. The n8n workflow object

An n8n workflow is JSON with four top-level keys:

```json
{
  "name": "My workflow",
  "nodes": [
    {
      "parameters": {},
      "id": "a1b2c3d4-0000-4000-8000-000000000001",
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.3,
      "position": [0, 0]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{ "node": "HTTP Request", "type": "main", "index": 0 }]]
    }
  },
  "settings": {}
}
```

Rules that matter:

- **`type` is the `workflow_type` field** in a node record, not the docs id. They usually
  look the same (`n8n-nodes-base.gmail`), but some differ — the docs page
  `n8n-nodes-base.emailimap` is really `n8n-nodes-base.emailReadImap`, and every AI node is
  in the `@n8n/n8n-nodes-langchain.` namespace. **Always take `workflow_type`.**
- **`typeVersion`** — take `type_version` from the record. It is the highest version the
  published package ships; n8n accepts it.
- **`name` is the connection key.** `connections` is keyed by node *name*, not id, so names
  must be unique. Give each node a readable, unique name ("Gmail — send receipt").
- **`id`** is any UUID v4 string; it only has to be unique inside the workflow.
- **`position`** is `[x, y]` in pixels; `[0,0]`, `[220,0]`, `[440,0]` … is a fine left-to-right
  layout. Vertical spacing of 150–200 px keeps branches readable.
- **Every connection entry** is `{"<source name>": {"<output type>": [[targets...]]}}`, where
  the outer array is one entry per output branch (IF/Filter/Switch have 2+ branches).

---

## 2. Build procedure

**Step 1 — understand the trigger.** Ask: does this workflow start on a schedule, a webhook,
a form, a chat message, or an app event?

```bash
jq -r '.triggers[] | select(.name|test("slack";"i")) | "\(.id)  \(.name)"' indexes/triggers.json
```

Core triggers cover most cases: `n8n-nodes-base.scheduleTrigger`, `n8n-nodes-base.webhook`,
`n8n-nodes-base.manualTrigger`, `n8n-nodes-base.formTrigger`, `n8n-nodes-base.chatTrigger`.

**Step 2 — find one node per step, from the operation index.**

```bash
grep -i "append row" indexes/operations.jsonl
python3 tools/search.py "post message to slack" --ops
```

**Step 3 — read the node record and confirm the operation exists.**

```bash
jq '{name, workflow_type, type_version, operations: [.operations[] | {resource, operation, resource_value, operation_value}]}' \
   nodes/app-node/n8n-nodes-base.slack.json
```

**Step 4 — get the exact parameter values.** `indexes/resources-operations.json` holds the
internal values (`resource`, `operation`, `authentication`) — these are what the workflow JSON
needs, while the docs show the human labels.

| Docs say | JSON needs |
|---|---|
| Resource: *Sheet Within Document*, Operation: *Append Row* | `"resource": "sheet"`, `"operation": "append"` |
| Resource: *Message*, Operation: *Send* (Slack) | `"resource": "message"`, `"operation": "post"` |
| Resource: *Message*, Operation: *Send* (Gmail) | `"resource": "message"`, `"operation": "send"` |

Then pull the field list from `node_schema.parameters` in the same record — each entry has
`name` (JSON key), `displayName`, `type`, `default`, `options` (label → value) and
`displayOptions` (which shows it). Copy `name` and `default`; copy option `value`s, not labels.

**Step 5 — plan credentials, don't invent them.**

```bash
jq '.credential_types, .credential_details' nodes/app-node/n8n-nodes-base.gmail.json
```

`credential_types` are the internal credential names (`gmailOAuth2`, `slackApi`). A workflow
JSON never contains secrets: the user attaches a credential in the n8n UI after import. Tell
them which credential to create — read `credentials/<slug>.json` for the auth methods.

**Step 6 — write the JSON, then check it.** See the checklist in §6.

---

## 3. Example: schedule → HTTP → filter → Google Sheets

Every type/version below is copied from this KB (Gmail, Sheets and HTTP Request versions move
with each release — re-read the record before pasting this into a newer instance).

```json
{
  "name": "Daily FX rate to Sheets",
  "nodes": [
    {
      "parameters": { "rule": { "interval": [{ "field": "hours", "hoursInterval": 24 }] } },
      "id": "11111111-1111-4111-8111-111111111111",
      "name": "Every day",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.3,
      "position": [0, 0]
    },
    {
      "parameters": {
        "url": "https://api.frankfurter.app/latest?from=INR&to=USD",
        "options": {}
      },
      "id": "22222222-2222-4222-8222-222222222222",
      "name": "Get rate",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.4,
      "position": [220, 0]
    },
    {
      "parameters": {
        "conditions": {
          "options": { "caseSensitive": true, "version": 2 },
          "conditions": [
            {
              "leftValue": "={{ $json.rates.USD }}",
              "rightValue": "",
              "operator": { "type": "number", "operation": "exists", "singleValue": true }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "33333333-3333-4333-8333-333333333333",
      "name": "Rate present?",
      "type": "n8n-nodes-base.filter",
      "typeVersion": 2.3,
      "position": [440, 0]
    },
    {
      "parameters": {
        "operation": "append",
        "documentId": { "__rl": true, "mode": "list", "value": "" },
        "sheetName": { "__rl": true, "mode": "list", "value": "" },
        "columns": {
          "mappingMode": "defineBelow",
          "value": { "rate": "={{ $json.rates.USD }}" },
          "matchingColumns": [],
          "schema": []
        },
        "options": {}
      },
      "id": "44444444-4444-4444-8444-444444444444",
      "name": "Append to sheet",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.7,
      "position": [660, 0]
    }
  ],
  "connections": {
    "Every day": { "main": [[{ "node": "Get rate", "type": "main", "index": 0 }]] },
    "Get rate": { "main": [[{ "node": "Rate present?", "type": "main", "index": 0 }]] },
    "Rate present?": { "main": [[{ "node": "Append to sheet", "type": "main", "index": 0 }], []] }
  },
  "settings": {}
}
```

Notes on what the KB told us here: `googleSheets` is `typeVersion` 4.7 and its sheet resource
value is `sheet` (the default operation is `append`, so it can be omitted); `filter` is 2.3
and needs two connection branches, even when the second is empty.

---

## 4. Example: an AI agent cluster

AI nodes connect with **typed** connections, not `main`. The agent is the root; models,
memory and tools are sub-nodes attached by type:

```json
"connections": {
  "Chat Trigger": { "main": [[{ "node": "AI Agent", "type": "main", "index": 0 }]] },
  "OpenAI Chat Model": {
    "ai_languageModel": [[{ "node": "AI Agent", "type": "ai_languageModel", "index": 0 }]]
  },
  "Simple Memory": { "ai_memory": [[{ "node": "AI Agent", "type": "ai_memory", "index": 0 }]] },
  "HTTP Request Tool": { "ai_tool": [[{ "node": "AI Agent", "type": "ai_tool", "index": 0 }]] }
}
```

- Root node type: `@n8n/n8n-nodes-langchain.agent` (typeVersion 3.1 in this snapshot).
- Chat model: `@n8n/n8n-nodes-langchain.lmChatOpenAi` (1.3), credential `openAiApi`.
- Memory: `@n8n/n8n-nodes-langchain.memoryBufferWindow` (1.4).
- Any node with `is_ai_tool: true` can be dropped in as a tool — `indexes/ai-tools.json` lists
  them, and `grep '"usable_as_tool": true'` over the node records finds more.

Connection type names you may need: `ai_languageModel`, `ai_memory`, `ai_tool`,
`ai_outputParser`, `ai_embedding`, `ai_vectorStore`, `ai_document`, `ai_textSplitter`,
`ai_retriever`, `ai_reranker`.

---

## 5. Expressions and data mapping

- Reference the current item with `{{ $json.fieldName }}`; prefix with `=` in JSON
  (`"text": "={{ $json.message }}"`), otherwise the string is treated as literal.
- Previous node output: `{{ $('Node Name').item.json.field }}`.
- Loops/branches: `{{ $item(0).$node["Node Name"].json.id }}`.
- Binary data is under `$binary`; use a *Convert to File* / *Extract from File* node
  (`n8n-nodes-base.convertToFile`, `n8n-nodes-base.extractFromFile`) rather than raw base64.
- Code node: `n8n-nodes-base.code` (typeVersion 1), `parameters.jsCode` returns
  `[{ json: {...} }]`.

---

## 6. Pre-flight checklist

1. Exactly one trigger node, and it is the entry point.
2. Every `type` equals a record's `workflow_type`; every `typeVersion` equals `type_version`.
3. Node names are unique and match the `connections` keys exactly.
4. Every `resource` / `operation` value comes from `indexes/resources-operations.json`, never
   from the display label.
5. Every required credential is listed for the user; no secrets, tokens or IDs invented.
6. `position` values are distinct and laid out left to right.
7. Branching nodes (IF, Switch, Filter) have as many `main` arrays as outputs.
8. Fields you could not verify are left at the schema `default` and flagged to the user,
   rather than guessed.

---

## 7. Common mistakes

- **Using the docs label as the value.** `"resource": "Sheet Within Document"` fails; the value
  is `"sheet"`.
- **Using the docs id as the type.** `n8n-nodes-base.emailimap` should be
  `n8n-nodes-base.emailReadImap`; langchain nodes need the `@n8n/` prefix.
- **Connecting sub-nodes with `main`.** AI sub-nodes use `ai_*` connection types.
- **Forgetting `typeVersion`.** n8n loads the node but parameter names may not match.
- **Inventing credential values.** Import creates the node with an empty credential; the user
  picks or creates one. Name the credential type so they know what to make.
- **Assuming a parameter exists because a blog post used it.** Trust `node_schema.parameters`;
  if a field is absent there, it is not available in this version.

---

## 8. Where each answer lives

| Question | File |
|---|---|
| Which node sends a WhatsApp message? | `indexes/operations.jsonl` (grep) or `tools/search.py --ops` |
| What are the exact parameter names for Gmail send? | `nodes/app-node/n8n-nodes-base.gmail.json` → `node_schema.parameters` |
| What is the internal value of "Append Row"? | `indexes/resources-operations.json` |
| Which nodes can be AI tools? | `indexes/ai-tools.json` |
| How do I authenticate to Slack? | `credentials/slack.json` |
| Why does this node fail with 401? | `common_issues` in the node record |
| Which nodes exist at all? | `catalog.json` |
| What does a working workflow look like? | `examples/index.json` → `examples/workflows/<file>.json` |
