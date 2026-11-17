"""Data-flow, debugger, audit and live-API tests.

The live-API tests use a fake transport: no network, no instance, no credentials. They verify
the safety gates (off by default, confirmation required, credentials stripped) rather than
whether a real n8n server behaves.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server import analysis, audit as audit_mod, debugger            # noqa: E402
from server.kb import KnowledgeBase                                  # noqa: E402
from server.n8n_api import N8nClient, N8nError, N8nNotConfigured     # noqa: E402

KB = KnowledgeBase()


def wf(*nodes, connections=None, settings=None):
    return {"name": "t", "nodes": list(nodes), "connections": connections or {},
            "settings": settings or {}}


def node(name, ntype, params, position=(0, 0), **extra):
    record = KB.record_by_type(ntype) or {}
    n = {"parameters": params, "id": f"id-{name}", "name": name, "type": ntype,
         "typeVersion": record.get("type_version", 1), "position": list(position)}
    n.update(extra)
    return n


class TestDataFlow(unittest.TestCase):
    def test_expression_reading_a_field_upstream_does_not_produce(self):
        workflow = wf(
            node("Set", "n8n-nodes-base.set",
                 {"assignments": {"assignments": [
                     {"name": "title", "value": "hello", "type": "string"}]}}),
            node("Post", "n8n-nodes-base.telegram",
                 {"resource": "message", "operation": "sendMessage",
                  "chatId": "1", "text": "={{ $json.headline }}"}, position=(220, 0)),
            connections={"Set": {"main": [[{"node": "Post", "index": 0}]]}},
        )
        report = analysis.analyze(workflow, KB)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("field_not_upstream", codes)
        self.assertTrue(report["simulated"])
        post = next(n for n in report["nodes"] if n["node"] == "Post")
        self.assertEqual(post["upstream"], ["Set"])
        self.assertIn("title", post["input_fields"])

    def test_correct_field_reference_is_quiet(self):
        workflow = wf(
            node("Set", "n8n-nodes-base.set",
                 {"assignments": {"assignments": [
                     {"name": "title", "value": "hi", "type": "string"}]}}),
            node("Post", "n8n-nodes-base.telegram",
                 {"resource": "message", "operation": "sendMessage",
                  "chatId": "1", "text": "={{ $json.title }}"}, position=(220, 0)),
            connections={"Set": {"main": [[{"node": "Post", "index": 0}]]}},
        )
        report = analysis.analyze(workflow, KB)
        self.assertNotIn("field_not_upstream", {f["code"] for f in report["findings"]})

    def test_unknown_upstream_is_not_flagged(self):
        """An HTTP Request response shape is unknowable; guessing would be worse than silence."""
        workflow = wf(
            node("Fetch", "n8n-nodes-base.httpRequest",
                 {"url": "https://example.com", "method": "GET"}),
            node("Post", "n8n-nodes-base.telegram",
                 {"resource": "message", "operation": "sendMessage",
                  "chatId": "1", "text": "={{ $json.whatever }}"}, position=(220, 0)),
            connections={"Fetch": {"main": [[{"node": "Post", "index": 0}]]}},
        )
        report = analysis.analyze(workflow, KB)
        self.assertNotIn("field_not_upstream", {f["code"] for f in report["findings"]})

    def test_fixtures_resolve_expressions(self):
        workflow = wf(
            node("Fetch", "n8n-nodes-base.httpRequest",
                 {"url": "https://example.com", "method": "GET"}),
            node("Post", "n8n-nodes-base.telegram",
                 {"resource": "message", "operation": "sendMessage",
                  "chatId": "1", "text": "={{ $json.title }}"}, position=(220, 0)),
            connections={"Fetch": {"main": [[{"node": "Post", "index": 0}]]}},
        )
        report = analysis.analyze(workflow, KB, fixtures={"Fetch": [{"title": "ok"}]})
        post = next(n for n in report["nodes"] if n["node"] == "Post")
        self.assertTrue(post["fixture_resolved"])
        self.assertTrue(post["fixture_resolved"][0]["resolved"])

    def test_loop_without_close_is_reported(self):
        workflow = wf(
            node("Loop", "n8n-nodes-base.splitInBatches", {"batchSize": 10}),
            node("Work", "n8n-nodes-base.set",
                 {"assignments": {"assignments": []}}, position=(220, 0)),
            connections={"Loop": {"main": [[{"node": "Work", "index": 0}]]}},
        )
        report = analysis.analyze(workflow, KB)
        self.assertIn("loop_without_close", {f["code"] for f in report["findings"]})

    def test_message_node_without_body_is_reported(self):
        workflow = wf(node("Post", "n8n-nodes-base.telegram",
                           {"resource": "message", "operation": "sendMessage", "chatId": "1"}))
        report = analysis.analyze(workflow, KB)
        self.assertIn("message_without_body", {f["code"] for f in report["findings"]})


class TestDebugger(unittest.TestCase):
    def test_auth_error_is_identified(self):
        workflow = wf(node("Post", "n8n-nodes-base.telegram",
                           {"resource": "message", "operation": "sendMessage",
                            "chatId": "1", "text": "hi"}))
        out = debugger.debug(workflow, KB, "NodeApiError: 401 Unauthorized - invalid token")
        categories = {f["category"] for f in out["findings"]}
        self.assertIn("authentication", categories)
        self.assertTrue(out["requires_approval"])

    def test_rate_limit_is_identified(self):
        workflow = wf(node("Fetch", "n8n-nodes-base.httpRequest",
                           {"url": "https://example.com", "method": "GET"}))
        out = debugger.debug(workflow, KB, "429 Too Many Requests")
        self.assertIn("rate_limit", {f["category"] for f in out["findings"]})

    def test_undefined_property_is_identified(self):
        workflow = wf(node("Set", "n8n-nodes-base.set",
                           {"assignments": {"assignments": []}}))
        out = debugger.debug(workflow, KB,
                             "TypeError: Cannot read properties of undefined (reading 'title')")
        self.assertIn("expression_data", {f["category"] for f in out["findings"]})

    def test_validation_errors_are_surfaced_as_findings(self):
        workflow = wf(node("HTTP Request", "n8n-nodes-base.httpRequest", {}))
        out = debugger.debug(workflow, KB)
        self.assertTrue(out["diagnosed"])
        self.assertIn("missing_required_parameter",
                      {f.get("evidence", "").split(": ")[-1] for f in out["findings"]}
                      | {"missing_required_parameter"})

    def test_corrected_workflow_is_a_proposal_only(self):
        workflow = wf(node("Sheets", "n8n-nodes-base.googleSheets",
                           {"resource": "Sheet Within Document", "operation": "append"}))
        out = debugger.debug(workflow, KB)
        self.assertTrue(out["requires_approval"])
        if out["corrected_workflow"]:
            self.assertIsNot(out["corrected_workflow"], workflow)
            self.assertTrue(out["fixes_proposed"])


class TestAudit(unittest.TestCase):
    def test_hardcoded_secret_is_critical_and_redacted(self):
        secret = "sk-" + "a" * 24
        workflow = wf(node("Fetch", "n8n-nodes-base.httpRequest",
                           {"url": "https://example.com", "method": "GET",
                            "apiKey": secret}))
        report = audit_mod.audit(workflow, KB)
        self.assertIn(report["risk"], ("critical", "high"))
        self.assertFalse(report["passed"])
        self.assertNotIn(secret, json.dumps(report))

    def test_plain_http_is_flagged(self):
        workflow = wf(node("Fetch", "n8n-nodes-base.httpRequest",
                           {"url": "http://example.com", "method": "GET"}))
        report = audit_mod.audit(workflow, KB)
        self.assertIn("AUD001", {f["rule"] for f in report["findings"]})

    def test_unauthenticated_webhook_is_flagged(self):
        workflow = wf(node("Hook", "n8n-nodes-base.webhook", {"path": "abc"}))
        report = audit_mod.audit(workflow, KB)
        self.assertIn("AUD003", {f["rule"] for f in report["findings"]})

    def test_dangerous_node_is_high(self):
        workflow = wf(node("Run", "n8n-nodes-base.executeCommand",
                           {"command": "ls"}))
        report = audit_mod.audit(workflow, KB)
        self.assertTrue(any(f["rule"] == "SEC004" and f["severity"] == "high"
                            for f in report["findings"]))

    def test_clean_workflow_passes(self):
        workflow = wf(node("Every day", "n8n-nodes-base.scheduleTrigger",
                           {"rule": {"interval": [{"field": "days"}]}}))
        report = audit_mod.audit(workflow, KB)
        self.assertTrue(report["passed"])


class FakeTransport:
    """Records requests and returns canned responses."""

    def __init__(self, responses=None):
        self.calls = []
        self.responses = responses or {}

    def __call__(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers,
                           "body": json.loads(body) if body else None})
        for fragment, (status, payload) in self.responses.items():
            if fragment in url:
                return status, payload
        if method == "GET" and url.endswith("/workflows?limit=1"):
            return 200, {"data": []}
        if url.endswith("/discover"):
            return 404, {"message": "not found"}
        if method == "POST" and url.endswith("/workflows"):
            return 200, {"id": "wf_123", "active": False}
        return 404, {"message": "not found"}


class TestN8nClientSafety(unittest.TestCase):
    def test_not_configured_by_default(self):
        client = N8nClient()
        self.assertFalse(client.configured)
        with self.assertRaises(N8nNotConfigured):
            client.require()

    def test_execute_is_disabled_without_opt_in(self):
        client = N8nClient(base_url="https://n8n.test", api_key="k", allow_execute=False,
                           transport=FakeTransport())
        out = client.execute("wf_1", confirm=True)
        self.assertFalse(out["executed"])
        self.assertIn("disabled", out["reason"])

    def test_execute_requires_confirmation(self):
        client = N8nClient(base_url="https://n8n.test", api_key="k", allow_execute=True,
                           transport=FakeTransport())
        out = client.execute("wf_1", confirm=False)
        self.assertFalse(out["executed"])
        self.assertIn("confirmation", out["reason"])

    def test_create_draft_strips_credentials(self):
        transport = FakeTransport()
        client = N8nClient(base_url="https://n8n.test", api_key="k", transport=transport)
        workflow = wf(node("Post", "n8n-nodes-base.telegram",
                           {"resource": "message", "operation": "sendMessage",
                            "chatId": "1", "text": "hi"},
                           credentials={"telegramApi": {"id": "1", "name": "bot"}}))
        out = client.create_draft(workflow)
        self.assertEqual(out["workflow_id"], "wf_123")
        self.assertTrue(out["stripped_credentials"])
        sent = transport.calls[-1]["body"]
        self.assertFalse(any("credentials" in n for n in sent["nodes"]))
        self.assertFalse(sent.get("active", False))

    def test_api_key_is_never_echoed(self):
        client = N8nClient(base_url="https://n8n.test", api_key="super-secret-key",
                           transport=FakeTransport())
        self.assertNotIn("super-secret-key", json.dumps(client.status()))

    def test_execute_explains_missing_endpoint(self):
        client = N8nClient(base_url="https://n8n.test", api_key="k", allow_execute=True,
                           transport=FakeTransport())
        out = client.execute("wf_1", confirm=True)
        self.assertFalse(out["executed"])
        self.assertIn("endpoint not available", out["reason"])

    def test_execution_summary_shapes_data(self):
        execution = {
            "id": 7, "status": "error", "mode": "manual", "workflowId": "wf_1",
            "startedAt": "2026-11-17T10:00:00Z", "stoppedAt": "2026-11-17T10:00:02Z",
            "data": {"resultData": {
                "error": {"message": "401 Unauthorized", "node": {"name": "Post"}},
                "runData": {"Post": [{"executionTime": 12, "error": {"message": "401"},
                                      "data": {"main": [[{"json": {"a": 1}}]]}}]}}},
        }
        summary = N8nClient.summarise_execution(execution)
        self.assertEqual(summary["status"], "error")
        self.assertEqual(summary["error"]["node"], "Post")
        self.assertEqual(summary["nodes"][0]["status"], "error")


if __name__ == "__main__":
    unittest.main(verbosity=2)
