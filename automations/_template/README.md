# Template

Starting point for a new automation.

```bash
cp -r automations/_template automations/integrations/my-service
```

Then:

1. Replace `workflow.json` with a real export from n8n (**Download**), or edit this one.
2. Keep the sticky note — rewrite it for the real workflow: what it does, credentials needed,
   assumptions.
3. Scrub secrets and identifiers before committing (see `../../SECURITY.md`).
4. Fill in the README below.
5. Run `python3 tools/validate_repo.py`.
6. Update `automations/registry.json` by committing the regenerated file.

---

## What it does

<!-- One paragraph. Trigger → steps → result. -->

## Trigger

<!-- Schedule, webhook, app event, manual. Include the interval or event name. -->

## Credentials

| Credential type | Used by | Scopes / notes |
|---|---|---|
| `exampleCredential` | Node name | what the scope must allow |

## Assumptions and limits

<!-- Rate limits, API quotas, required plan, data shape expected from the previous node. -->

## Tested with

<!-- n8n version, self-hosted or Cloud, date. -->

## Provenance

<!-- Written here, or adapted from <source>. If adapted, record it in sources/sources.json. -->
