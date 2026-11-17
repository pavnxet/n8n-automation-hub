#!/usr/bin/env python3
"""Check that the documentation's numbers match the repository.

Docs drift silently: a new tool ships, the README still says twenty. This script reads the
claims out of the Markdown and compares them with the actual state, then fails if they disagree.

Checked claims
  * tool count            "24 tools", "Twenty-four tools"
  * resource count        "7 resources"
  * source count          "20 sources"
  * node / operation / credential counts
  * reference layer counts (expressions, env vars, releases, breaking changes)
  * MCP catalogue counts
  * template count
  * protocol check count  (counted from server/test_server.py)
  * unit test count       (counted from tests/*.py)

Usage
    python3 tools/check_docs.py
    python3 tools/check_docs.py --fix     # rewrite the numbers it knows how to fix
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DOC_FILES = ["README.md", "server/README.md", "docs/mcp-tools.md", "docs/architecture.md",
             "mcp-servers/README.md", "knowledge-base/README.md", "CONTRIBUTING.md"]

WORD_NUMBERS = {
    20: "Twenty", 21: "Twenty-one", 22: "Twenty-two", 23: "Twenty-three", 24: "Twenty-four",
    25: "Twenty-five", 26: "Twenty-six", 27: "Twenty-seven", 28: "Twenty-eight",
    29: "Twenty-nine", 30: "Thirty",
}


def actual_state() -> dict:
    from server.mcp_catalog import McpCatalog
    from server.mcp_server import TOOLS
    from server.reference import Reference

    catalog = json.load(open(os.path.join(ROOT, "knowledge-base", "catalog.json")))
    manifest = json.load(open(os.path.join(ROOT, "knowledge-base", "manifest.json")))
    sources = json.load(open(os.path.join(ROOT, "sources", "sources.json")))["sources"]
    templates = json.load(open(os.path.join(ROOT, "templates", "index.json")))
    ref = Reference().counts()
    mcp = McpCatalog().counts()

    protocol_source = open(os.path.join(ROOT, "server", "test_server.py"), encoding="utf-8").read()
    protocol_checks = len(re.findall(r"^\s*check\(", protocol_source, re.M))

    unit_tests = 0
    for path in glob.glob(os.path.join(ROOT, "tests", "test_*.py")):
        unit_tests += len(re.findall(r"^\s+def test_", open(path, encoding="utf-8").read(), re.M))

    resources = re.findall(r'\("n8n://[^"]+",\s*"[^"]+",',
                           open(os.path.join(ROOT, "server", "mcp_server.py"),
                                encoding="utf-8").read())
    return {
        "tools": len(TOOLS),
        "resources": len(resources),
        "sources": len(sources),
        "nodes": len(catalog["nodes"]),
        "operations": manifest["counts"].get("operations_total"),
        "credentials": manifest["counts"].get("credentials_total"),
        "templates": templates.get("count"),
        "expressions": ref.get("expressions"),
        "env_vars": ref.get("env-vars"),
        "releases": ref.get("releases"),
        "breaking": ref.get("breaking-changes"),
        "mcp_servers": mcp.get("servers"),
        "mcp_official": mcp.get("official"),
        "triggers": len(json.load(open(os.path.join(ROOT, "knowledge-base", "indexes",
                                                    "triggers.json")))["triggers"]),
        "protocol_checks": protocol_checks,
        "unit_tests": unit_tests,
    }


# A number that starts a claim: not glued to a preceding word (`python3 tools/` is not a claim)
# and allowed to carry thousands separators.
NUM = r"(?<![A-Za-z0-9_.,])([\d,]+)"

# (claim regex, state key, human label)
CLAIMS = [
    (NUM + r"\s+tools\b", "tools", "tools"),
    (r"\b(Twenty(?:-\w+)?|Thirty)\s+tools\b", "tools", "tools (words)"),
    (NUM + r"\s+resources\b", "resources", "resources"),
    (NUM + r"\s+sources\b", "sources", "sources"),
    (NUM + r"\s+protocol checks\b", "protocol_checks", "protocol checks"),
    (NUM + r"\s+protocol and tool (?:checks|assertions)\b", "protocol_checks", "protocol checks"),
    (NUM + r"\s+unit(?:, integration)?(?: and regression)? tests\b", "unit_tests", "unit tests"),
    (NUM + r"\s+unit and regression tests\b", "unit_tests", "unit tests"),
    (NUM + r"\s+listed\b", "mcp_servers", "MCP servers listed"),
    (NUM + r"\s+templates\b", "templates", "templates"),
    # only the index description talks about the flag count; the category breakdown elsewhere
    # legitimately says 91, so the phrase is matched narrowly
    (r"All\s+" + NUM + r"\s+trigger nodes", "triggers", "trigger index size"),
    (NUM + r"\s+expressions\b", "expressions", "expressions"),
    (NUM + r"\s+env[ -]vars?\b", "env_vars", "env vars"),
]


def scan(fix: bool, state: dict) -> list:
    problems = []
    for rel in DOC_FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            problems.append((rel, "missing doc file", None, None))
            continue
        text = open(path, encoding="utf-8").read()
        original = text
        for pattern, key, label in CLAIMS:
            expected = state.get(key)
            if expected is None:
                continue
            for m in re.finditer(pattern, text, re.I if "words" in label else 0):
                found = (m.group(1) or "").strip()
                if not found:
                    continue
                if "words" in label:
                    if WORD_NUMBERS.get(expected, "").lower() != found.lower():
                        problems.append((rel, label, found, expected))
                        if fix and WORD_NUMBERS.get(expected):
                            text = text.replace(m.group(0),
                                                f"{WORD_NUMBERS[expected]} tools")
                else:
                    digits = re.sub(r"\D", "", found)
                    if not digits:
                        continue
                    if int(digits) != expected:
                        problems.append((rel, label, found, expected))
                        if fix:
                            text = text.replace(m.group(0), m.group(0).replace(
                                found, str(expected), 1), 1)
        if fix and text != original:
            open(path, "w", encoding="utf-8").write(text)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify documentation numbers against the repo.")
    ap.add_argument("--fix", action="store_true", help="rewrite the numbers in place")
    args = ap.parse_args()

    state = actual_state()
    problems = scan(args.fix, state)

    if not problems:
        print("documentation matches the repository:")
        for k, v in state.items():
            print(f"  {k}: {v}")
        return 0

    print("documentation drift found:")
    for rel, label, found, expected in problems:
        print(f"  {rel}: {label} says {found}, repository has {expected}")
    if args.fix:
        print("\nrewritten; re-run without --fix to confirm")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
