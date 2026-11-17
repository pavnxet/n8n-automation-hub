"""Documentation drift tests.

The README quotes numbers — tools, sources, tests, nodes, servers. Those numbers rot the moment
something ships. `tools/check_docs.py` owns the comparison; this wraps it so the normal test run
catches drift too.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check_docs  # noqa: E402


class TestDocumentation(unittest.TestCase):
    def test_no_number_drift(self):
        state = check_docs.actual_state()
        problems = check_docs.scan(fix=False, state=state)
        self.assertEqual(problems, [], f"documentation drift: {problems}")

    def test_every_doc_file_exists(self):
        for rel in check_docs.DOC_FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_counts_are_discoverable(self):
        state = check_docs.actual_state()
        for key in ("tools", "sources", "nodes", "protocol_checks", "unit_tests"):
            self.assertIsNotNone(state.get(key), key)
            self.assertGreater(state[key], 0, key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
