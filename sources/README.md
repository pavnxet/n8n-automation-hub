# Sources

`sources.json` is the provenance record for this repository. If a file here came from
somewhere else, the source is in that file — with its licence, what it actually contains, and
what was verified about it.

Twenty sources are registered as of 2026-11-17.

---

## Tiers

| Tier | Meaning | How it may be used |
|---|---|---|
| `official` | Published by n8n | Copied into the knowledge base, cited as authoritative |
| `community-curated` | Identifiable maintainer, stated licence, hand-picked content | Read for patterns; a workflow may be adapted with attribution |
| `aggregator` | Bulk collection, unclear per-file provenance | Research only. Never bulk-imported, never presented as original |

The tier is a statement about **provenance**, not about quality of any single file. A good
workflow inside an aggregator is still untraceable, which is the problem.

---

## Why aggregators are research-only

Bulk collections are useful for seeing what people automate. They are poor inputs to a
repository like this one, for three reasons found during research:

1. **Placeholders.** An independent audit of the largest collection reported that a large
   share of files replace AI nodes with `n8n-nodes-base.noOp`, so the AI steps do nothing.
   Importing one produces a workflow that looks complete and silently skips the model call.
2. **No attribution.** Many files carry no author, no source URL and no licence. Copying them
   into a private repo is a licence question you cannot answer.
3. **No verification.** Nothing checks that a file imports into a current n8n version, that
   its `typeVersion` values still exist, or that its parameters are still valid.

The workflow in this repository is the opposite: read it, validate it, scrub it, attribute it,
then commit it.

---

## Adding a source

Append one object to `sources.json`:

```json
{
  "id": "short-slug",
  "name": "Human name",
  "url": "https://…",
  "tier": "official | community-curated | aggregator",
  "licence": "MIT / CC BY 4.0 / Sustainable Use License / Not stated",
  "what_it_is": "What it actually contains, in one sentence.",
  "quality_notes": "What you verified — counts, placeholders, attribution, referral links.",
  "used_for": "knowledge-base / automations / landscape research only",
  "last_checked": "YYYY-MM-DD"
}
```

Then update the count in the first paragraph of this file, and note it in `CHANGELOG.md`.

---

## Reviewing a source before you trust it

Step 1: read the licence file, not the GitHub sidebar — they disagree often.

Step 2: open five files at random and check three things.

- Do the nodes have real `type` values, or `noOp` / `stickyNote` placeholders?
- Is there a `typeVersion` on each node?
- Can you find the original author anywhere in the file or its history?

Step 3: check whether the repository attributes its own sources. A collection that hides
where its files came from cannot be a source of record.

Step 4: record what you found in `quality_notes`, in plain language, including the bad parts.

---

## Refresh cadence

| Source | Checked | Next |
|---|---|---|
| n8n docs and docs repo | 2026-11-17 | monthly |
| npm node packages | 2026-11-17 | monthly, or when an n8n release changes a node used here |
| Community collections | 2026-11-17 | quarterly |
| `awesome-n8n-restyler` | 2026-11-17 | quarterly, or when the ranking is refreshed |
| `ncnodes` | 2026-11-17 | quarterly |
