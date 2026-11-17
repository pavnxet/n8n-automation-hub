"""Search regression benchmark.

Every query below is a real phrasing an agent or a person would use. Each has an expected node
type; the benchmark reports top-1 accuracy, top-3 accuracy, false positives (a result whose
confidence is high but whose node is not the expected one) and latency.

Run:
    python3 -m unittest tests.test_search_benchmark -v
    python3 tests/test_search_benchmark.py          # prints the table and metrics
"""
import json
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.kb import KnowledgeBase          # noqa: E402
from server.search import SearchEngine       # noqa: E402

KB = KnowledgeBase()
SE = SearchEngine(KB)

# (query, expected workflow_type, allow_top3)
CASES = [
    # --- core nodes: the original failures first
    ("HTTP Request GET JSON API", "n8n-nodes-base.httpRequest", False),
    ("Filter items based on conditions", "n8n-nodes-base.filter", False),
    ("Schedule Trigger", "n8n-nodes-base.scheduleTrigger", False),
    ("Fetch information from a REST API", "n8n-nodes-base.httpRequest", False),
    ("make an http call to an endpoint", "n8n-nodes-base.httpRequest", False),
    ("call an api and get json back", "n8n-nodes-base.httpRequest", False),
    ("if condition branch", "n8n-nodes-base.if", False),
    ("switch between multiple branches", "n8n-nodes-base.switch", False),
    ("merge two branches together", "n8n-nodes-base.merge", False),
    ("remove duplicates from the list", "n8n-nodes-base.removeDuplicates", False),
    ("split out an array into items", "n8n-nodes-base.splitOut", False),
    ("loop over items in batches", "n8n-nodes-base.splitInBatches", False),
    ("iterate over every item", "n8n-nodes-base.splitInBatches", True),
    ("wait for 5 seconds", "n8n-nodes-base.wait", False),
    ("edit fields and rename a property", "n8n-nodes-base.set", False),
    ("run custom javascript code", "n8n-nodes-base.code", False),
    ("aggregate items into one", "n8n-nodes-base.aggregate", False),
    ("sort items by date", "n8n-nodes-base.sort", False),
    ("limit to the first 10 items", "n8n-nodes-base.limit", False),
    ("parse a csv file", "n8n-nodes-base.extractFromFile", True),
    ("format a date and add days", "n8n-nodes-base.dateTime", False),
    # --- triggers
    ("run every morning at 8 AM", "n8n-nodes-base.scheduleTrigger", False),
    ("every day at 9am", "n8n-nodes-base.scheduleTrigger", False),
    ("receive an incoming webhook", "n8n-nodes-base.webhook", False),
    ("webhook trigger for a post request", "n8n-nodes-base.webhook", False),
    ("when a form is submitted", "n8n-nodes-base.formTrigger", True),
    ("on workflow error send an alert", "n8n-nodes-base.errorTrigger", True),
    ("when a new message arrives in telegram", "n8n-nodes-base.telegramTrigger", True),
    ("when a new row appears in google sheets", "n8n-nodes-base.googleSheetsTrigger", True),
    # --- app nodes
    ("Telegram Send Message", "n8n-nodes-base.telegram", False),
    ("send a telegram message to a chat", "n8n-nodes-base.telegram", False),
    ("post a message to slack", "n8n-nodes-base.slack", False),
    ("append row to google sheet", "n8n-nodes-base.googleSheets", False),
    ("read rows from a spreadsheet", "n8n-nodes-base.googleSheets", True),
    ("query a postgres database", "n8n-nodes-base.postgres", False),
    ("insert a record into postgres", "n8n-nodes-base.postgres", False),
    ("send an email with gmail", "n8n-nodes-base.gmail", False),
    ("create a record in airtable", "n8n-nodes-base.airtable", False),
    ("add a page to notion", "n8n-nodes-base.notion", False),
    ("create a hubspot contact", "n8n-nodes-base.hubspot", False),
    ("send a whatsapp message", "n8n-nodes-base.whatsApp", True),
    ("ask an ai agent to answer", "@n8n/n8n-nodes-langchain.agent", True),
    ("upload a file to google drive", "n8n-nodes-base.googleDrive", True),
    ("run a shell command", "n8n-nodes-base.executeCommand", True),
    # --- capability phrasing with no node name in it
    ("turn a json payload into csv", "n8n-nodes-base.convertToFile", True),
    ("deduplicate records we have seen before", "n8n-nodes-base.removeDuplicates", True),
    ("notify me on telegram when something fails", "n8n-nodes-base.telegram", True),
]


def run_benchmark(verbose=False):
    rows = []
    for query, expected, allow_top3 in CASES:
        started = time.perf_counter()
        res = SE.search(query, limit=3)
        elapsed_ms = (time.perf_counter() - started) * 1000
        results = res.get("results") or []
        top = results[0]["workflow_type"] if results else None
        top3 = [r["workflow_type"] for r in results]
        hit1 = top == expected
        hit3 = expected in top3
        # a confident result for the wrong node is worse than a low-confidence guess
        false_positive = bool(results) and not hit3 and results[0]["confidence"] >= 0.6
        rows.append({
            "query": query, "expected": expected, "top1": top,
            "hit1": hit1, "hit3": hit3, "false_positive": false_positive,
            "confidence": results[0]["confidence"] if results else 0.0,
            "ms": round(elapsed_ms, 2),
        })
        if verbose:
            mark = "OK " if hit1 else ("TOP3" if hit3 else "MISS")
            print(f"{mark:5} {query[:46]:46} -> {str(top):38} conf="
                  f"{rows[-1]['confidence']:.2f} {elapsed_ms:5.1f}ms")

    n = len(rows)
    metrics = {
        "queries": n,
        "top1_accuracy": round(sum(r["hit1"] for r in rows) / n, 3),
        "top3_accuracy": round(sum(r["hit3"] for r in rows) / n, 3),
        "false_positive_rate": round(sum(r["false_positive"] for r in rows) / n, 3),
        "mean_latency_ms": round(sum(r["ms"] for r in rows) / n, 2),
        "p95_latency_ms": round(sorted(r["ms"] for r in rows)[int(n * 0.95) - 1], 2),
        "misses": [r["query"] for r in rows if not r["hit3"]],
        "top1_misses": [r["query"] for r in rows if not r["hit1"]],
    }
    return rows, metrics


class TestSearchBenchmark(unittest.TestCase):
    """Thresholds are deliberately a little below the measured values, so a genuine
    regression fails while wording changes do not."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.metrics = run_benchmark()

    def test_at_least_30_queries(self):
        self.assertGreaterEqual(self.metrics["queries"], 30)

    def test_top1_accuracy(self):
        self.assertGreaterEqual(self.metrics["top1_accuracy"], 0.70,
                                f"top-1 too low: {self.metrics['top1_misses']}")

    def test_top3_accuracy(self):
        self.assertGreaterEqual(self.metrics["top3_accuracy"], 0.88,
                                f"top-3 too low: {self.metrics['misses']}")

    def test_no_confident_false_positives(self):
        self.assertLessEqual(self.metrics["false_positive_rate"], 0.05)

    def test_latency(self):
        self.assertLess(self.metrics["mean_latency_ms"], 250,
                        "search should stay well under a quarter second per query")

    def test_original_regressions(self):
        """The three failures from the first version must stay fixed."""
        for query, expected in [("HTTP Request GET JSON API", "n8n-nodes-base.httpRequest"),
                                ("Filter items based on conditions", "n8n-nodes-base.filter"),
                                ("Schedule Trigger", "n8n-nodes-base.scheduleTrigger")]:
            res = SE.search(query, limit=3)
            self.assertEqual(res["results"][0]["workflow_type"], expected, query)

    def test_results_explain_themselves(self):
        res = SE.search("append row to google sheet", limit=2)
        top = res["results"][0]
        for key in ("name", "workflow_type", "category", "type_version", "confidence",
                    "confidence_band", "match", "why"):
            self.assertIn(key, top)
        self.assertTrue(top["why"])

    def test_operation_values_are_surfaced(self):
        res = SE.search_operations("append row to google sheet", limit=3)
        rows = [r for r in res["results"] if r.get("operation")]
        self.assertTrue(rows, "expected an operation-level result")
        self.assertEqual(rows[0]["operation"]["operation_value"], "append")

    def test_no_padding_with_irrelevant_results(self):
        res = SE.search("zzzz nonexistent capability qqqq", limit=8)
        for r in res["results"]:
            self.assertGreaterEqual(r["confidence"], 0.28)


if __name__ == "__main__":
    rows, metrics = run_benchmark(verbose=True)
    print("\n" + json.dumps(metrics, indent=2))
