# n8n Automation Hub

An open, version-controlled home for n8n work: **ready-to-import automations**, a
**machine-readable knowledge base of every built-in node**, an **MCP server** that puts that
knowledge in front of an AI agent, and the **provenance record** for every source that feeds
them.

Built for two readers at once:

- **You, in the n8n editor** — import a workflow, attach a credential, ship it.
- **An AI agent, headless** — search 3,848 operations, read exact parameter schemas, generate
  workflow JSON, and validate it before handing it over.

---

## Table of contents

1. [What is in this repository](#1-what-is-in-this-repository)
2. [Quick start](#2-quick-start)
3. [Repository layout](#3-repository-layout)
4. [The knowledge base](#4-the-knowledge-base)
5. [Automations](#5-automations)
6. [Community nodes](#6-community-nodes)
7. [MCP server](#7-mcp-server)
8. [Sources and provenance](#8-sources-and-provenance)
9. [Tooling](#9-tooling)
10. [Security model](#10-security-model)
11. [Working conventions](#11-working-conventions)
12. [Licensing](#12-licensing)
13. [Roadmap](#13-roadmap)
14. [Contributing](#14-contributing)

---

## 1. What is in this repository

| Area | Path | What it holds | Scale |
|---|---|---|---|
| Knowledge base | `knowledge-base/` | Every n8n built-in node as JSON + Markdown, with operations, parameter schemas, credentials and search indexes | 531 nodes · 3,848 operations · 322 credentials |
| Automations | `automations/` | Importable workflow JSON, grouped by AI / integrations / core / patterns | 12 seed workflows |
| MCP server | `server/` | Model Context Protocol server: 8 tools, 5 resources, stdlib only | 24 protocol tests |
| Community nodes | `community-nodes/` | npm index of community node packages, a top-100 ranked by real download counts, and the approved shortlist | 1,500 indexed · 100 ranked |
| Sources | `sources/` | Registry of official and unofficial sources, with licences, quality notes and check dates | 14 sources |
| Tooling | `tools/` | Validators, security scanner, KB builders, BM25 search, node ranker | 7 scripts |
| Documentation | `docs/` | Architecture, workflow conventions, importing guide, research notes, roadmap | 5 documents |

Snapshot date: **2026-11-17**. Node schemas come from `n8n-nodes-base@2.15.1` and
`@n8n/n8n-nodes-langchain@2.48.3`.

---

## 2. Quick start

### Import an automation into n8n

In n8n: **Workflows → ⋯ → Import from File** → pick a file from `automations/` → attach a
credential to each flagged node. No workflow here contains secrets; credentials are always
yours to attach.

### Ask the knowledge base a question

```bash
# which node can append a row to a sheet?
grep -i "append row" knowledge-base/indexes/operations.jsonl

# ranked search, no dependencies
python3 tools/search.py "send whatsapp message"
python3 tools/search.py "append row" --ops
python3 tools/search.py "new email" --trigger
```

### Give an agent the same knowledge over MCP

```bash
python3 server/mcp_server.py        # stdio JSON-RPC
python3 server/test_server.py       # 24 checks
```

Point Claude Desktop, Cursor, VS Code or an n8n **MCP Client Tool** node at
`server/mcp_server.py`. Config snippets: [`server/README.md`](server/README.md).

### Check your work before committing

```bash
python3 tools/validate_repo.py      # workflows + registry
python3 tools/security_scan.py      # secrets, dangerous nodes, PII, package provenance
```

---

## 3. Repository layout

```
n8n-automation-hub/
├── README.md                     ← you are here
├── LICENSE                       MIT for this repository's own code and docs
├── NOTICE.md                     third-party attribution and licence map
├── CONTRIBUTING.md               how to add an automation, node or source
├── SECURITY.md                   secret handling, import safety, reporting
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── pyproject.toml                installs the MCP server as `n8n-hub-mcp`
├── automations/
│   ├── README.md                 conventions for workflow JSON
│   ├── registry.json             generated index of every workflow
│   ├── _template/                starting point for a new automation
│   ├── ai/                       AI agent, RAG and LLM workflows
│   ├── integrations/<app>/       app-specific examples
│   ├── core/<node>/              core-node examples
│   └── patterns/                 general patterns
├── knowledge-base/
│   ├── README.md                 KB reference and field-level schema
│   ├── AGENT-GUIDE.md            KB → workflow JSON walkthrough
│   ├── catalog.json              all 531 nodes, one compact entry each
│   ├── manifest.json             build metadata and counts
│   ├── schema.json               JSON Schema for a node record
│   ├── nodes/<category>/         one .json + one .md per node
│   ├── credentials/              one .json + one .md per credential type
│   ├── indexes/                  operations, nodes, keywords, triggers, enums
│   └── examples/                 the 12 bundled workflows + index
├── server/
│   ├── README.md                 tools, resources, client configuration
│   ├── mcp_server.py             protocol layer (stdio JSON-RPC 2.0)
│   ├── kb.py                     data layer: search and lookups
│   └── test_server.py            24 protocol and tool assertions
├── community-nodes/
│   ├── README.md                 what community nodes are, how to install them safely
│   ├── index.json                1,500 npm packages tagged n8n-community-node-package
│   ├── top-100.json              100 packages ranked by monthly downloads
│   └── shortlist.json            approved packages, machine-checked
├── sources/
│   ├── README.md                 how to evaluate and record a source
│   └── sources.json              12-source registry with tiers and licences
├── security/
│   └── waivers.json              accepted risks, with reasons and expiry dates
├── docs/
│   ├── architecture.md           how the pieces fit together
│   ├── workflow-conventions.md   naming, structure and versioning rules
│   ├── importing.md              import, credential and activation checklist
│   ├── research-2026-11.md       the research behind this repository
│   └── roadmap.md                what gets added next
├── tools/
│   ├── validate_repo.py          workflow lint + registry generation
│   ├── security_scan.py          secrets, dangerous nodes, PII, package provenance
│   ├── build_kb.py               rebuild the KB from an n8n-docs clone
│   ├── enrich_kb.py              add exact parameter schemas from the npm packages
│   ├── build_community_index.py  rebuild community-nodes/index.json from npm
│   ├── build_top_nodes.py        rank community nodes by monthly downloads
│   └── search.py                 BM25 search CLI
└── .github/
    ├── workflows/validate.yml    CI: workflows, security scan, MCP server tests
    ├── ISSUE_TEMPLATE/           bug / new automation / new source
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 4. The knowledge base

`knowledge-base/` answers the question an agent actually asks: *"which node does X, and what
do I put in its parameters?"* It is deliberately split into many small files so a search hits
a 5 KB record instead of a 17 MB dump.

### Layers

| Layer | Source | Strength |
|---|---|---|
| Prose, operations, credentials, common issues | docs.n8n.io (docs repository snapshot) | Intent — what the node is for |
| Exact parameter names, types, defaults, option values, `typeVersion` | `n8n-nodes-base`, `@n8n/n8n-nodes-langchain` | Precision — what the JSON accepts |

Where the two disagree, the package wins for generating JSON and the docs win for choosing the
node.

### Record shape

```json
{
  "id": "n8n-nodes-base.gmail",
  "name": "Gmail",
  "category": "app-node",
  "workflow_type": "n8n-nodes-base.gmail",
  "type_version": 2.2,
  "is_trigger": false,
  "is_ai_tool": true,
  "credential_types": ["googleApi", "gmailOAuth2"],
  "operations": [
    {"resource": "Message", "operation": "Send",
     "resource_value": "message", "operation_value": "send",
     "parameters": [{"name": "To", "description": "..."}]}
  ],
  "node_schema": {"parameters": [{"name": "resource", "type": "options",
                                  "options": [{"name": "Message", "value": "message"}]}]},
  "common_issues": [{"title": "401 unauthorized error", "summary": "..."}]
}
```

Full field reference: `knowledge-base/README.md`. Building rules: `knowledge-base/AGENT-GUIDE.md`.

### Indexes

| File | Contents |
|---|---|
| `indexes/operations.jsonl` | 3,848 lines, one per operation — the fastest "which node does X" lookup |
| `indexes/resources-operations.json` | Internal `resource` / `operation` / `authentication` values for 521 nodes |
| `indexes/nodes.jsonl` | One line per node: id, type, typeVersion, operations, description |
| `indexes/keywords.json` | 2,604 keywords mapped to node ids |
| `indexes/triggers.json` | All 91 trigger nodes |
| `indexes/ai-tools.json` | Every node usable as an AI Agent tool |
| `indexes/credentials.json` | 322 credential types with auth methods |

### Known gaps

Ten documented nodes are not present in the pinned package versions and carry docs only
(`confluence`, `kitemaker`, `microsoftdataverse`, `microsoftexcelsharepoint`,
`databrickstrigger`, `microsoftsharepointtrigger`, `activationtrigger`, `messageanagent`,
`n8n-mcp-registry.databricksgenie`, `n8n-nodes-langchain.embeddingsgooglepalm`). Community
nodes are intentionally **not** merged into the node records — they change too fast and are
tracked separately in `community-nodes/`.

---

## 5. Automations

Every file under `automations/` is a complete, importable n8n workflow.

### Conventions

- **One workflow per file**, named in kebab-case after what it does, not after the node it uses.
- **No secrets, ever.** No API keys, tokens, passwords, instance ids or personal emails in
  `parameters`. Credentials are named in documentation, never embedded.
- **`type` must be a real node type** (`workflow_type` in the knowledge base), and
  `typeVersion` must be present.
- **Node names are unique** and describe the step ("Fetch invoices", not "HTTP Request1").
- **Positions** laid out left to right; AI sub-nodes placed below their agent.
- **Sticky notes** carry intent and the credential checklist for anything non-obvious.

`automations/registry.json` is generated by `tools/validate_repo.py` and records, per
workflow: node count, node types used, trigger type, knowledge-base records it depends on,
community nodes it requires, and a content hash.

### Starting a new automation

```bash
cp -r automations/_template automations/integrations/my-service
# edit automations/integrations/my-service/workflow.json
python3 tools/validate_repo.py
python3 tools/security_scan.py
```

---

## 6. Community nodes

`community-nodes/index.json` is built from the npm registry using the exact keyword n8n
itself searches — `n8n-community-node-package` — so it mirrors what **Settings → Community
Nodes → Browse** shows. npm reports **14,543** packages carrying that keyword; this index
captures the top **1,500** by search rank and enriches **401** with last-month downloads.

`community-nodes/top-100.json` is the popularity view: the hundred packages with the highest
30-day downloads, ranked by `tools/build_top_nodes.py` from npm data. It is computed here, not
quoted from a third-party list, and it is cross-checked against two independent directories —
both recorded in `sources/sources.json`. A high rank means many installs, not a security review.

`community-nodes/shortlist.json` is the approved list, and it is machine-checked: every entry
must pin an exact version, declare a licence and a source repository, be old enough to have a
track record, and not sit two edits away from a far more popular package. Details in
[`community-nodes/README.md`](community-nodes/README.md).

Read this before installing anything:

- **Community nodes are unverified third-party code.** n8n's own documentation states they have
  full access to the machine n8n runs on and to the data flowing through your workflows.
- **"Verified" is an n8n-side badge**, shown with a shield icon in the node panel. A package
  scoped `@n8n/*` is not the same as being verified.
- **Pin versions.** A minor upgrade can carry a breaking change that silently breaks every
  workflow using the node.
- **Self-hosted controls:** `N8N_COMMUNITY_PACKAGES_ENABLED`,
  `N8N_VERIFIED_PACKAGES_ENABLED`, `N8N_UNVERIFIED_PACKAGES_ENABLED` and `NODES_EXCLUDE` let
  you narrow what an instance will load.

---

## 7. MCP server

`server/` exposes the knowledge base over the Model Context Protocol, so an agent can look up
nodes and validate its own output instead of guessing.

| Tool | Answers |
|---|---|
| `search_operations` | "which node appends a row to a sheet?" — with the internal values JSON needs |
| `search_nodes` | Discovery without pinning an operation |
| `get_node` | One record: summary, or `operations` / `schema` / `params` / `events` / `issues` / `examples` |
| `get_operation` | One operation's parameters and options |
| `list_triggers` | How a workflow can start |
| `search_community_nodes` | Third-party packages for an app, with download counts and rank |
| `resolve_enum` | "Append Row" → `append` |
| `validate_workflow` | Runs the same lint as CI on JSON the agent just produced |

Resources: `n8n://guide/agent`, `n8n://guide/knowledge-base`,
`n8n://guide/workflow-conventions`, `n8n://guide/security`, and the template
`n8n://node/{id}`.

```bash
python3 server/mcp_server.py     # stdio, no dependencies
pip install -e .                 # or install it as `n8n-hub-mcp`
```

Client configuration for Claude Desktop, Cursor, VS Code and n8n's **MCP Client Tool** node is
in [`server/README.md`](server/README.md). The server is read-only, stdio-only and capped at
60 000 characters per tool result.

---

## 8. Sources and provenance

`sources/sources.json` is the single place that records where material comes from, what its
licence is, and how far to trust it. Three tiers:

| Tier | Meaning | Examples in the registry |
|---|---|---|
| `official` | Published by n8n | docs.n8n.io, n8n.io/workflows, the npm node packages |
| `community-curated` | Maintained by identifiable people, licence stated | `enescingoz/awesome-n8n-templates` (CC BY 4.0), `felipfr/awesome-n8n-workflows` (MIT) |
| `aggregator` | Bulk scrapes; provenance of individual workflows is unclear | `Zie619/n8n-workflows`, `ScraperNode/awesome-n8n-templates` |

Research findings that shaped this repository — including a documented quality problem in the
largest aggregator — are written up in `docs/research-2026-11.md`.

**Rule:** a workflow enters `automations/` only after it has been read, validated, scanned,
stripped of secrets, and attributed. Bulk imports are not accepted; provenance beats volume.

---

## 9. Tooling

Python 3.12 standard library only — no `pip install` needed to run any of it.

| Command | What it does |
|---|---|
| `python3 tools/validate_repo.py` | Validates workflow JSON, checks node types against the KB, regenerates `automations/registry.json` |
| `python3 tools/security_scan.py` | Secrets, dangerous nodes, dangerous code, SSRF targets, disabled TLS, PII, and community-package provenance |
| `python3 tools/search.py "<query>"` | BM25 search over nodes (`--ops`, `--trigger`, `--ai-tool`, `--category`, `--json`) |
| `python3 tools/build_kb.py --docs-repo <clone>` | Rebuilds `knowledge-base/` from an n8n-docs clone |
| `python3 tools/enrich_kb.py --kb <dir>` | Re-applies exact parameter schemas from the npm packages |
| `python3 tools/build_community_index.py` | Rebuilds `community-nodes/index.json` from npm |
| `python3 tools/build_top_nodes.py` | Ranks community nodes by monthly downloads into `community-nodes/top-100.json` |
| `python3 server/test_server.py` | Drives the MCP server over stdio and asserts 24 behaviours |

Refreshing the knowledge base is two steps because the two sources are versioned separately:

```bash
git clone --depth 1 https://github.com/n8n-io/n8n-docs.git vendor/n8n-docs
npm pack n8n-nodes-base @n8n/n8n-nodes-langchain
tar -xzf n8n-nodes-base-*.tgz --wildcards 'package/dist/types/nodes.json'
mv package/dist/types/nodes.json vendor/n8n-nodes-base.nodes.json
# repeat for the langchain package, then:
python3 tools/build_kb.py
python3 tools/enrich_kb.py
```

---

## 10. Security model

Three layers, all enforced in CI.

**Layer 1 — never commit a secret.** Workflows are exported with credential references
stripped; you attach credentials in your own instance. `tools/validate_repo.py` rejects
secret-shaped parameter fields, and `tools/security_scan.py` looks for the patterns a real
key actually has: `sk-`, `sk-ant-`, `ghp_`, `xoxb-`, `AKIA`, `AIza`, `ya29.`, JWTs, PEM private
keys, Stripe live keys, and Slack or Discord webhook URLs with live tokens.

**Layer 2 — flag the nodes that can hurt you.** The scanner reports `executeCommand`, `ssh`,
`readWriteFile`, `localFileTrigger`, Code nodes that touch `child_process`, `eval`,
`new Function` or `process.env`, HTTP Request nodes aimed at cloud metadata or loopback
addresses, disabled TLS verification, unauthenticated webhooks, embedded emails, and any
third-party node that is not on the shortlist.

**Layer 3 — check the packages themselves.** Every entry in `community-nodes/shortlist.json`
is verified against npm: exact version pin, declared licence, declared source repository,
publication age, last-modified date, and Levenshtein distance to the most-downloaded packages
to catch typosquats.

```bash
python3 tools/security_scan.py                 # whole repository
python3 tools/security_scan.py --changed       # only what this branch adds (CI, PRs)
python3 tools/security_scan.py --json          # machine readable
python3 tools/security_scan.py --fail-on low   # stricter gate
```

Accepted risks are written down in `security/waivers.json` with a reason, an owner and an
expiry date. An expired waiver stops working, so an exception cannot quietly become permanent.
Full detail, including the import checklist for untrusted workflows: [`SECURITY.md`](SECURITY.md).

---

## 11. Working conventions

- **Branch per change**, conventional-commit messages (`feat(automations): add …`,
  `chore(kb): refresh to n8n-nodes-base@2.x`).
- **`main` stays importable.** CI rejects a workflow that fails validation or the security scan.
- **Refresh cadence:** knowledge base monthly, community index monthly, automations as they are
  built. Every refresh updates `CHANGELOG.md` and the snapshot dates in `manifest.json` and
  `sources.json`.
- **Every generated file says it is generated** in its header or metadata block. Do not
  hand-edit `catalog.json`, `manifest.json`, `indexes/*`, `registry.json` or
  `community-nodes/index.json`.

---

## 12. Licensing

This repository mixes three kinds of material, so the licence is layered — see `NOTICE.md` for
the full map.

| Material | Licence |
|---|---|
| Scripts, documentation, MCP server and workflow JSON authored here | MIT (`LICENSE`) |
| Knowledge base content derived from docs.n8n.io | n8n Sustainable Use License v1.0 |
| Workflow JSON originating from the n8n docs repository | n8n Sustainable Use License v1.0 |
| Community node metadata | npm registry metadata, per-package licences |
| Third-party workflow collections | per-source, recorded in `sources/sources.json` |

What the Sustainable Use License means for a public repository: use and modification for
personal or internal business purposes is granted, and redistribution is allowed **only free of
charge and non-commercially**, with n8n's notices intact. This repository is published free and
non-commercially on that basis. If it ever acquires a commercial purpose, the n8n-derived
material (`knowledge-base/`, the docs-sourced workflows) needs a separate agreement — talk to
license@n8n.io before that happens, not after.

---

## 13. Roadmap

Near term, in `docs/roadmap.md`:

1. A production reference workflow with retries, an error workflow and failure notification.
2. Error-handling pattern as a reusable template.
3. Curated community node shortlist — three to five packages, read before approval.
4. Expression examples in the knowledge base, from the packages' `codex` hints.
5. A static search page over the indexes, for reading without Python.

---

## 14. Contributing

Read `CONTRIBUTING.md`. In short: one workflow or one source per pull request, validation and
the security scan green, provenance recorded, no secrets, and a short "what it does / what it
needs" note in the automation's README.
