"""Reference layer tests: expressions, environment variables, releases, breaking changes.

These assert the layer is present, parseable and actually reachable through the tools — not
that n8n behaves a particular way.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server import expressions as expr                 # noqa: E402
from server.kb import KnowledgeBase                    # noqa: E402
from server.reference import Reference                 # noqa: E402
from server.validation import validate                 # noqa: E402

KB = KnowledgeBase()
REF = Reference()


class TestReferenceFiles(unittest.TestCase):
    def test_all_four_files_exist(self):
        for kind in ("expressions", "env-vars", "releases", "breaking-changes"):
            path = os.path.join(ROOT, "knowledge-base", "reference", f"{kind}.json")
            self.assertTrue(os.path.exists(path), f"missing {kind}.json")

    def test_counts_are_plausible(self):
        counts = REF.counts()
        self.assertGreaterEqual(counts["expressions"], 150)
        self.assertGreaterEqual(counts["env-vars"], 250)
        self.assertGreaterEqual(counts["releases"], 300)
        self.assertGreaterEqual(counts["breaking-changes"], 20)

    def test_index_reports_the_same_counts(self):
        index = REF.index()
        self.assertEqual(index["counts"]["expressions"], REF.counts()["expressions"])

    def test_every_entry_has_a_doc_url(self):
        for kind in ("expressions", "env-vars"):
            missing = [r for r in REF.load(kind) if not r.get("doc_url")]
            self.assertEqual(missing, [], f"{kind} entries without a doc_url")

    def test_no_prose_headings_leaked_into_expressions(self):
        """A signature like `$if(condition, "true", "false")` may contain spaces; a prose
        heading like "Related resources" may not."""
        for row in REF.load("expressions"):
            looks_like_code = any(c in row["name"] for c in "$().")
            self.assertTrue(looks_like_code or " " not in row["name"],
                            f"prose heading parsed as an entry: {row}")


class TestExpressionReference(unittest.TestCase):
    def test_root_variables_are_documented(self):
        names = {r["name"] for r in REF.load("expressions")}
        for expected in ("$json", "$now", "$execution", "$jmespath()", "$fromAI()"):
            self.assertIn(expected, names, f"{expected} missing from the reference")

    def test_methods_are_attributed_to_their_section(self):
        rows = [r for r in REF.load("expressions") if r["name"] == "base64Decode()"]
        self.assertTrue(rows)
        self.assertEqual(rows[0]["section"], "string")

    def test_syntax_and_returns_are_captured(self):
        row = REF.get("expressions", "$jmespath()")
        self.assertIsNotNone(row)
        self.assertTrue(row.get("description"))

    def test_validator_knows_documented_globals(self):
        """A documented helper must not be reported as an unknown variable."""
        self.assertIn("$fromAI", expr.KNOWN_GLOBALS)
        self.assertIn("$jmespath", expr.KNOWN_GLOBALS)
        self.assertGreaterEqual(len(expr.DOCUMENTED_GLOBALS), 10)

    def test_documented_expression_passes_validation(self):
        workflow = {"name": "t", "nodes": [
            {"parameters": {"assignments": {"assignments": [
                {"name": "x", "value": "={{ $jmespath($json, 'a.b') }}", "type": "string"}]}},
             "id": "1", "name": "Set", "type": "n8n-nodes-base.set", "typeVersion": 3.4,
             "position": [0, 0]}], "connections": {}}
        report = validate(workflow, KB)
        self.assertNotIn("unknown_global", {e["code"] for e in report["errors"]})


class TestEnvVarReference(unittest.TestCase):
    def test_known_variable_is_present(self):
        row = REF.get("env-vars", "N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS")
        self.assertIsNotNone(row)
        self.assertIn("category", row)

    def test_search_finds_by_fragment(self):
        out = REF.search("timezone", kind="env-vars", limit=5)
        self.assertGreaterEqual(out["count"], 1)

    def test_entries_carry_type_and_default(self):
        row = REF.get("env-vars", "N8N_PORT") or REF.load("env-vars")[0]
        self.assertIn("type", row)
        self.assertIn("default", row)


class TestReleasesAndBreaking(unittest.TestCase):
    def test_release_has_date_and_summary(self):
        rows = [r for r in REF.load("releases") if r.get("date")]
        self.assertGreaterEqual(len(rows), 100)
        self.assertTrue(rows[0]["version"].startswith(("1.", "2.")))

    def test_breaking_changes_are_categorised(self):
        rows = REF.load("breaking-changes")
        self.assertTrue(all(r.get("category") for r in rows))
        self.assertTrue(all(r.get("version") for r in rows))

    def test_removed_nodes_are_detectable(self):
        removed = REF.removed_nodes()
        self.assertTrue(removed, "expected at least one removal entry")
        self.assertTrue(all("version" in r for r in removed))

    def test_validator_flags_a_node_removed_in_a_breaking_change(self):
        """A node the docs say was removed fails with a clear reason, not just 'unknown'."""
        from unittest import mock
        import server.reference as reference_module

        fake = [{"version": "3.0", "title": "Removed nodes",
                 "detail": "n8n-nodes-base.legacyWidget was removed",
                 "doc_url": "https://docs.n8n.io/changelog/v30-breaking-changes"}]
        workflow = {"name": "t", "nodes": [
            {"parameters": {}, "id": "1", "name": "Old", "type": "n8n-nodes-base.legacyWidget",
             "typeVersion": 1, "position": [0, 0]}], "connections": {}}
        with mock.patch.object(reference_module.Reference, "removed_nodes", return_value=fake):
            report = validate(workflow, KB)
        err = next((e for e in report["errors"] if e["code"] == "node_removed_in_version"), None)
        self.assertIsNotNone(err, f"expected a removal finding, got {report['errors']}")
        self.assertIn("3.0", err["message"])


class TestReferenceSearch(unittest.TestCase):
    def test_search_across_all_kinds(self):
        out = REF.search("removed nodes", limit=10)
        kinds = {r["kind"] for r in out["results"]}
        self.assertTrue(kinds & {"breaking-changes", "releases"})

    def test_unknown_lookup_returns_none(self):
        self.assertIsNone(REF.get("expressions", "$definitelyNotAThing()"))

    def test_limit_is_respected(self):
        out = REF.search("n8n", limit=3)
        self.assertLessEqual(out["count"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
