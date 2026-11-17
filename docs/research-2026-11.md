# Research log — November 2026

What was surveyed before this repository was structured, what was verified first-hand, what
came from secondary sources, and which decisions followed. Written so a future reader can see
*why* the repository looks like this, not just what it contains.

Method: the n8n documentation repository was cloned and parsed directly; the two node packages
were downloaded from npm and their `dist/types/nodes.json` inspected; the npm registry API was
queried for the community node keyword; the wider ecosystem was surveyed through published
collections and their READMEs.

---

## 1. What was measured directly

These numbers come from files in hand, not from anyone's README.

| Measurement | Value | How |
|---|---|---|
| Markdown pages under `docs/integrations/builtin` | 951 | `find` on a fresh `n8n-io/n8n-docs` clone |
| Built-in nodes documented | 531 | 275 app, 91 trigger, 69 core, 24 AI cluster root, 72 AI cluster sub |
| Credential types documented | 322 | `docs/integrations/builtin/credentials` |
| Operations parsed from docs | 3,848 | structured extraction from the `## Operations` sections |
| Nodes matched to a package schema | 521 / 531 | normalised name match against `dist/types/nodes.json` |
| `n8n-nodes-base` version | 2.15.1 | `registry.npmjs.org/n8n-nodes-base/latest` |
| `@n8n/n8n-nodes-langchain` version | 2.48.3 | same method |
| Workflow JSON bundled with the docs | 12 | `docs/_workflows/**/*.json` |
| npm packages tagged `n8n-community-node-package` | 14,543 | `registry.npmjs.org/-/v1/search?text=keywords:n8n-community-node-package` |
| Community packages captured in the index | 1,500 | first six pages of that search, exact-keyword filtered |
| Of those, with monthly download counts | 329 | `api.npmjs.org/downloads/point/last-month` |

Two caveats worth writing down: the npm keyword match count of 14,543 is far higher than the
number of community nodes a person would recognise — the keyword is open to anyone, so forks,
experiments and abandoned packages all count. And 329 download lookups were performed because
the bulk endpoint rejects scoped packages, so scoped names are queried one at a time.

---

## 2. Official sources

### Documentation — `docs.n8n.io`

Authoritative for intent: what a node is for, which operations it exposes, which credential it
needs, what commonly goes wrong. Weak on precision: app-node pages list operations but rarely
every parameter, and the parameter labels are display strings, not the values the JSON needs.

Notable structural detail: the docs are published from a GitBook-backed repository
(`n8n-io/n8n-docs`) where every page carries frontmatter with its canonical URL. Reusable
snippets appear as unresolved `{% include %}` blocks with an ID; a repository-level index
(`REUSABLE_CONTENT_INDEX.md`) maps those IDs to names, which is how this repository can tell
that a page carries the "AI tool" note.

Source: <https://docs.n8n.io/integrations/builtin/>

### Node packages — `n8n-nodes-base`, `@n8n/n8n-nodes-langchain`

The precise source. `dist/types/nodes.json` in each package holds the full node description:
`properties[]` with parameter names, types, defaults, `options[]` carrying both the display
name and the internal value, `displayOptions` controlling visibility, `version` (a number or an
array of accepted versions), and `credentials[]` with internal credential names.

This is what makes `resources-operations.json` possible — the mapping from "Append Row" to
`append`, which is the difference between a workflow that imports and one that fails.

Sources: <https://registry.npmjs.org/n8n-nodes-base> ·
<https://registry.npmjs.org/@n8n/n8n-nodes-langchain>

### Template library — `n8n.io/workflows`

n8n's own gallery, and the same library the Templates button inside n8n opens. A secondary
survey counted roughly 13,778 templates listed on 28 October 2026, each with a named creator
and a last-updated date. The public API (`api.n8n.io`) was not reachable from this build
environment, so templates are referenced by URL rather than mirrored.

Source: <https://n8n.io/workflows/> · secondary count: <https://urielpapa.com/blog/free-n8n-workflow-templates-github>

### Community nodes — the npm keyword

n8n's own installation flow browses npm by the keyword `n8n-community-node-package`, so that
keyword is the definition of a community node in practice. n8n also runs a **verified**
programme: a subset of packages is inspected and surfaced in the node panel with a shield icon,
installable from the canvas including on Cloud. The programme started in May 2025 with roughly
25 nodes, chosen partly because they were MIT-licensed and dependency-free.

Sources: <https://docs.n8n.io/integrations/community-nodes/installation-and-management/gui-installation> ·
<https://blog.n8n.io/community-nodes-available-on-n8n-cloud/>

### Risk model for community nodes

n8n's documentation is explicit, and the repository repeats it verbatim in spirit: community
nodes are unverified code from a public source, they have full access to the machine n8n runs
on, they can see workflow data, and they may introduce breaking changes between versions.
n8n maintains a blocklist, and self-hosted instances can disable community packages entirely
or restrict them to verified ones.

Sources: <https://docs.n8n.io/integrations/community-nodes/risks> ·
<https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/use-environment-variables/nodes>

### Licensing — the Sustainable Use License

n8n is source-available under the Sustainable Use License v1.0, not OSI open source. The
grant: use, modify and prepare derivative works for **internal business purposes or personal,
non-commercial use**. Distribution is permitted **only free of charge and non-commercially**,
and notices may not be altered or removed. Consulting and building workflows for clients is
explicitly allowed; letting people outside your organisation build or configure their own
workflows on your instance requires a commercial licence.

That is why this repository is private, and why `NOTICE.md` splits the licence map by
directory instead of putting one LICENSE over everything.

Sources: <https://docs.n8n.io/n8n-community-license> ·
<https://github.com/n8n-io/n8n/blob/master/LICENSE.md> · <https://spdx.org/licenses/SUL-1.0.html>

---

## 3. Community and unofficial sources

Surveyed, recorded in `sources/sources.json`, and used for landscape research only.

| Source | Size claimed | Licence | Assessment |
|---|---|---|---|
| `enescingoz/awesome-n8n-templates` | ~280 templates, 18 categories | CC BY 4.0 per its LICENSE (GitHub reports NOASSERTION) | The most cited collection. Discloses affiliate links; states no template is its own work, so per-file attribution does not exist |
| `Zie619/n8n-workflows` | 4,343 claimed; 2,061 JSON files counted in the `workflows` folder on 28 Oct 2026 | MIT (collection) | Largest, with a search UI — and the biggest quality problem, below |
| `ScraperNode/awesome-n8n-templates` | 8,697 → 13,593 in different README revisions | MIT (collection) | Volume without verification or per-file attribution |
| `felipfr/awesome-n8n-workflows` | curated set by function | MIT | Clear licence, explicit "gathered from the internet, credit to authors" note |
| `nusquama/n8nworkflows.xyz` | catalogue with a web UI | not stated | No licence ⇒ nothing may be copied from it |
| `7and1/n8n-Library` | ~2,348 templates, regenerated | not stated | No licence, no per-file provenance, contents change in bulk |

### The finding that shaped the import policy

An independent audit of `Zie619/n8n-workflows`, published 28 October 2026, reported that a
large share of the JSON files replace AI nodes — `lmChatOpenAi`, `agent`, `chainLlm` — with
`n8n-nodes-base.noOp`. The reported figures: 767 of 2,061 files contain `noOp` nodes, and in
756 of them the notes say those were originally AI nodes; only one file in the folder
contained a real AI node.

The practical consequence: a workflow from that collection imports cleanly, shows a tidy
canvas, and silently skips the model call. Nothing errors. That is the worst failure mode an
automation can have, and it is exactly why this repository refuses bulk imports.

Source: <https://urielpapa.com/blog/free-n8n-workflow-templates-github>

### Sources added after the first survey

Two more were evaluated later in the month and added to the registry.

**`restyler/awesome-n8n`** — a single README ranking ~100 community nodes by npm monthly
downloads, in eight categories, with a crawler-statistics table that tracks the ecosystem from
1,075 packages in February 2025 to 5,834 in January 2026. Useful as a second opinion on which
packages lead. Three problems: no LICENSE file, so nothing may be copied; affiliate and sponsor
links throughout; and an author column that credits "GitHub Actions" for several packages whose
npm author field is a CI bot. Conclusion: cross-check only, and compute our own ranking instead.

**`ncnodes.com`** — a directory of community nodes that does two things npm metadata cannot:
it separates 30-day from all-time downloads, and it marks packages that declare themselves
AI-generated. Its API host is not reachable from this build environment and no licence is
stated, so it is cited as a reference rather than ingested. Package facts were verified against
npm directly.

Both are now listed in `sources/sources.json` with those notes, and both were used to sanity
check `community-nodes/top-100.json` — the leaders agree with our npm-derived ranking.

---

## 4. Decisions

| Decision | Reason |
|---|---|
| Two-layer knowledge base (docs + packages) | Docs give intent, packages give precision; neither alone produces valid JSON |
| Split into per-node files rather than one corpus | Retrieval cost, grep-ability, diffability |
| Community nodes indexed, not merged | They change weekly and are unverified; merging would make `node_schema` a moving target |
| No bulk imports into `automations/` | The placeholder finding above: volume without verification is a liability |
| Provenance registry with tiers | Licence and quality questions must be answerable per file, months later |
| Private repository, layered licence | The Sustainable Use License permits personal/internal use and non-commercial distribution only |
| Stdlib-only tooling | Nothing to install, nothing to rot; runs on any machine with Python 3 |
| CI validates and fails on stale registry | The one file that silently rots in repositories like this is the index |

---

## 5. Gaps and open questions

- **Ten documented nodes have no package schema** in the pinned versions. Either they were
  removed, renamed, or live in a package this build did not fetch. Recorded as
  `node_schema: null` rather than guessed.
- **The n8n templates API was unreachable** from the build environment, so the official gallery
  is a link, not a local index. If the API becomes reachable, a `templates/` index would be the
  natural next addition.
- **No verified-community-node flag** exists in npm metadata. Verification is an n8n-side
  state, visible only in the node panel, so the index cannot carry it honestly. The
  `official_scope` flag means only that the package name starts with `@n8n/`.
- **`typeVersion` drift** is unsolved by design: the snapshot records what was current on
  2026-11-17. Anything older or newer needs a re-run of the enrichment step.
- **Expression coverage** is thin. The docs explain expressions in prose; the packages expose
  `codex` hints that could seed per-node examples. Not yet extracted — see `roadmap.md`.
