# Workflow conventions

Rules for any workflow JSON that lives in `automations/`. CI enforces the mechanical ones;
the rest are review criteria.

---

## 1. Structure

### Required keys

| Key | Rule |
|---|---|
| `name` | Human-readable, sentence case, describes the job |
| `nodes` | Non-empty array |
| `connections` | Object keyed by **node name** |
| `settings.executionOrder` | `"v1"` for anything new |

### Every node needs

```json
{
  "parameters": {},
  "id": "uuid-v4",
  "name": "Unique readable name",
  "type": "n8n-nodes-base.something",
  "typeVersion": 2.2,
  "position": [220, 0]
}
```

- `type` — a real node type. Built-in types are in `knowledge-base/catalog.json` as
  `workflow_type`. Community types follow `n8n-nodes-*` or `@scope/n8n-nodes-*`.
- `typeVersion` — take `type_version` from the knowledge base record. Missing versions make
  n8n fall back to defaults that may not match your parameter names.
- `name` — must be unique. `connections` is keyed by name, so two nodes called
  "HTTP Request" silently collapse into one.
- `id` — any UUID v4, unique inside the workflow. Export from n8n rather than inventing ids.

---

## 2. Naming

| Thing | Pattern | Good | Bad |
|---|---|---|---|
| File | kebab-case, describes the job | `invoice-logger.json` | `workflow1.json`, `gmail2.json` |
| Node | Verb + object | `Fetch open invoices` | `HTTP Request1` |
| Credential reference in docs | internal type name | `googleSheetsOAuth2Api` | "Google Sheets login" |
| Folder | group, then app | `integrations/google-sheets/` | `misc/` |

---

## 3. Layout

- Left to right, 220 px apart: `[0,0]`, `[220,0]`, `[440,0]`.
- Branches drop 150–200 px: the second output of an IF sits at `[440,200]`.
- AI cluster sub-nodes sit **below** their agent, 200 px down and 220 px apart.
- One sticky note per workflow, top-left, at negative x so it never overlaps the flow.
- No duplicate positions — CI rejects them.

---

## 4. Data and expressions

- Reference upstream data with `{{ $json.field }}`; prefix the whole string with `=`
  (`"text": "={{ $json.message }}"`) or it is treated as a literal.
- Reach into a specific node with `{{ $('Node Name').item.json.field }}`; keep node names
  stable or those references break silently.
- Prefer **Set (Edit Fields)** over Code for simple reshaping — it survives upgrades better
  and is readable in the canvas.
- Use the Code node (`n8n-nodes-base.code`) for logic that would otherwise be five IF nodes,
  and return `[{ json: { ... } }]`.
- Binary data lives under `$binary`; convert with `convertToFile` / `extractFromFile` rather
  than handling base64 by hand.

---

## 5. Error handling

Production workflows in this repository follow three rules:

1. **A workflow-level error workflow** is set in `settings.errorWorkflow`, pointing at a
   workflow that notifies a channel you actually read.
2. **Retries on network nodes**: `retryOnFail: true` with `maxTries: 3` and
   `waitBetweenTries: 2000` for anything that calls an external API.
3. **A stop-and-report branch** instead of silent failure: an IF on `$json.error` that ends in
   a notification node, not a dead end.

A workflow with no failure path is accepted only if it is explicitly labelled as a demo.

---

## 6. Secrets and identifiers

Never in a parameter value:

| Never | Instead |
|---|---|
| API keys, tokens, passwords | Attach a credential in n8n after import |
| OAuth client secrets | Same |
| Personal emails, phone numbers | Placeholder or empty |
| Sheet ids, folder ids, base ids, instance ids | Empty resource-locator value |
| Webhook path segments that act as a secret | Empty path |

CI fails on fields named `apiKey`, `token`, `password`, `secret`, `clientSecret`,
`privateKey` with a non-empty literal, and on values that look like live keys
(`sk-`, `ghp_`, `xoxb-`, long high-entropy strings).

---

## 7. Documentation per workflow

Every automation folder has a `README.md` covering:

1. What it does — trigger → steps → result, one paragraph.
2. Trigger — schedule, webhook, app event, manual; include the interval or event name.
3. Credentials — table of credential type → node → scopes required.
4. Assumptions — rate limits, plan requirements, expected input shape.
5. Tested with — n8n version, self-hosted or Cloud, date.
6. Provenance — written here, or adapted from `<source>` and recorded in `sources/sources.json`.

---

## 8. Versioning

| Change | Version bump | Notes |
|---|---|---|
| New workflow | minor | — |
| Fix inside an existing workflow | patch | Say what was broken in the commit body |
| Change that alters output shape or required credentials | major | Note it in `CHANGELOG.md` |
| Knowledge base refresh | patch on the KB, note the package versions | Regenerated files only |

---

## 9. Review checklist

- [ ] Imports into a current n8n without warnings.
- [ ] Runs once end to end, or the failure point is documented.
- [ ] No secret-shaped or personal values.
- [ ] Node names unique and readable; connections keyed correctly.
- [ ] `typeVersion` present on every node.
- [ ] Failure path exists or the workflow is labelled a demo.
- [ ] README filled in; provenance recorded.
- [ ] `python3 tools/validate_repo.py` passes and `registry.json` is committed.
