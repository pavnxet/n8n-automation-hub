# Importing a workflow

From a file in `automations/` to a running automation, without leaking credentials or
importing something that silently does nothing.

---

## 1. Before you import

Read the JSON. Ten seconds of reading prevents most incidents.

| Check | Why |
|---|---|
| Does it contain `n8n-nodes-base.executeCommand`, `readWriteFile`, or a `Code` node? | These run on your host with your permissions |
| Any `httpRequest` node? Look at the URL. | It can post your data anywhere |
| Any `n8n-nodes-*` community node? | Third-party code with full host access — install only what you trust |
| Is there a sticky note explaining it? | If not, treat the workflow as unexplained |
| Any literal that looks like a key or an id? | Remove it before import |

---

## 2. Import

Step 1: in n8n, go to **Workflows → ⋯ (top right) → Import from File** and choose the JSON.

Step 2: the workflow opens with red credential warnings on each node that needs one. That is
expected — this repository never ships credentials.

Step 3: for each flagged node, pick an existing credential or create a new one. Use a
least-privilege credential per workflow rather than one shared admin key.

Step 4: replace empty resource locators — sheet, base, folder, channel, mailbox. These were
scrubbed on purpose; select the real target now.

Step 5: run it once manually with **Execute Workflow**. Check the output of each node, not
just the last one.

Step 6: set the error workflow (**Workflow settings → Error Workflow**) before activating.

Step 7: activate.

---

## 3. Credential cheat sheet

Internal names, as they appear in the knowledge base `credential_types` field.

| Service | Credential type | Notes |
|---|---|---|
| Google (Gmail, Sheets, Drive, Calendar) | `googleApi`, `gmailOAuth2`, `googleSheetsOAuth2Api`, `googleDriveOAuth2Api` | Prefer OAuth2 over service account for user data; enable the specific API in the Google Cloud project |
| Slack | `slackApi` (bot token) or `slackOAuth2Api` | Bot token needs the scopes the workflow uses; check `credentials/slack.json` |
| OpenAI / Anthropic / Gemini | `openAiApi`, `anthropicApi`, `googlePalmApi` | One key per environment |
| Airtable | `airtableTokenApi` or `airtableOAuth2Api` | Personal access token needs the right base scopes |
| Notion | `notionApi` | Share the page or database with the integration explicitly |
| HTTP APIs (no dedicated node) | `httpHeaderAuth`, `httpBasicAuth`, `httpQueryAuth`, `httpCustomAuth` | Generic credential types for `httpRequest` |
| IMAP / SMTP | `imap`, `smtp` | App passwords, not account passwords, where the provider offers them |

Full list with authentication methods: `knowledge-base/indexes/credentials.json`.

---

## 4. Importing a workflow you found elsewhere

A workflow from a blog, a marketplace or a bulk collection is untrusted code.

1. Open it in a text editor, not in n8n.
2. List the node types. Anything you do not recognise, look up before importing.
3. Search for `httpRequest` and read every URL.
4. Search for the strings `executeCommand`, `eval(`, `child_process`, `fs.` — a Code node can
   do all of this.
5. Import into a scratch instance if you have one, not production.
6. Run it with fake data before pointing it at real data.

Bulk collections are the highest-risk source: a large share of files in the biggest ones are
known to contain placeholder `noOp` nodes where AI nodes should be, so the workflow imports
cleanly and quietly does nothing. See `../sources/README.md`.

---

## 5. Moving a workflow between instances

Step 1: export from the source instance (**Download**), not copy-paste from the canvas.

Step 2: credentials do not travel. Note which ones each node used before exporting.

Step 3: on the target, import, then re-attach credentials node by node.

Step 4: compare `typeVersion` values. If the target runs an older n8n, some nodes will load
at a lower version and parameters may not match — the knowledge base records the versions
that were current at snapshot time.

Step 5: check the timezone. Schedule triggers run in the instance timezone unless the
workflow sets its own.
