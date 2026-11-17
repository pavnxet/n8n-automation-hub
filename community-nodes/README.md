# Community nodes

`index.json` is an index of n8n community node packages taken straight from the npm
registry, using the same keyword n8n's own **Settings → Community Nodes → Browse** searches:
`n8n-community-node-package`.

| Field | Value |
|---|---|
| Packages indexed (`index.json`) | 1,500 (top of npm search ranking) |
| npm matches for the keyword | 14,543 |
| Packages with download counts | 401 (last 30 days) |
| Ranked shortlist (`top-100.json`) | 100, by monthly downloads |
| Generated | 2026-11-17 |

---

## What a community node is

A community node is an npm package that adds nodes to n8n beyond the built-in set. On a
self-hosted instance the owner or an admin installs it from **Settings → Community Nodes**;
n8n then loads it like any other node.

Two classes exist:

- **Verified community nodes** — inspected by n8n, shown with a shield icon in the node
  panel, installable from the canvas (including on n8n Cloud).
- **Unverified community nodes** — everything else on npm. Installable on self-hosted
  instances only, after accepting the risk warning.

---

## Read this before installing

n8n's own documentation is blunt about the risks, and it is right to be:

- **System security.** A community node has full access to the machine n8n runs on. It can
  read files, run commands, and open network connections.
- **Data security.** It can see everything flowing through your workflows, including
  customer data.
- **Breaking changes.** A minor version bump can change parameter names and silently break
  every workflow that uses the node.

Practical rules for this repository:

1. Pin an exact version, never a dist-tag. `n8n-nodes-foo@1.4.2`, not `@latest` or `@beta`.
2. Prefer a verified node; if none exists, read the package source before installing.
3. Install once, then watch it: `N8N_COMMUNITY_PACKAGES_PREVENT_LOADING=true` lets you boot
   an instance that a bad node is blocking.
4. Keep the list small. Every package is permanent attack surface.
5. Record what you installed and why, in the shortlist below.

Self-hosted controls worth knowing:

| Variable | Effect |
|---|---|
| `N8N_COMMUNITY_PACKAGES_ENABLED` | Master switch — `false` disables verified and unverified packages |
| `N8N_VERIFIED_PACKAGES_ENABLED` | Hide verified community nodes from the panel |
| `N8N_UNVERIFIED_PACKAGES_ENABLED` | Block everything except verified nodes |
| `N8N_COMMUNITY_PACKAGES_PREVENT_LOADING` | Skip loading installed packages at startup (recovery) |
| `NODES_EXCLUDE` | Block specific node types entirely, e.g. `executeCommand` |

---

## Top 100 by downloads

`top-100.json` is the popularity view: the hundred community packages with the highest
last-30-day npm downloads, with version, author, repository link and npm link for each.

The ranking is computed here by `tools/build_top_nodes.py`, which reads the index, refreshes
counts from `api.npmjs.org`, and sorts. Counts, versions and descriptions come from npm, so the
file is ours to publish — no rows are copied from any third-party list.

```bash
python3 tools/build_top_nodes.py                 # refresh and re-rank
python3 tools/build_top_nodes.py --offline       # re-rank on stored counts, no network
jq -r '.packages[:20][] | "\(.rank). \(.name)  \(.downloads_last_month)"' community-nodes/top-100.json
```

Two independent directories were used as a cross-check on the ranking, and both are recorded in
`sources/sources.json`:

| Source | What it gave us | What we did not take |
|---|---|---|
| [restyler/awesome-n8n](https://github.com/restyler/awesome-n8n) | A second opinion on which packages lead, plus a crawler history of ecosystem growth | Any row or description — the repository has no licence file, and its author column miscredits CI bots as people |
| [ncnodes.com](https://ncnodes.com/packages) | A cleaner presentation: 30-day vs all-time downloads, and an "AI-generated" badge | Any data — no licence is stated and its API is unreachable from the build environment |

**Popularity is not trust.** The top of this list is dominated by WhatsApp and chat wrappers
with no security review. A high rank means many installs, nothing more — which is exactly why
the shortlist below exists.

## How to search the index

```bash
# top 20 by monthly downloads
python3 - <<'PY'
import json
d = json.load(open("community-nodes/index.json"))
for p in d["packages"][:20]:
    print(f"{p.get('downloads_last_month') or 0:>9,}  {p['name']:<45} {p['description'][:60]}")
PY

# everything mentioning whatsapp
jq -r '.packages[] | select(.description|test("whatsapp";"i")) | "\(.name)\t\(.version)"' community-nodes/index.json

# official-scope packages only
jq -r '.packages[] | select(.official_scope) | .name' community-nodes/index.json
```

The `official_scope` flag only means the package name starts with `@n8n/`. It is **not** a
verified badge — check the shield icon in the n8n panel for that.

---

## Shortlist

Nodes approved for use in this repository live in `shortlist.json`, not in a table nobody
checks. Each entry pins an exact version and records who reviewed it and why.

`tools/security_scan.py` verifies every entry against npm: exact version pin, declared licence,
declared source repository, publication age, last-modified date, and Levenshtein distance to the
most-downloaded packages. A typosquat, an unpinned version or a package with no repository is a
CI failure.

```bash
python3 tools/security_scan.py --fail-on medium
```

The list is empty on purpose. Nothing gets approved until it is needed and read.

---

## Rebuilding

```bash
python3 tools/build_community_index.py --pages 6 --downloads 400
```

The script reads `registry.npmjs.org` and `api.npmjs.org` only, and writes metadata — no
package code is vendored into this repository.
