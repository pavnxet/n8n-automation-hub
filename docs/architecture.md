# Architecture

How the pieces of this repository fit together, and why they are split the way they are.

---

## 1. The problem

An n8n workflow is JSON that references node types, node versions and internal parameter
values. Documentation explains nodes in prose, with human labels. The gap between the two is
where most broken workflows come from:

- the docs say *Resource: Sheet Within Document*, the JSON needs `"resource": "sheet"`;
- the docs page is `n8n-nodes-base.emailimap`, the JSON needs
  `n8n-nodes-base.emailReadImap`;
- the docs say *Append Row*, the JSON needs `"operation": "append"`.

So the repository keeps two layers of truth and merges them per node.

```
        docs.n8n.io (docs repo)                  npm packages
   prose · operations · credentials        parameter schema · enum values
   · common issues · examples              · typeVersion · credential names
              │                                        │
              ▼                                        ▼
        tools/build_kb.py                     tools/enrich_kb.py
              │                                        │
              └──────────────┬─────────────────────────┘
                             ▼
                     knowledge-base/
        nodes/<cat>/<id>.{json,md}   catalog.json   indexes/*
                             │
        ┌────────────────────┴─────────────────────┐
        ▼                                          ▼
  tools/validate_repo.py                    tools/search.py
  (lint automations, build registry)        (BM25 over the indexes)
        │                                          │
        │                                   server/mcp_server.py
        │                                   (same index, MCP tools)
        ▼                                          ▼
   automations/registry.json              any MCP client
        │
        ▼
  tools/security_scan.py  ──►  CI gate (fail on high)
  (secrets, dangerous nodes, packages)
```

---

## 2. Why the knowledge base is many small files

A single 17 MB JSON is useless to an agent: it blows a context window and every query costs
the same as reading everything. Splitting by node gives:

| Concern | Effect |
|---|---|
| Retrieval cost | A hit is one 5–40 KB record, not the whole corpus |
| Grep-ability | `grep -l "append row" knowledge-base/indexes/*.jsonl` is instant and needs no runtime |
| Diffability | A node change touches one file, so `git log` answers "when did this change" |
| Regeneration | Rebuilding rewrites only the parts that are generated |

The cost is file count — 1,735 files. That is acceptable because no human reads the tree
directly; they read `catalog.json` or search.

---

## 3. Layers and their guarantees

| Layer | Guarantee | Failure mode if wrong |
|---|---|---|
| `nodes/<id>.md` | Faithful rendering of the docs page | Prose is stale; the doc URL is always included so it can be re-checked |
| `nodes/<id>.json` → `operations[]` | Every documented operation, with internal values where known | An operation exists in the UI but not here |
| `nodes/<id>.json` → `node_schema` | Exact parameter keys, types, defaults, option values | Absent for 10 nodes and for all community nodes |
| `indexes/*` | Derived from the records above | Regenerate, never hand-edit |
| `reference/*.json` | Parsed from other n8n doc sections: expressions, env vars, releases, breaking changes | Regenerate with `tools/build_reference.py` |
| `automations/*.json` | Imports, has no secrets, node types exist | CI rejects it |
| `server/*` | Speaks MCP correctly; validator identical to CI's | `server/test_server.py` fails |
| `templates/*.json` | Importable and schema-valid | `tests/test_validator.py` fails |
| `security/waivers.json` | Every accepted risk has a reason, an owner and an expiry | An expired waiver stops applying |

---

## 4. Build pipeline

### Knowledge base (two steps, two independent sources)

```bash
git clone --depth 1 https://github.com/n8n-io/n8n-docs.git
npm pack n8n-nodes-base @n8n/n8n-nodes-langchain
python3 tools/build_kb.py      # docs  → records, catalog, indexes, examples
python3 tools/enrich_kb.py     # packages → node_schema, resources-operations.json
```

Step 1 is deterministic given the docs snapshot. Step 2 matches records to packages by
normalised node name, with an exact display-name fallback for renamed nodes — that fallback
is what resolves `emailimap` → `emailReadImap`. 521 of 531 records match; the remaining 10
are documented nodes absent from the pinned package versions and keep `node_schema: null`.

Both steps preserve hand-written files. They delete only the directories they generate
(`nodes/`, `credentials/`, `indexes/`, `examples/`) plus `catalog.json` and `manifest.json`,
so `README.md`, `AGENT-GUIDE.md` and `schema.json` survive a rebuild.

### Community nodes

```bash
python3 tools/build_community_index.py --pages 6 --downloads 400
```

Reads the npm search API for the exact keyword n8n uses, then enriches the top results with
last-month downloads. Scoped packages are fetched one at a time because the bulk downloads
endpoint rejects them.

### The MCP catalogue

`mcp-servers/index.json` answers "what can I attach to an MCP Client Tool node?". It merges three
sources by repository slug: the seven official reference servers, ~5,000 entries from the largest
curated community list, and npm packages carrying the `mcp-server` keyword. The last group is kept
in a separate array because the keyword is self-declared — `yahoo-finance2` carries it and is a
library, not a server — and search only includes those when explicitly asked.

### The reference layer

Node records cover "which node, which parameters". Four more documentation sections cover the
questions around them, and `tools/build_reference.py` parses each into JSON:

| File | Answers | Entries |
|---|---|---|
| `reference/expressions.json` | is `$fromAI()` real, what does `$jmespath()` take? | 243 |
| `reference/env-vars.json` | what does `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS` do? | 364 |
| `reference/releases.json` | which release introduced or fixed something? | 609 |
| `reference/breaking-changes.json` | did 3.0 remove the node I use? | 46 |

Two couplings make it useful rather than decorative: the expression validator checks unknown
`$globals` against `expressions.json`, so a new helper in a future release is recognised without
a code change; and the validator matches unknown node types against documented removals, so a
removed node fails with the version that removed it.

### Workflow intelligence

`planner.py` → `generator.py` → `validation.py` is one pipeline: the planner proposes steps from
real node knowledge, the generator emits JSON and calls the validator, and the validator is the
only thing that decides whether the result is valid. `analysis.py`, `debugger.py` and `audit.py`
read the same knowledge base and never invent a node type.

### Security gate

```bash
python3 tools/security_scan.py                # whole repository
python3 tools/security_scan.py --changed      # what a branch adds (CI on PRs)
```

Two scanners, two questions. `validate_repo.py` asks *is this a well-formed workflow?*;
`security_scan.py` asks *is this workflow safe to run, and did the author paste a key into it?*
They are separate so a structural warning never hides a credential.

### MCP server

```bash
python3 server/test_server.py     # protocol and tool assertions
pip install -e .                  # optional: `n8n-hub-mcp`
```

`server/kb.py` reuses the same BM25 scorer as `tools/search.py`, and
`server/mcp_server.py` imports `tools/validate_repo.py` for its `validate_workflow` tool. No
second implementation of either exists — that is deliberate, because two implementations
eventually disagree.

### Automations

```bash
python3 tools/validate_repo.py
```

Walks `automations/**/*.json`, validates each workflow, cross-checks node types against the
knowledge base, scans for secret-shaped values, and rewrites `automations/registry.json`.

---

## 5. Extension points

| You want to add | Touch this | Not this |
|---|---|---|
| A workflow | `automations/<group>/` | `registry.json` (generated) |
| A source | `sources/sources.json` | — |
| A pinned community node | `community-nodes/README.md` shortlist | `index.json` (generated) |
| A node missing from the docs | nothing — it is a docs gap; record it in `docs/roadmap.md` | hand-editing `nodes/` |
| A new index | `tools/build_kb.py` | writing it by hand |
| An MCP tool | `server/mcp_server.py` + a test in `server/test_server.py` | adding a tool without a test |
| A security rule | `tools/security_scan.py` + a row in the `SECURITY.md` table | silencing a finding by editing the file it flagged |

---

## 6. Design decisions worth remembering

**Docs are the source of intent, packages are the source of precision.** Neither alone is
enough: docs know what a node is *for*, packages know what it *accepts*.

**No community nodes in the node records.** They change weekly, are unverified, and would
make `node_schema` a moving target. They get their own index instead.

**No bulk imports.** A workflow enters `automations/` only after being read, validated,
scrubbed and attributed. This is the single rule that keeps the repository trustworthy.

**Generated files say so.** Every generated file carries a metadata block naming its source
and date, so a future reader knows what not to edit.
