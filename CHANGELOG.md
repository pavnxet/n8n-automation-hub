# Changelog

All notable changes to this repository. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.2.0] — 2026-11-17

Two more sources ingested into the provenance registry, a popularity ranking computed from
npm, and community nodes made searchable over MCP.

### Added — community nodes

- `community-nodes/top-100.json`: the hundred community packages with the highest last-30-day
  npm downloads, with version, author, repository and npm link per row. Ranked by
  `tools/build_top_nodes.py` from npm data — computed here, not quoted from a third-party list.
- `tools/build_top_nodes.py`: refreshes download counts, re-ranks, writes the file.
  `--offline` re-ranks on stored counts; `--candidates` / `--top` control depth.
- `search_community_nodes` MCP tool: name, description, downloads and top-100 rank for
  third-party packages, with an explicit warning that they are unverified. Tool count is now 8,
  protocol tests 24.

### Added — sources

- `awesome-n8n-restyler` (community-curated): a README ranking community nodes by npm
  downloads, plus a crawler history of ecosystem growth. No licence file, affiliate links, and
  an author column that miscredits CI bots — so it is used only as a cross-check.
- `ncnodes` (community-curated): a directory that separates 30-day from all-time downloads and
  flags AI-generated packages. No licence stated and its API is unreachable from the build
  environment, so it is cited, not ingested.
- Registry is now 14 sources.

### Changed

- `community-nodes/index.json` download coverage grew from 329 to 401 packages.
- Documentation updated across the root README, `community-nodes/README.md`,
  `server/README.md`, `docs/roadmap.md` and `sources/README.md`.

### Verified

- `server/test_server.py`: 24/24 checks, including three new community-search assertions.
- `tools/security_scan.py`: 13 workflows and 853 records, clean apart from the one waived
  documentation webhook.
- The top-100 ranking was cross-checked against both new sources; the leaders agree.

---

## [1.1.0] — 2026-11-17

The repository went public, gained an MCP server, and grew a security gate in CI.

### Added — MCP server (`server/`)

- `server/mcp_server.py`: Model Context Protocol server over stdio (newline-delimited
  JSON-RPC 2.0), standard library only, no runtime dependencies.
- Seven tools: `search_operations`, `search_nodes`, `get_node`, `get_operation`,
  `list_triggers`, `resolve_enum`, `validate_workflow`. The validator imports
  `tools/validate_repo.py` directly, so the agent's check and CI's check cannot diverge.
- Five resources: `n8n://guide/{agent,knowledge-base,workflow-conventions,security}` and the
  template `n8n://node/{id}`.
- Tool results capped at 60 000 characters so a greedy call cannot flood a context window.
- `server/kb.py`: shared BM25 data layer, the same scorer as `tools/search.py`.
- `server/test_server.py`: 20 protocol and tool assertions, run in CI.
- `pyproject.toml`: `pip install -e .` exposes the `n8n-hub-mcp` command.
- `server/README.md`: client configuration for Claude Desktop, Cursor, VS Code and n8n's MCP
  Client Tool node.

### Added — security scanning (`tools/security_scan.py`)

- Workflow rules: secret-shaped parameter fields (SEC001), real credential shapes — `sk-`,
  `sk-ant-`, `ghp_`, `github_pat_`, `xoxb-`, `AKIA`, `AIza`, `ya29.`, JWT, PEM, Stripe live
  keys (SEC002), live Slack and Discord webhook URLs (SEC003), dangerous nodes such as
  `executeCommand` and `ssh` (SEC004), dangerous Code-node APIs (SEC005), SSRF-shaped HTTP
  targets (SEC006), unauthenticated webhooks (SEC007), embedded emails (SEC008), disabled TLS
  verification (SEC009), high-entropy strings (SEC011), community nodes missing from the
  shortlist (SEC012).
- Record rule: credential shapes pasted into a knowledge-base record (SEC101).
- Package rules against npm: unpinned version (SEC202), typosquat distance (SEC203), missing
  repository or licence (SEC205), brand-new package (SEC206), unmaintained package (SEC207).
- `--changed --base <ref>` scans only what a branch adds, so pull requests get a fast,
  focused gate. `--json` and `--fail-on <severity>` for machine use and stricter gates.
- `security/waivers.json`: accepted risks with reason, owner and expiry. Expired waivers stop
  applying automatically.
- `community-nodes/shortlist.json`: approved packages as data, machine-checked, replacing the
  hand-maintained table.

### Added — CI

- Three jobs: `workflows` (structure, registry freshness, JSON integrity, search smoke test),
  `security` (full scan on push, changed-files scan on pull requests, findings in the job
  summary), `mcp-server` (protocol tests plus a packaging install check).

### Changed

- **Repository is now public.** The n8n-derived material is redistributed free and
  non-commercially with notices intact, which is what the Sustainable Use License permits;
  `NOTICE.md` and the README licensing section state the terms and the commercial-use boundary.
- `tools/` is the single home for scripts. The duplicate `knowledge-base/tools/` directory is
  gone; the knowledge base points at `../tools/`.
- `tools/build_kb.py` and `tools/enrich_kb.py` no longer hard-code absolute paths. Both take
  `--docs-repo` / `--out` / `--kb` / `--base-nodes` / `--langchain-nodes`, with
  `N8N_DOCS_REPO`, `N8N_KB_OUT`, `N8N_BASE_NODES_JSON` and `N8N_LC_NODES_JSON` as environment
  fallbacks, and fail with an actionable message when an input is missing.
- `tools/search.py` resolves `knowledge-base/indexes` correctly when run from the repository
  root (it previously assumed it sat inside the knowledge base).
- Documentation restructured: the README documents the MCP server, the security model and the
  public-licensing boundary; `SECURITY.md` carries the full rule table.

### Verified

- A fresh `build_kb.py` + `enrich_kb.py` run from the refactored scripts reproduces the
  committed catalog exactly: 531 nodes, identical `workflow_type` and `type_version` per node.
- `tools/security_scan.py` over the repository: 13 workflows and 853 records, one medium
  finding (a documentation webhook with no auth), waived explicitly with a reason and expiry.
- `server/test_server.py`: 20/20 checks pass.

### Known limitations

- 10 documented nodes have no package schema (`node_schema: null`): `confluence`,
  `kitemaker`, `microsoftdataverse`, `microsoftexcelSharePoint`, `databricksTrigger`,
  `microsoftSharePointTrigger`, `activationTrigger`, `messageAnAgent`,
  `n8n-mcp-registry.databricksGenie`, `embeddingsGooglePalm`.
- The MCP server is stdio-only, read-only, and does not index community nodes.
- Community nodes are indexed but not merged into node records.
- `typeVersion` values track the pinned package versions and drift with each n8n release.

---

## [1.0.0] — 2026-11-17

First version of the hub. Consolidated the standalone n8n node knowledge base into a
repository that also carries automations, a community node index and a source registry.

### Added — knowledge base

- 531 node records (275 app, 91 trigger, 69 core, 24 AI cluster root, 72 AI cluster sub),
  each as a structured `.json` and a cleaned `.md`.
- 3,848 parsed operations with documented parameters and options.
- 322 credential type records with authentication methods.
- Exact parameter schemas for 521 nodes, merged from `n8n-nodes-base@2.15.1` and
  `@n8n/n8n-nodes-langchain@2.48.3`: parameter names, types, defaults, option values,
  `displayOptions`, `typeVersion`, credential type names.
- Indexes: `operations.jsonl`, `nodes.jsonl`, `keywords.json` (2,604 keywords),
  `resources-operations.json` (internal enum values for 521 nodes), `triggers.json`,
  `ai-tools.json`, `by-category.json`, `credentials.json`.
- `schema.json` (JSON Schema for a node record) and `AGENT-GUIDE.md` (KB → workflow JSON).

### Added — automations

- 12 seed workflows from the n8n docs bundle, grouped as `ai/`, `integrations/`, `core/`
  and `patterns/`.
- `automations/registry.json`, generated by the validator.
- `automations/_template/` for new workflows.

### Added — community nodes

- `community-nodes/index.json`: 1,500 npm packages tagged `n8n-community-node-package`,
  ranked by last-month downloads where available (329 enriched). npm reports 14,543 total
  matches for the keyword.

### Added — sources

- `sources/sources.json`: 12 sources across `official`, `community-curated` and
  `aggregator` tiers, each with licence, quality notes and check date.
- `docs/research-2026-11.md`: findings, including the placeholder-node quality problem
  documented in the largest workflow aggregator.

### Added — tooling and CI

- `tools/validate_repo.py`: workflow lint, secret-shaped value scan, node-type check against
  the knowledge base, registry regeneration.
- `tools/build_kb.py`, `tools/enrich_kb.py`, `tools/build_community_index.py`,
  `tools/search.py` (BM25, stdlib only).
- GitHub Actions workflow running validation on push and pull request.
