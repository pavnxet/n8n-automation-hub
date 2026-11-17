# Notice — third-party material in this repository

This repository combines material under several licences. The map below says which licence
applies to which path, and where the original lives.

---

## 1. This repository's own work — MIT

| Path | Licence |
|---|---|
| `tools/` | MIT |
| `docs/` | MIT |
| `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md` | MIT |
| `automations/` workflows written for this repository | MIT |

Full text: `LICENSE`.

---

## 2. n8n documentation content — Sustainable Use License v1.0

| Path | Origin |
|---|---|
| `knowledge-base/nodes/` | docs.n8n.io — `integrations/builtin/**` |
| `knowledge-base/credentials/` | docs.n8n.io — `integrations/builtin/credentials/**` |
| `knowledge-base/examples/` | docs.n8n.io — `docs/_workflows/**` |
| `automations/ai/`, `automations/integrations/`, `automations/core/`, `automations/patterns/` | docs.n8n.io — `docs/_workflows/**` |

Source: <https://github.com/n8n-io/n8n-docs> · documentation: <https://docs.n8n.io>
Licence: n8n Sustainable Use License v1.0 — <https://docs.n8n.io/n8n-community-license>

What the licence grants and limits:

- You may use, modify and prepare derivative works for your **own internal business
  purposes, or for non-commercial or personal use**.
- You may distribute this material to others **only free of charge and non-commercially**.
- You may **not alter, remove or obscure** n8n's licensing, copyright or other notices.

Practical consequence: keeping this repository private is clearly within the licence. Making
it public is only acceptable while it stays free and non-commercial, with this notice intact.
Any commercial redistribution needs a separate agreement with n8n (license@n8n.io).

---

## 3. Node parameter schemas — package metadata

| Path | Origin |
|---|---|
| `node_schema` blocks inside `knowledge-base/nodes/**` | `n8n-nodes-base@2.15.1`, `@n8n/n8n-nodes-langchain@2.48.3` — `dist/types/nodes.json` |
| `knowledge-base/indexes/resources-operations.json` | derived from the same files |

These packages ship under the n8n Sustainable Use License (with the `.ee.` enterprise files
excluded, which this repository does not use). Same terms as section 2.

---

## 4. Community node metadata — npm registry

| Path | Origin |
|---|---|
| `community-nodes/index.json` | `https://registry.npmjs.org/-/v1/search?text=keywords:n8n-community-node-package` and `https://api.npmjs.org/downloads` |

This file contains **metadata only** — package names, versions, descriptions, authors,
links, download counts. No package code is vendored here. Each package remains under its own
licence; check it before installing or redistributing anything.

---

## 5. Third-party sources referenced, not vendored

The sources below informed `docs/research-2026-11.md` and `sources/sources.json`. No files
from them are copied into this repository.

| Source | Licence (as published) | Used for |
|---|---|---|
| `n8n-io/n8n-docs` | Sustainable Use License | Knowledge base, seed workflows |
| `n8n-io/n8n` | Sustainable Use License | Behaviour reference |
| n8n template library (n8n.io/workflows) | hosted by n8n | Discovery, not copied |
| `enescingoz/awesome-n8n-templates` | CC BY 4.0 (per LICENSE file) | Landscape research |
| `felipfr/awesome-n8n-workflows` | MIT | Landscape research |
| `Zie619/n8n-workflows` | MIT (collection) | Landscape research |
| `ScraperNode/awesome-n8n-templates` | MIT (collection) | Landscape research |
| `nusquama/n8nworkflows.xyz` | not stated in repository | Landscape research |
| `7and1/n8n-Library` | not stated in repository | Landscape research |

Trademarks: n8n is a trademark of n8n GmbH. This repository is not affiliated with,
endorsed by, or sponsored by n8n.
