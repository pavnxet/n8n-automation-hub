"""Planner, generator and template-library tests.

Generation is checked the only way that matters statically: the produced JSON must pass the
same validator the agent will run, with no errors.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.generator import generate          # noqa: E402
from server.kb import KnowledgeBase            # noqa: E402
from server.planner import plan                # noqa: E402
from server.search import SearchEngine         # noqa: E402
from server.templates import TemplateLibrary   # noqa: E402
from server.validation import validate         # noqa: E402

KB = KnowledgeBase()
SE = SearchEngine(KB)


class TestPlanner(unittest.TestCase):
    def test_complex_request_produces_a_plan(self):
        p = plan("Get Hacker News stories, filter out previously processed stories, summarize "
                 "new stories using an API, save them to a database, and send the results to "
                 "Telegram.", KB, SE)
        self.assertIn("trigger", p)
        self.assertGreaterEqual(len(p["steps"]), 4)
        types = [s["node_type"] for s in p["steps"]]
        self.assertIn("n8n-nodes-base.telegram", types)
        self.assertIn("n8n-nodes-base.httpRequest", types)
        # every step must name a real node
        for s in p["steps"]:
            self.assertIsNotNone(KB.record_by_type(s["node_type"]), s["node_type"])

    def test_dedupe_is_not_a_filter_node(self):
        p = plan("filter out previously processed stories and save them", KB, SE)
        types = [s["node_type"] for s in p["steps"]]
        self.assertIn("n8n-nodes-base.removeDuplicates", types,
                      "cross-run dedupe needs Remove Duplicates, not Filter")

    def test_schedule_request_sets_a_time_hint(self):
        p = plan("Run every morning at 8 AM and post the weather to Slack", KB, SE)
        self.assertEqual(p["trigger"]["node_type"], "n8n-nodes-base.scheduleTrigger")
        hint = p["trigger"].get("parameter_hint") or {}
        self.assertEqual(hint.get("triggerAtHour"), 8)

    def test_app_event_uses_that_apps_trigger(self):
        p = plan("When a new row appears in Google Sheets, send it to Telegram", KB, SE)
        self.assertEqual(p["trigger"]["node_type"], "n8n-nodes-base.googleSheetsTrigger")
        types = [s["node_type"] for s in p["steps"]]
        self.assertNotIn("n8n-nodes-base.googleSheets", types,
                         "the trigger already covers the read")
        self.assertIn("n8n-nodes-base.telegram", types)

    def test_unknown_capability_becomes_an_open_question(self):
        p = plan("summarize the article using an API", KB, SE)
        self.assertTrue(p["open_questions"])
        self.assertIn("n8n-nodes-base.httpRequest", [s["node_type"] for s in p["steps"]])

    def test_no_invented_nodes(self):
        p = plan("Send a fax with telepathy and then update my brain", KB, SE)
        for s in p["steps"]:
            self.assertIsNotNone(KB.record_by_type(s["node_type"]))


class TestGenerator(unittest.TestCase):
    def _assert_importable(self, out):
        self.assertTrue(out.get("importable"),
                        f"not importable: {out.get('validation', {}).get('errors')}")
        self.assertFalse(out["validation"]["errors"])
        wf = out["workflow"]
        names = [n["name"] for n in wf["nodes"]]
        self.assertEqual(len(names), len(set(names)), "node names must be unique")
        for n in wf["nodes"]:
            self.assertIn("typeVersion", n)
            self.assertIsNotNone(KB.record_by_type(n["type"]) or
                                 n["type"] == "n8n-nodes-base.stickyNote", n["type"])
        # every connection points at a real node
        for src, outputs in wf["connections"].items():
            self.assertIn(src, names)
            for branches in outputs.values():
                for branch in branches:
                    for target in branch:
                        self.assertIn(target["node"], names)
        return wf

    def test_two_node_workflow(self):
        out = generate(request="Every day at 9am post a message to Slack", kb=KB, se=SE)
        wf = self._assert_importable(out)
        self.assertGreaterEqual(len(wf["nodes"]), 2)

    def test_scheduled_api_workflow(self):
        out = generate(request="Every morning at 8 fetch the weather for Delhi from an API and "
                               "post it to Slack", kb=KB, se=SE)
        wf = self._assert_importable(out)
        types = [n["type"] for n in wf["nodes"]]
        self.assertIn("n8n-nodes-base.scheduleTrigger", types)
        self.assertIn("n8n-nodes-base.httpRequest", types)
        trigger = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.scheduleTrigger")
        self.assertEqual(trigger["parameters"]["rule"]["interval"][0]["triggerAtHour"], 8)

    def test_api_to_database_workflow(self):
        out = generate(request="Every day fetch a paginated API and save the records to Postgres",
                       kb=KB, se=SE)
        wf = self._assert_importable(out)
        self.assertIn("n8n-nodes-base.postgres", [n["type"] for n in wf["nodes"]])

    def test_database_to_telegram_workflow(self):
        out = generate(request="When a new row appears in Google Sheets, save it to Postgres and "
                               "send a Telegram message", kb=KB, se=SE)
        wf = self._assert_importable(out)
        types = [n["type"] for n in wf["nodes"]]
        self.assertIn("n8n-nodes-base.telegram", types)

    def test_workflow_with_expressions(self):
        out = generate(request="When a new row appears in Google Sheets, send it to Telegram",
                       kb=KB, se=SE)
        self._assert_importable(out)

    def test_placeholders_are_marked_not_invented(self):
        out = generate(request="Every day call an API", kb=KB, se=SE)
        self._assert_importable(out)
        self.assertTrue(out["placeholders"], "a required URL should be a marked placeholder")
        url_ph = [p for p in out["placeholders"] if p["parameter"] == "url"]
        self.assertTrue(url_ph)
        self.assertIn("example.com", str(url_ph[0]["value"]))

    def test_no_credentials_are_fabricated(self):
        out = generate(request="Every day post a message to Slack", kb=KB, se=SE)
        self._assert_importable(out)
        blob = json.dumps(out["workflow"])
        for marker in ("xoxb-", "sk-", "Bearer "):
            self.assertNotIn(marker, blob)

    def test_generated_workflow_declares_it_was_not_executed(self):
        out = generate(request="Every day at 9am post a message to Slack", kb=KB, se=SE)
        self.assertFalse(out["executed"])
        self.assertIn("not been executed", out["note"])

    def test_sticky_note_documents_credentials(self):
        out = generate(request="Every day post a message to Slack", kb=KB, se=SE)
        note = next(n for n in out["workflow"]["nodes"]
                    if n["type"] == "n8n-nodes-base.stickyNote")
        self.assertIn("Credentials", note["parameters"]["content"])

    def test_generate_from_plan(self):
        p = plan("Every day at 9am post a message to Slack", KB, SE)
        out = generate(plan=p, kb=KB, se=SE)
        self._assert_importable(out)


class TestTemplates(unittest.TestCase):
    def setUp(self):
        self.lib = TemplateLibrary()

    def test_index_loads(self):
        self.assertGreaterEqual(len(self.lib.templates), 5)

    def test_search_by_tag(self):
        rows = self.lib.search("", tag="pagination")
        self.assertTrue(rows)

    def test_get_returns_workflow(self):
        entry = self.lib.templates[0]
        t = self.lib.get(entry["id"])
        self.assertIsNotNone(t["workflow"])
        self.assertIn("verified_note", t)

    def test_every_template_workflow_validates(self):
        for entry in self.lib.templates:
            t = self.lib.get(entry["id"])
            if t.get("status") == "documented":
                continue  # shipped by n8n; may use nodes newer than this snapshot
            with self.subTest(template=entry["id"]):
                report = validate(t["workflow"], KB)
                self.assertTrue(report["valid"], f"{entry['id']}: {report['errors']}")

    def test_status_vocabulary_is_honest(self):
        for entry in self.lib.templates:
            self.assertIn(entry["status"], ("validated", "documented", "executed"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
