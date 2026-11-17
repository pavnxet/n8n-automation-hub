# Security policy

## Reporting

This repository is private, so there is no public disclosure channel. Report an issue by
opening a private security advisory on this repository (Security → Advisories → New draft
security advisory) or by contacting the maintainer directly.

Include: the file and path, what the risk is, how it could be triggered, and whether a
secret was exposed.

## What counts as a security issue here

- A committed credential, token, key or secret-shaped value in a workflow parameter.
- A workflow that, on import, would exfiltrate data, call an unexpected host, or run shell
  commands without the reader noticing.
- A knowledge-base record that misdocuments an authentication method in a way that would
  push someone towards an insecure setup.
- A tooling bug that causes validation to pass a workflow it should reject.

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
