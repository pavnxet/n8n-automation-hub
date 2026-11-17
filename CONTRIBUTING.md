# Contributing

This is a public repository with one maintainer, written as if others will use it.
The rules below are what keep it usable a year from now.

---

## 1. What you can add

| Kind of change | Where it goes | Required |
|---|---|---|
| A new automation | `automations/<group>/` | Workflow JSON + a README note + registry refresh |
| A fix to an existing automation | same file | Note the reason in the commit body |
| A new source (official or unofficial) | `sources/sources.json` | Licence, quality notes, check date |
| A community node worth pinning | `community-nodes/README.md` shortlist | Downloads, licence, security note |
| A knowledge base refresh | `knowledge-base/` | Regenerated files only, never hand-edited |
| Tooling improvement | `tools/` | Stdlib only, no new dependencies |

---

## 2. Adding an automation

Step 1: copy the template.

```bash
cp -r automations/_template automations/integrations/my-service
```

Step 2: export the workflow from n8n (**Workflows → ⋯ → Download**) and replace
`workflow.json`. Do not hand-write UUIDs — export, don't invent.

Step 3: strip anything personal.

- No API keys, tokens, passwords, OAuth client secrets.
- No personal email addresses, phone numbers, sheet ids, folder ids or instance ids.
  Replace them with empty strings or obvious placeholders.
- No webhook URLs that contain a secret path segment.

Step 4: fill in the automation README — what it does, what triggers it, which credentials it
needs, and any assumption a reader must know.

Step 5: validate and scan.

```bash
python3 tools/validate_repo.py      # structure, node types, registry
python3 tools/security_scan.py      # secrets, dangerous nodes, PII
```

Both must be clean before a pull request. A `high` finding is a blocker, not a discussion.

If you touched the MCP server, run its suite too:

```bash
python3 server/test_server.py            # protocol and tool behaviour
python3 -m unittest discover -s tests    # unit, integration and regression tests
python3 tests/test_search_benchmark.py   # search accuracy and latency
```

Step 6: commit with a scoped message.

```
feat(automations): add Gmail-to-Sheets invoice logger
```

---

## 3. Workflow rules enforced by CI

A workflow fails validation when:

- the file is not valid JSON, or has no `nodes` / `connections`;
- two nodes share a `name` (connections are keyed by name, so duplicates silently merge);
- a node has no `type`, or a `type` that is neither a knowledge-base `workflow_type` nor a
  community node pattern (`n8n-nodes-*`, `@scope/n8n-nodes-*`);
- a node has no `typeVersion`;
- a parameter key looks like a secret (`apiKey`, `token`, `password`, `secret`, `clientSecret`,
  `privateKey`) and has a non-empty literal value;
- a string value looks like a live credential (long high-entropy string, `sk-…`, `ghp_…`,
  `xoxb-…`, a bearer token);
- a node sits at a duplicate `position`;
- `tools/security_scan.py` reports a `high` finding (real credential shape, `executeCommand`,
  `ssh`, `eval`/`child_process` in a Code node, unauthenticated webhook, typosquatted package).

The validator prints the exact path and reason for every failure.

---

## 3a. Adding a community node

A package is not approved by adding it to `community-nodes/README.md` alone. Add it to
`community-nodes/shortlist.json`:

```json
{
  "name": "n8n-nodes-example",
  "version": "1.4.2",
  "verified": false,
  "reviewed": "2026-11-17",
  "reviewed_by": "pavnxet",
  "why": "One sentence on what it adds and why nothing built-in covers it.",
  "source_reviewed": "read the package source on 2026-11-17; no network calls outside its stated API"
}
```

Then run `python3 tools/security_scan.py`. It checks the exact pin, the declared licence, the
declared repository, publication age, last-modified date, and Levenshtein distance against the
most-downloaded community packages. A typosquat or an unpinned version fails CI.

## 4. Adding a source

Add one entry to `sources/sources.json`:

```json
{
  "id": "example-source",
  "name": "Example n8n collection",
  "url": "https://github.com/owner/repo",
  "tier": "community-curated",
  "licence": "MIT",
  "what_it_is": "One sentence on what it actually contains.",
  "quality_notes": "What you verified. Call out placeholders, missing attribution, referral links.",
  "used_for": "landscape research",
  "last_checked": "2026-11-17"
}
```

Rules:

- `tier` is one of `official`, `community-curated`, `aggregator`.
- `quality_notes` must say what you actually checked, not what the README claims.
- Never copy files from an `aggregator` tier into `automations/`. Read, rewrite, attribute.

---

## 5. Refreshing the knowledge base

Never hand-edit generated files. Regenerate:

```bash
git clone --depth 1 https://github.com/n8n-io/n8n-docs.git /tmp/n8n-docs
npm pack n8n-nodes-base @n8n/n8n-nodes-langchain        # extract dist/types/nodes.json
python3 tools/build_kb.py
python3 tools/enrich_kb.py
```

Then update `CHANGELOG.md` with the new snapshot date and package versions.

---

## 6. Commit messages

```
<type>(<scope>): <imperative summary>

<why, in one or two sentences>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `security`.
Scopes: `automations`, `kb`, `community`, `sources`, `tools`, `ci`.

---

## 7. Pull requests

One concern per pull request. The template asks for: what changed, why, how it was verified,
and whether any secret-shaped value was removed. A pull request that adds a workflow without
running `tools/validate_repo.py` is not reviewed.
