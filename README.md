# n8n Automation Hub

A private, version-controlled home for n8n work: **ready-to-import automations**, a
**machine-readable knowledge base of every built-in node**, an **indexed registry of
community nodes**, and the **provenance record** for every source that feeds them.

The repository is built for two readers at once:

- **You, in the n8n editor** — import a workflow, wire up a credential, ship it.
- **An AI agent, headless** — search 3,848 operations, read exact parameter schemas, and
  emit workflow JSON that imports without hand-fixing.

---

## Table of contents

1. [What is in this repository](#1-what-is-in-this-repository)
2. [Quick start](#2-quick-start)
3. [Repository layout](#3-repository-layout)
4. [The knowledge base](#4-the-knowledge-base)
5. [Automations](#5-automations)
6. [Community nodes](#6-community-nodes)
7. [Sources and provenance](#7-sources-and-provenance)
8. [Tooling](#8-tooling)
9. [Working conventions](#9-working-conventions)
10. [Security and secrets](#10-security-and-secrets)
11. [Licensing](#11-licensing)
12. [Roadmap](#12-roadmap)
13. [Contributing](#13-contributing)

---

## 1. What is in this repository

| Area | Path | What it holds | Scale |
|---|---|---|---|
| Knowledge base | `knowledge-base/` | Every n8n built-in node as JSON + Markdown, with operations, parameter schemas, credentials and search indexes | 531 nodes · 3,848 operations · 322 credentials |
| Automations | `automations/` | Importable workflow JSON, grouped by AI / integrations / core / patterns | 12 seed workflows |
| Community nodes | `community-nodes/` | npm registry index of community node packages, ranked by real download counts | 1,500 packages indexed |
| Sources | `sources/` | Registry of official and unofficial sources, with licences, quality notes and check dates | 12 sources |
| Tooling | `tools/` | Builders, validators and a BM25 search CLI (stdlib only) | 5 scripts |
| Documentation | `docs/` | Architecture, workflow conventions, importing guide, research notes, roadmap | 5 documents |

Snapshot date: **2026-11-17**. Node schemas come from `n8n-nodes-base@2.15.1` and
`@n8n/n8n-nodes-langchain@2.48.3`.

---

## 2. Quick start

### Import an automation into n8n

```bash
# pick a workflow from automations/
cat automations/ai/let_your_ai_call_an_api.json
```

In n8n: **Workflows → ⋯ → Import from File** → choose the JSON → open each node and attach
a credential. No workflow in this repository contains secrets; credentials are always
attached by you, in your own instance.

### Ask the knowledge base a question

```bash
# which node can append a row to a sheet?
grep -i "append row" knowledge-base/indexes/operations.jsonl

# ranked search, no dependencies
python3 knowledge-base/tools/search.py "send whatsapp message"
python3 knowledge-base/tools/search.py "append row" --ops
python3 knowledge-base/tools/search.py "new email" --trigger
```

### Find a community node

```bash
# top packages by monthly downloads
python3 - <<'PY'
import json
d = json.load(open("community-nodes/index.json"))
for p in d["packages"][:15]:
    print(f"{p.get('downloads_last_month') or 0:>9,}  {p['name']}")
PY
```

### Validate everything before committing

```bash
python3 tools/validate_repo.py          # workflows + indexes + registry refresh
```

---

## 3. Repository layout

```
n8n-automation-hub/
├── README.md                     ← you are here
├── LICENSE                       MIT for this repository's own code and docs
├── NOTICE.md                     third-party attribution and licence map
├── CONTRIBUTING.md               how to add an automation, node or source
├── SECURITY.md                   secret-handling and reporting policy
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── automations/
│   ├── README.md                 conventions for workflow JSON in this repo
│   ├── registry.json             generated index: every workflow, its nodes and trigger
│   ├── _template/                starting point for a new automation
│   ├── ai/                       AI agent, RAG and LLM workflows
│   ├── integrations/<app>/       app-specific examples
│   ├── core/<node>/              core-node examples
│   └── patterns/                 general patterns (quickstart, credential expressions)
├── knowledge-base/
│   ├── README.md                 KB reference and field-level schema
│   ├── AGENT-GUIDE.md            KB → workflow JSON walkthrough
│   ├── catalog.json              all 531 nodes, one compact entry each
│   ├── manifest.json             build metadata and counts
│   ├── schema.json               JSON Schema for a node record
│   ├── nodes/<category>/         one .json + one .md per node
│   ├── credentials/              one .json + one .md per credential type
│   ├── indexes/                  operations, nodes, keywords, triggers, ai-tools, enums
│   └── examples/                 the 12 bundled workflows + index
├── community-nodes/
│   ├── README.md                 what community nodes are and how to install them safely
│   └── index.json                1,500 npm packages tagged n8n-community-node-package
├── sources/
│   ├── README.md                 how to evaluate and record a new source
│   └── sources.json              machine-readable source registry
├── docs/
│   ├── architecture.md           how the pieces fit together
│   ├── workflow-conventions.md   naming, structure and versioning rules
│   ├── importing.md              import, credential and activation checklist
│   ├── research-2026-11.md       the research behind this repo, with findings
│   └── roadmap.md                what gets added next
├── tools/
│   ├── validate_repo.py          validates workflows + regenerates registry.json
│   ├── build_kb.py               rebuild the KB from an n8n-docs snapshot
│   ├── enrich_kb.py              add exact parameter schemas from the npm packages
│   ├── build_community_index.py  rebuild community-nodes/index.json from npm
│   └── search.py                 BM25 search CLI (mirrored into knowledge-base/tools)
└── .github/
    ├── workflows/validate.yml    CI: JSON validity, workflow lint, index freshness
    ├── ISSUE_TEMPLATE/           bug / new automation / new source
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 4. The knowledge base

`knowledge-base/` answers the question an agent actually asks: *"which node does X, and
what do I put in its parameters?"* It is deliberately split into many small files so that a
search hits a 5 KB record instead of a 17 MB dump.

### Layers

| Layer | Source | Strength |
|---|---|---|
| Prose, operations, credentials, common issues | docs.n8n.io (docs repository snapshot) | Intent — what the node is for |
| Exact parameter names, types, defaults, option values, `typeVersion` | `n8n-nodes-base`, `@n8n/n8n-nodes-langchain` | Precision — what the JSON accepts |

Where the two disagree, the package wins for generating JSON and the docs win for choosing
the node.

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
  `parameters`. Credentials are referenced by name in the documentation, never embedded.
- **`type` must be a real node type** (`workflow_type` in the knowledge base), and
  `typeVersion` must be present.
- **Node names are unique** and describe the step ("Fetch invoices", not "HTTP Request1").
- **Positions** laid out left to right; AI sub-nodes placed below their agent.
- **Sticky notes** carry the intent and the credential checklist for anything non-obvious.

`automations/registry.json` is generated by `tools/validate_repo.py` and records, for each
workflow: node count, node types used, trigger type, and the KB records it depends on. Add a
workflow and the registry updates on the next validation run.

### Starting a new automation

```bash
cp -r automations/_template automations/integrations/my-service
# edit automations/integrations/my-service/workflow.json
python3 tools/validate_repo.py
```

---

## 6. Community nodes

`community-nodes/index.json` is built from the npm registry using the exact keyword n8n
itself searches — `n8n-community-node-package` — so it mirrors what **Settings → Community
Nodes → Browse** shows. npm reports **14,543** packages carrying that keyword; this index
captures the top **1,500** by search rank and enriches **329** of them with last-month
download counts.

Read this before installing anything:

- **Community nodes are unverified third-party code.** n8n's own documentation states they
  have full access to the machine n8n runs on and to the data flowing through your
  workflows.
- **"Verified" is an n8n-side badge**, shown with a shield icon in the node panel. A package
  being scoped `@n8n/*` is not the same as being verified.
- **Pin versions.** A minor upgrade can carry a breaking change that silently breaks every
  workflow using the node.
- **Self-hosted controls:** `N8N_COMMUNITY_PACKAGES_ENABLED`,
  `N8N_VERIFIED_PACKAGES_ENABLED`, `N8N_UNVERIFIED_PACKAGES_ENABLED`, and `NODES_EXCLUDE`
  let you narrow what an instance will load.

Rebuild the index with `python3 tools/build_community_index.py --pages 6 --downloads 400`.

---

## 7. Sources and provenance

`sources/sources.json` is the single place that records where material comes from, what its
licence is, and how far to trust it. It separates three tiers:

| Tier | Meaning | Examples in the registry |
|---|---|---|
| `official` | Published by n8n | docs.n8n.io, n8n.io/workflows, the npm node packages |
| `community-curated` | Maintained by identifiable people, licence stated | `enescingoz/awesome-n8n-templates` (CC BY 4.0), `felipfr/awesome-n8n-workflows` (MIT) |
| `aggregator` | Bulk scrapes; provenance of individual workflows is unclear | `Zie619/n8n-workflows`, `ScraperNode/awesome-n8n-templates` |

Research findings that shaped this repository — including a documented quality problem in
the largest aggregator — are written up in `docs/research-2026-11.md`.

**Rule:** a workflow enters `automations/` only after it has been read, validated by
`tools/validate_repo.py`, stripped of secrets, and attributed in `sources/sources.json`.
Bulk imports are not accepted; provenance beats volume.

---

## 8. Tooling

All scripts are Python 3.12 standard library only — no `pip install`, no virtualenv.

| Command | What it does |
|---|---|
| `python3 tools/validate_repo.py` | Validates every workflow JSON, checks node types against the KB, scans for secret-shaped fields, regenerates `automations/registry.json` |
| `python3 knowledge-base/tools/search.py "<query>"` | BM25 search over nodes (`--ops`, `--trigger`, `--ai-tool`, `--category`, `--json`) |
| `python3 tools/build_kb.py` | Rebuilds `knowledge-base/` from a fresh `n8n-io/n8n-docs` clone |
| `python3 tools/enrich_kb.py` | Re-applies exact parameter schemas from the npm packages |
| `python3 tools/build_community_index.py` | Rebuilds `community-nodes/index.json` |

The KB build is two steps because the two sources are versioned independently:

```bash
git clone --depth 1 https://github.com/n8n-io/n8n-docs.git
npm pack n8n-nodes-base @n8n/n8n-nodes-langchain   # extract dist/types/nodes.json from each
python3 tools/build_kb.py
python3 tools/enrich_kb.py
```

---

## 9. Working conventions

- **Branch per change**, conventional-commit style messages (`feat(automations): add …`,
  `chore(kb): refresh to n8n-nodes-base@2.x`).
- **`main` stays importable.** CI rejects a workflow that fails validation.
- **Refresh cadence:** knowledge base monthly, community index monthly, automations as they
  are built. Every refresh updates `CHANGELOG.md` and the snapshot dates in `manifest.json`
  and `sources.json`.
- **Every generated file says it is generated** in its header or metadata block. Do not
  hand-edit `catalog.json`, `manifest.json`, `indexes/*` or `registry.json`.

---

## 10. Security and secrets

This repository is private, but private is not a secret store.

- Never commit a credential, token, API key, webhook URL with an embedded secret, or a
  personal email address inside workflow parameters.
- Before importing a workflow that a client or a third party sent you, read every node's
  parameters — especially `HTTP Request`, `Execute Command`, `Code` and `Read/Write File`.
- `tools/validate_repo.py` blocks the obvious cases (fields named `apiKey`, `token`,
  `password`, `secret`, and long high-entropy strings) but it is a net, not a guarantee.
- See `SECURITY.md` for reporting and for the instance-hardening checklist.

---

## 11. Licensing

This repository mixes three kinds of material, so the licence is layered — see `NOTICE.md`
for the full map.

| Material | Licence |
|---|---|
| Scripts, documentation and workflow JSON authored here | MIT (`LICENSE`) |
| Knowledge base content derived from docs.n8n.io | n8n Sustainable Use License v1.0 |
| Workflow JSON originating from the n8n docs repository | n8n Sustainable Use License v1.0 |
| Community node metadata | npm registry metadata, per-package licences |
| Third-party workflow collections | per-source, recorded in `sources/sources.json` |

What the Sustainable Use License means here: use and modification for personal or internal
business purposes is granted; redistribution is allowed only free of charge and
non-commercially; n8n's notices must stay intact. Keep this repository private unless you
have checked each layer against those terms.

---

## 12. Roadmap

Near term, in `docs/roadmap.md`:

1. Grow `automations/` with hand-built, validated workflows (error handling + logging pattern first).
2. Add a `workflows/` linter rule set: require an error workflow hook and a retry policy.
3. Community node shortlist — a curated, pinned set with security notes.
4. Knowledge base: add node-level `codex` hints and expression examples from the packages.
5. Optional: a static search page over the indexes for use without Python.

---

## 13. Contributing

Read `CONTRIBUTING.md`. In short: one workflow or one source per pull request, validation
green, provenance recorded, no secrets, and a short "what it does / what it needs" note in
the automation's README.
