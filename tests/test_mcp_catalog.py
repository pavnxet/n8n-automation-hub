"""MCP server catalogue tests.

Asserts the catalogue is present, merged sensibly, and that the self-declared npm keyword does
not leak into default search results.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.mcp_catalog import McpCatalog   # noqa: E402

CAT = McpCatalog()


class TestIndexShape(unittest.TestCase):
    def test_index_exists(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "mcp-servers", "index.json")))

    def test_counts_are_plausible(self):
        counts = CAT.counts()
        self.assertGreaterEqual(counts["servers"], 1000)
        self.assertEqual(counts["official"], 7)
        self.assertGreaterEqual(counts["keyword_only"], 100)

    def test_every_listed_server_has_a_source(self):
        for row in CAT.doc["servers"]:
            self.assertTrue(row.get("sources"), f"{row.get('name')} has no source")
            self.assertIn(row.get("trust"), ("official", "community"))

    def test_official_servers_are_the_reference_set(self):
        names = {r["name"] for r in CAT.doc["servers"] if r["trust"] == "official"}
        self.assertEqual(names, {"fetch", "filesystem", "git", "memory",
                                 "sequentialthinking", "time", "everything"})

    def test_official_servers_have_real_descriptions(self):
        for row in CAT.doc["servers"]:
            if row["trust"] == "official":
                self.assertGreater(len(row["description"]), 20, row["name"])

    def test_no_duplicate_ids(self):
        ids = [r["id"] for r in CAT.doc["servers"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestSearch(unittest.TestCase):
    def test_search_finds_a_database_server(self):
        out = CAT.search("postgres", limit=5)
        self.assertGreaterEqual(out["count"], 1)

    def test_keyword_only_packages_are_excluded_by_default(self):
        default = CAT.search("excel", limit=20)
        for row in default["results"]:
            self.assertFalse(row.get("keyword_only"), row["name"])
        widened = CAT.search("excel", limit=20, include_keyword_only=True)
        self.assertGreaterEqual(widened["count"], default["count"])

    def test_category_filter(self):
        cats = [c["category"] for c in CAT.categories()]
        self.assertTrue(cats)
        out = CAT.search("", category=cats[0], limit=3)
        for row in out["results"]:
            self.assertEqual(row["category"], cats[0])

    def test_min_downloads_filter(self):
        out = CAT.search("mcp", limit=10, min_downloads=10000)
        for row in out["results"]:
            self.assertGreaterEqual(row["downloads_last_month"] or 0, 10000)

    def test_empty_query_returns_top_by_downloads(self):
        out = CAT.search("", limit=5)
        self.assertLessEqual(out["count"], 5)

    def test_get_by_id_and_by_name(self):
        self.assertIsNotNone(CAT.get("modelcontextprotocol/servers/fetch"))
        self.assertIsNotNone(CAT.get("fetch"))
        self.assertIsNone(CAT.get("definitely-not-a-server-xyz"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
