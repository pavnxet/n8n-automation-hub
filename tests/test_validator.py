"""Validator tests: every case here is a workflow that must be caught, plus valid workflows
that must not be rejected.

The first two cases are the reported bug: an HTTP Request with no URL, and a Telegram node
with no chat/text. Both used to pass.
"""
import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.kb import KnowledgeBase          # noqa: E402
from server.validation import validate       # noqa: E402

KB = KnowledgeBase()


def wf(*nodes, connections=None):
    return {"name": "test", "nodes": list(nodes), "connections": connections or {}}


def node(name, ntype, params=None, tv=None, nid=None, position=None, credentials=None):
    record = KB.record_by_type(ntype) or {}
    n = {
        "parameters": params if params is not None else {},
        "id": nid or f"id-{name}",
        "name": name,
        "type": ntype,
        "typeVersion": tv if tv is not None else record.get("type_version", 1),
        "position": position or [0, 0],
    }
    if credentials:
        n["credentials"] = credentials
    return n


def codes(report):
    return {e["code"] for e in report["errors"]}


class TestRequiredParameters(unittest.TestCase):
    def test_http_request_without_url_is_invalid(self):
        """The reported bug."""
        report = validate(wf(node("HTTP Request", "n8n-nodes-base.httpRequest")), KB)
        self.assertFalse(report["valid"])
        self.assertIn("missing_required_parameter", codes(report))
        err = next(e for e in report["errors"] if e["code"] == "missing_required_parameter")
        self.assertEqual(err["parameter"], "url")
        self.assertEqual(err["node"], "HTTP Request")
        self.assertIn("suggestion", err)
        self.assertIn("doc", err)

    def test_http_request_with_url_is_valid(self):
        report = validate(wf(node("HTTP Request", "n8n-nodes-base.httpRequest",
                                  {"url": "https://example.com/api", "method": "GET"})), KB)
        self.assertTrue(report["valid"], report["errors"])

    def test_telegram_without_chat_or_text_is_invalid(self):
        report = validate(wf(node("Telegram", "n8n-nodes-base.telegram",
                                  {"resource": "message", "operation": "sendMessage"})), KB)
        self.assertFalse(report["valid"])
        missing = {e["parameter"] for e in report["errors"]
                   if e["code"] == "missing_required_parameter"}
        self.assertTrue({"chatId", "text"} & missing, f"expected chatId/text, got {missing}")

    def test_hidden_conditional_parameters_are_not_flagged(self):
        """A body type that is not selected must not produce phantom errors."""
        report = validate(wf(node("HTTP Request", "n8n-nodes-base.httpRequest",
                                  {"url": "https://example.com", "method": "GET"})), KB)
        self.assertTrue(report["valid"], report["errors"])


class TestTypesAndEnums(unittest.TestCase):
    def test_display_label_instead_of_internal_value(self):
        report = validate(wf(node("Sheets", "n8n-nodes-base.googleSheets",
                                  {"resource": "Sheet Within Document", "operation": "append"})), KB)
        self.assertFalse(report["valid"])
        err = next(e for e in report["errors"] if e["code"] == "invalid_enum")
        self.assertIn("display label", err["suggestion"])
        self.assertIn("'sheet'", err["suggestion"])

    def test_wrong_type_is_reported(self):
        report = validate(wf(node("HTTP", "n8n-nodes-base.httpRequest",
                                  {"url": {"not": "a string"}, "method": "GET"})), KB)
        self.assertFalse(report["valid"])
        self.assertTrue({"wrong_type", "invalid_enum"} & codes(report))

    def test_expression_values_are_not_type_checked(self):
        report = validate(wf(node("HTTP", "n8n-nodes-base.httpRequest",
                                  {"url": "={{ $json.endpoint }}", "method": "GET"})), KB)
        self.assertTrue(report["valid"], report["errors"])


class TestVersions(unittest.TestCase):
    def test_future_type_version_is_rejected(self):
        report = validate(wf(node("HTTP", "n8n-nodes-base.httpRequest",
                                  {"url": "https://example.com"}, tv=99.0)), KB)
        self.assertFalse(report["valid"])
        self.assertIn("unsupported_type_version", codes(report))

    def test_missing_type_version_is_rejected(self):
        n = node("HTTP", "n8n-nodes-base.httpRequest", {"url": "https://example.com"})
        n.pop("typeVersion")
        report = validate(wf(n), KB)
        self.assertIn("missing_type_version", codes(report))

    def test_old_type_version_warns_but_passes(self):
        report = validate(wf(node("HTTP", "n8n-nodes-base.httpRequest",
                                  {"url": "https://example.com"}, tv=1.0)), KB)
        self.assertTrue(report["valid"], report["errors"])
        self.assertIn("deprecated_type_version", {w["code"] for w in report["warnings"]})


class TestStructureAndConnections(unittest.TestCase):
    def test_duplicate_node_names(self):
        a = node("Same", "n8n-nodes-base.set", {"assignments": {"assignments": []}})
        b = node("Same", "n8n-nodes-base.set", {"assignments": {"assignments": []}}, nid="other")
        report = validate(wf(a, b), KB)
        self.assertIn("duplicate_node_name", codes(report))

    def test_duplicate_node_ids(self):
        a = node("A", "n8n-nodes-base.set", nid="dup")
        b = node("B", "n8n-nodes-base.set", nid="dup", position=[220, 0])
        report = validate(wf(a, b), KB)
        self.assertIn("duplicate_node_id", codes(report))

    def test_connection_to_missing_node(self):
        a = node("A", "n8n-nodes-base.manualTrigger")
        report = validate(wf(a, connections={"A": {"main": [[{"node": "Ghost", "index": 0}]]}}), KB)
        self.assertIn("connection_unknown_target", codes(report))

    def test_connection_from_missing_node(self):
        a = node("A", "n8n-nodes-base.manualTrigger")
        report = validate(wf(a, connections={"Ghost": {"main": [[]]}}), KB)
        self.assertIn("connection_unknown_source", codes(report))

    def test_orphan_node_warns(self):
        a = node("A", "n8n-nodes-base.manualTrigger")
        b = node("B", "n8n-nodes-base.set", position=[220, 0])
        report = validate(wf(a, b), KB)
        self.assertIn("orphan_node", {w["code"] for w in report["warnings"]})

    def test_unknown_node_type(self):
        report = validate(wf({"name": "X", "type": "n8n-nodes-base.notARealNode",
                              "parameters": {}, "id": "1", "typeVersion": 1,
                              "position": [0, 0]}), KB)
        self.assertIn("unknown_node_type", codes(report))

    def test_missing_trigger_is_a_warning_not_an_error(self):
        report = validate(wf(node("Set", "n8n-nodes-base.set",
                                  {"assignments": {"assignments": []}})), KB)
        self.assertTrue(report["valid"])
        self.assertIn("no_trigger", {w["code"] for w in report["warnings"]})


class TestExpressions(unittest.TestCase):
    def test_unknown_node_reference(self):
        report = validate(wf(
            node("Trigger", "n8n-nodes-base.manualTrigger"),
            node("Set", "n8n-nodes-base.set",
                 {"assignments": {"assignments": [
                     {"name": "x", "value": "={{ $('Missing Node').item.json.id }}",
                      "type": "string"}]}},
                 position=[220, 0])), KB)
        self.assertIn("expression_unknown_node", codes(report))

    def test_unbalanced_expression(self):
        report = validate(wf(node("HTTP", "n8n-nodes-base.httpRequest",
                                  {"url": "https://example.com", "options": {}},
                                  ), node("Set", "n8n-nodes-base.set",
                                          {"assignments": {"assignments": [
                                              {"name": "x", "value": "={{ $json.a ", "type": "string"}]}},
                                          position=[220, 0])), KB)
        self.assertFalse(report["valid"])

    def test_unknown_global(self):
        report = validate(wf(node("Set", "n8n-nodes-base.set",
                                  {"assignments": {"assignments": [
                                      {"name": "x", "value": "={{ $jsoN.a }}", "type": "string"}]}})), KB)
        self.assertIn("unknown_global", codes(report))

    def test_valid_expressions_pass(self):
        report = validate(wf(
            node("Trigger", "n8n-nodes-base.manualTrigger"),
            node("Set", "n8n-nodes-base.set",
                 {"assignments": {"assignments": [
                     {"name": "a", "value": "={{ $json.title }}", "type": "string"},
                     {"name": "b", "value": "={{ $now.toISO() }}", "type": "string"},
                     {"name": "c", "value": "={{ $('Trigger').item.json.id }}", "type": "string"}]}},
                 position=[220, 0])), KB)
        self.assertTrue(report["valid"], report["errors"])


class TestCredentials(unittest.TestCase):
    def test_missing_credential_reference_warns(self):
        report = validate(wf(node("Telegram", "n8n-nodes-base.telegram",
                                  {"resource": "message", "operation": "sendMessage",
                                   "chatId": "123", "text": "hi"})), KB)
        self.assertIn("missing_credential_reference", {w["code"] for w in report["warnings"]})

    def test_malformed_credential_reference(self):
        report = validate(wf(node("Telegram", "n8n-nodes-base.telegram",
                                  {"resource": "message", "operation": "sendMessage",
                                   "chatId": "123", "text": "hi"},
                                  credentials={"telegramApi": {}})), KB)
        self.assertIn("invalid_credential_structure", codes(report))

    def test_credential_values_are_never_echoed(self):
        secret = "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        report = validate(wf(node("Telegram", "n8n-nodes-base.telegram",
                                  {"resource": "message", "operation": "sendMessage",
                                   "chatId": "1", "text": "hi"},
                                  credentials={"telegramApi": {"id": secret}})), KB)
        self.assertNotIn(secret, str(report))


class TestValidWorkflowsSurvive(unittest.TestCase):
    def test_generated_style_workflow(self):
        trigger = node("Every day", "n8n-nodes-base.scheduleTrigger",
                       {"rule": {"interval": [{"field": "days", "triggerAtHour": 8}]}})
        http = node("Fetch", "n8n-nodes-base.httpRequest",
                    {"url": "https://example.com/api", "method": "GET",
                     "authentication": "none"}, position=[220, 0])
        slack = node("Post", "n8n-nodes-base.slack",
                     {"resource": "message", "operation": "post", "text": "={{ $json.title }}",
                      "authentication": "accessToken"}, position=[440, 0])
        report = validate(wf(trigger, http, slack, connections={
            "Every day": {"main": [[{"node": "Fetch", "index": 0}]]},
            "Fetch": {"main": [[{"node": "Post", "index": 0}]]},
        }), KB)
        self.assertTrue(report["valid"], report["errors"])

    def test_every_template_validates(self):
        import glob
        import json
        for path in glob.glob(os.path.join(ROOT, "templates", "*.json")):
            if path.endswith("index.json"):
                continue
            with self.subTest(template=os.path.basename(path)):
                report = validate(json.load(open(path)), KB)
                self.assertTrue(report["valid"], f"{path}: {report['errors']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
