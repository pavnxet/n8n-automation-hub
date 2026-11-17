# Community nodes

`index.json` is an index of n8n community node packages taken straight from the npm
registry, using the same keyword n8n's own **Settings → Community Nodes → Browse** searches:
`n8n-community-node-package`.

| Field | Value |
|---|---|
| Packages indexed | 1,500 (top of npm search ranking) |
| npm matches for the keyword | 14,543 |
| Packages with download counts | 329 (last 30 days) |
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

Nodes actually approved for use in this repository. Empty until one is evaluated — add a row
only after reading the source or finding it verified.

| Package | Version pinned | Verified | Why it is here | Reviewed |
|---|---|---|---|---|
| — | — | — | — | — |

---

## Rebuilding

```bash
python3 tools/build_community_index.py --pages 6 --downloads 400
```

The script reads `registry.npmjs.org` and `api.npmjs.org` only, and writes metadata — no
package code is vendored into this repository.
