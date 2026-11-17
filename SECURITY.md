# Security policy

## Reporting

Report an issue by opening a private security advisory on this repository
(Security → Advisories → New draft security advisory) or by contacting the maintainer directly.
Please do not open a public issue for a suspected secret.

Include: the file and path, what the risk is, how it could be triggered, and whether a
secret was exposed.

## What counts as a security issue here

- A committed credential, token, key or secret-shaped value in a workflow parameter.
- A workflow that, on import, would exfiltrate data, call an unexpected host, or run shell
  commands without the reader noticing.
- A knowledge-base record that misdocuments an authentication method in a way that would
  push someone towards an insecure setup.
- A tooling bug that causes validation to pass a workflow it should reject.

## Automated checks

Two scanners run in CI on every push and pull request. Neither replaces reading a diff.

| Script | Scope | Fails CI on |
|---|---|---|
| `tools/validate_repo.py` | workflow structure | secret-shaped parameter fields, duplicate node names, unknown node types, missing `typeVersion`, unresolvable connections, duplicate positions |
| `tools/security_scan.py` | workflows, KB records, community packages | any `high` finding — real credential shapes, `executeCommand`/`ssh`, `eval`/`child_process` in a Code node, unauthenticated webhooks, typosquatted packages |

What `security_scan.py` looks for, in its own words:

| Rule | Severity | Catches |
|---|---|---|
| SEC001 | high | literal value in a field named like a secret (`apiKey`, `token`, `password`, …) |
| SEC002 | high / critical | real key shapes: `sk-`, `sk-ant-`, `ghp_`, `github_pat_`, `xoxb-`, `AKIA`, `AIza`, `ya29.`, JWTs, PEM private keys, Stripe live keys |
| SEC003 | high | Slack or Discord webhook URLs carrying a live token |
| SEC004 | high / medium | `executeCommand`, `ssh`, `readWriteFile`, `localFileTrigger`, `ftp` |
| SEC005 | high / medium | Code node touching `child_process`, `eval(`, `new Function`, `process.env`, `fs.*` |
| SEC006 | medium | HTTP Request aimed at cloud metadata, loopback or private ranges (SSRF) |
| SEC007 | medium | webhook with no authentication |
| SEC008 | low | email addresses embedded in workflow data |
| SEC009 | medium | `allowUnauthorizedCerts: true` |
| SEC011 | low | long high-entropy strings that could be a key |
| SEC012 | low | community node in use but not on the shortlist |
| SEC101 | high | credential shapes pasted into a knowledge-base record |
| SEC202–SEC207 | medium / low | unpinned version, typosquat distance, missing repository or licence, brand-new package, unmaintained package |

Accepted risks live in `security/waivers.json`, each with a reason, an owner and an expiry
date. Expired waivers stop applying automatically.

## Secret handling rules

1. **Credentials never enter this repository.** Workflows are exported with credential
   references stripped; you attach credentials inside your own n8n instance.
2. **Scrub before commit.** `tools/validate_repo.py` fails on keys named `apiKey`, `token`,
   `password`, `secret`, `clientSecret`, `privateKey` with a literal value, and on
   high-entropy strings that look like live keys (`sk-`, `ghp_`, `xoxb-`, long base64/hex).
3. **No personal identifiers.** Sheet ids, folder ids, instance ids, personal emails and
   webhook paths with secrets are removed before commit.
4. **Rotate on suspicion.** If a secret did land in a commit, rotate it first, then rewrite
   history — deleting the file is not enough, the object stays in the pack.

## The optional n8n API client

`server/n8n_api.py` is off unless `N8N_BASE_URL` and `N8N_API_KEY` are set. When it is on:

- the key travels only in the `X-N8N-API-KEY` header and is redacted from every error message;
- workflows are uploaded with their credential references stripped, because credential ids are
  instance-local and names are sensitive;
- nothing is ever activated, overwritten or deleted — the client has no such call;
- `execute_workflow` needs `N8N_ALLOW_EXECUTE=1` **and** `confirm: true`, and should point at a
  staging instance rather than production.

Treat a configured client as production access to your automation platform: the same review
rules apply as for a human with an API key.

## Importing a workflow you did not write

Treat a downloaded workflow as untrusted code. Before importing, open the JSON and read:

| Node | Why it matters |
|---|---|
| `n8n-nodes-base.executeCommand` | Runs shell commands on the host |
| `n8n-nodes-base.code` / `function` | Arbitrary JavaScript in the n8n process |
| `n8n-nodes-base.httpRequest` | Any URL, any header — check for credential harvesting |
| `n8n-nodes-base.readWriteFile` | Filesystem access outside the workflow |
| `n8n-nodes-base.webhook` | Opens a public endpoint; check the auth setting |
| Any `n8n-nodes-*` community node | Third-party code with full host access |

## Instance hardening checklist

- Keep n8n behind TLS and do not expose the editor publicly without auth.
- Set `N8N_ENCRYPTION_KEY` explicitly and back it up — losing it loses every credential.
- Restrict community nodes: `N8N_COMMUNITY_PACKAGES_ENABLED=false`, or allow only verified
  packages with `N8N_UNVERIFIED_PACKAGES_ENABLED=false`.
- Use `NODES_EXCLUDE` to remove `executeCommand`, `localFileTrigger` and any node you do not
  need.
- Prefer a dedicated, least-privilege credential per workflow over a shared admin key.
- Turn on execution data pruning; workflow data can contain customer PII.
- Point error workflows at a channel you actually read.
