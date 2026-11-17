# Roadmap

Ordered by what makes the repository more useful soonest. Each item states the acceptance test,
so "done" is not a matter of opinion.

---

## Now

### 1. A production reference workflow

The first workflow worth copying: schedule → API → transform → destination, with retries, an
error workflow, and a notification on failure.

**Done when:** it imports clean, runs green in a scratch instance, and `docs/workflow-conventions.md`
§5 is satisfied by the file itself rather than by a note.

### 2. Error-handling pattern as a template

A reusable sub-workflow that receives `$json.error` and posts a structured message (workflow,
node, message, execution URL) to one channel.

**Done when:** `automations/patterns/error-notifier.json` exists and two other workflows
reference it in `settings.errorWorkflow`.

### 3. Extend the validator

~~Security scanning~~ shipped in 1.1.0 as `tools/security_scan.py`. Remaining: a
required-sticky-note check for production workflows, a retry-policy check on network nodes, and
an `errorWorkflow` presence check.

**Done when:** the new rules fail a deliberately bad fixture and pass the existing corpus.

---

### 3a. MCP server — shipped in 1.1.0

`server/` now exposes seven tools over stdio. Follow-ups worth doing:

- ~~a `search_community_nodes` tool over `community-nodes/index.json`~~ shipped in 1.2.0
- a `diff_kb_versions` tool once item 8 exists
- an HTTP transport, only if a remote client actually needs one

## Next

### 4. Curated community node shortlist

Three to five packages, each read before approval, with pinned versions and a security note in
`community-nodes/README.md`.

**Done when:** the shortlist table has real rows and `automations/` contains at least one
workflow that uses each pinned package.

### 5. Expression examples in the knowledge base

Extract `codex` hints and `defaults` from the node packages into each record, so an agent can
see realistic parameter values instead of empty objects.

**Done when:** `node_schema.parameters[].codex` is populated where the package provides it, and
`knowledge-base/schema.json` documents the field.

### 6. Templates index — shipped in 1.3.0

`templates/index.json` exists with 9 entries and a status per entry (`validated`, `documented`,
`executed`), served by `search_templates` and `get_template`. The remaining part is blocked:
indexing the **official** n8n template gallery needs `api.n8n.io`, which is not reachable from
this build environment.

**Done when:** the official gallery is indexed alongside the local templates.

### 6a. Reference layer — shipped in 1.4.0

Expressions, environment variables, releases and breaking changes are parsed into
`knowledge-base/reference/` and served by `search_reference` / `get_reference`. Two of the four
files feed validation rather than documentation.

**Next:** a diff between two builds, so an upgrade can be read as "what changed" instead of
"read 609 release notes".

### 6b. MCP catalogue — shipped in 1.5.0

`mcp-servers/index.json` lists 4,978 external MCP servers with trust level and sources, served by
`search_mcp_servers` / `get_mcp_server`.

**Next:** transport and auth metadata for the top ~200 by downloads, read from each server's own
README, so the catalogue becomes configurable rather than just discoverable.

---

## Later

### 7. Static search page

A single self-contained HTML page over `knowledge-base/indexes/*` for reading on a phone
without Python.

### 8. Node-level changelog

Diff two knowledge base builds to produce "what changed in this n8n release" — useful before
upgrading an instance that runs 30 workflows.

### 9. Import dry-run harness

A container that boots n8n, imports every workflow in `automations/`, and reports nodes whose
`typeVersion` no longer exists.

### 10. Credential scope audit

For each credential type, record the minimum scopes the workflows in this repository actually
need, so a new credential can be created least-privilege by default.

---

## Not planned

- **Bulk import of third-party workflow collections.** The quality and licence problems are
  documented in `docs/research-2026-11.md`; volume is not the goal.
- **Merging community nodes into the node records.** They change too fast and are unverified.
- **Hosting a public mirror of the documentation.** The Sustainable Use License permits
  non-commercial distribution only; publishing it free and non-commercially, as this
  repository does, is within the licence.
