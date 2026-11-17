#!/usr/bin/env python3
"""Build the reference layer: expressions, environment variables, releases, breaking changes.

The node knowledge base answers "which node and what parameters". It cannot answer "is
`$fromAI()` a thing", "what does N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS do", or "did 3.0 remove
the node I am using". Those live in other parts of the n8n documentation, and this script turns
them into structured JSON.

Sources (all from an n8n-docs clone, all official):
  build/work-with-data/transform-data/expression-reference/*.md   expression reference
  deploy/…/use-environment-variables/*.md                          environment variables
  changelog/release-notes-*.md                                     release notes
  changelog/v*-breaking-changes.md                                 breaking changes

Usage
    python3 tools/build_reference.py
    python3 tools/build_reference.py --docs-repo /path/to/n8n-docs --out knowledge-base/reference
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.environ.get("N8N_DOCS_REPO", os.path.join(ROOT, "vendor", "n8n-docs"))
OUT = os.environ.get("N8N_KB_OUT", os.path.join(ROOT, "knowledge-base"))
REF = os.path.join(OUT, "reference")

ANCHOR_RE = re.compile(r'\s*<a href="#[^"]*" id="[^"]*"></a>')
BOLD_HEAD_RE = re.compile(r"^#{2,4}\s+\*\*`?([^`*]+)`?\*\*")
PLAIN_HEAD_RE = re.compile(r"^(#{2,4})\s+(.*)$")
VAR_ROW_RE = re.compile(r"^\|\s*`([A-Z0-9_]+)`\s*\|")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text: str) -> Dict[str, str]:
    fm: Dict[str, str] = {}
    if not text.startswith("---"):
        return fm
    end = text.find("\n---", 3)
    if end == -1:
        return fm
    for line in text[3:end].split("\n"):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


def clean(text: str) -> str:
    text = ANCHOR_RE.sub("", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def first_paragraph(text: str) -> str:
    """First meaningful paragraph, tolerating the docs' `**Description:**` label style."""
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if not p or p.startswith(("|", ">", "-", "#", "{%")):
            continue
        if p.startswith("**"):
            p = re.sub(r"^\*\*[^*]+\*\*:?\s*", "", p)   # drop the bold label
            if not p:
                continue
        return clean(p)[:400]
    return ""


# ---------------------------------------------------------------- expressions
HEADING_RE = re.compile(r"^(#{2,4})\s+(.*)$")
BOLD_CODE_RE = re.compile(r"\*\*`([^`]+)`\*\*")
ANY_CODE_RE = re.compile(r"`([^`]+)`")
FIELD_RE = re.compile(r"\*\*(Description|Syntax|Returns|Type)\*\*:?\s*(.+)")


def _entry_name(heading: str) -> str:
    """`## _`String`_.**`base64Decode()`**` → base64Decode(); `## **`$json`**` → $json."""
    m = BOLD_CODE_RE.search(heading)
    if m:
        return m.group(1).strip()
    codes = ANY_CODE_RE.findall(heading)
    return codes[-1].strip() if codes else clean(heading)


def _entry_fields(body: List[str]) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in body:
        m = FIELD_RE.match(line.strip())
        if m:
            fields[m.group(1).lower()] = clean(m.group(2))
    if "description" not in fields:
        fallback = first_paragraph("\n".join(body))
        if fallback:
            fields["description"] = fallback
    return fields


def build_expressions() -> List[Dict[str, Any]]:
    base = os.path.join(DOCS, "build", "work-with-data", "transform-data", "expression-reference")
    if not os.path.isdir(base):
        return []
    entries: List[Dict[str, Any]] = []
    seen = set()

    for name in sorted(os.listdir(base)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(base, name)
        text = read(path)
        url = frontmatter(text).get("url") or ""
        section = name[:-3]

        current: Optional[Dict[str, Any]] = None
        buffer: List[str] = []

        def flush():
            if not current:
                return
            fields = _entry_fields(buffer)
            desc = fields.get("description", "")
            key = (current["name"], section)
            # a real entry names a variable, property or method — not a prose heading
            if desc and key not in seen and not re.search(r"\s", current["name"]):
                seen.add(key)
                entry = {"name": current["name"], "section": section,
                         "kind": "function" if "(" in current["name"] else "variable",
                         "description": desc[:400], "doc_url": url}
                for extra in ("syntax", "returns"):
                    if fields.get(extra):
                        entry[extra] = fields[extra][:200]
                entries.append(entry)

        for line in ANCHOR_RE.sub("", text).split("\n"):
            m = HEADING_RE.match(line)
            if m:
                flush()
                heading_name = _entry_name(m.group(2))
                current = {"name": heading_name} if heading_name and not heading_name.lower().startswith(("in this section", "these are")) else None
                buffer = []
                continue
            if current:
                buffer.append(line)
        flush()

        # "| Category | Expression | Description |" tables (the common-expressions page)
        header: Optional[List[str]] = None
        for line in text.split("\n"):
            if not line.strip().startswith("|"):
                header = None if not line.strip() else header
                continue
            cells = [clean(c) for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            lowered = [c.lower() for c in cells]
            if "expression" in lowered:
                header = lowered
                continue
            if header and len(cells) == len(header):
                row = dict(zip(header, cells))
                expr = row.get("expression", "")
                if not expr or not expr.startswith("$"):
                    continue
                key = (expr, section)
                if key in seen:
                    continue
                seen.add(key)
                entries.append({
                    "name": expr, "section": section,
                    "kind": "function" if expr.endswith(")") else "variable",
                    "category": row.get("category") or "",
                    "description": row.get("description", "")[:400], "doc_url": url,
                })

    entries.sort(key=lambda e: (e["section"], e["name"]))
    return entries


# ---------------------------------------------------------------- env vars
def build_env_vars() -> List[Dict[str, Any]]:
    base = os.path.join(DOCS, "deploy", "host-n8n", "configure-n8n", "basic-configuration",
                        "use-environment-variables")
    if not os.path.isdir(base):
        return []
    entries: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(base)):
        if not name.endswith(".md") or name == "README.md":
            continue
        path = os.path.join(base, name)
        text = read(path)
        url = frontmatter(text).get("url") or ""
        category = name[:-3]
        for line in text.split("\n"):
            m = VAR_ROW_RE.match(line.strip())
            if not m:
                continue
            cells = [clean(c) for c in line.strip().strip("|").split("|")]
            entries.append({
                "name": m.group(1),
                "type": cells[1] if len(cells) > 1 else "",
                "default": cells[2] if len(cells) > 2 else "",
                "description": (cells[3] if len(cells) > 3 else "")[:300],
                "category": category,
                "doc_url": url,
            })
    entries.sort(key=lambda e: e["name"])
    return entries


# ---------------------------------------------------------------- releases
def build_releases() -> List[Dict[str, Any]]:
    changelog = os.path.join(DOCS, "changelog")
    if not os.path.isdir(changelog):
        return []
    releases: List[Dict[str, Any]] = []
    for name in ("release-notes-2.x.md", "release-notes-1.x.md"):
        path = os.path.join(changelog, name)
        if not os.path.exists(path):
            continue
        text = read(path)
        url = frontmatter(text).get("url") or ""
        current: Optional[Dict[str, Any]] = None
        buffer: List[str] = []
        for line in ANCHOR_RE.sub("", text).split("\n"):
            m = re.match(r"^##\s+n8n@([0-9]+\.[0-9]+\.[0-9]+[^\s<]*)", line)
            if m:
                if current:
                    releases.append(_finish_release(current, buffer))
                current = {"version": m.group(1), "doc_url": url}
                buffer = []
                continue
            if re.match(r"^##\s+", line):
                if current:
                    releases.append(_finish_release(current, buffer))
                    current = None
                continue
            if current:
                buffer.append(line.strip())
        if current:
            releases.append(_finish_release(current, buffer))
    return releases


def _finish_release(release: Dict[str, Any], buffer: List[str]) -> Dict[str, Any]:
    """Pull the release date and the one-line summary out of a release section."""
    body = "\n".join(buffer)
    date = ""
    m = re.search(r"\*\*Release date:\*\*\s*(\d{4}-\d{2}-\d{2})", body)
    if m:
        date = m.group(1)
    summary = ""
    for para in re.split(r"\n\s*\n", body):
        p = clean(para)
        if not p or p.startswith(("View the commits", "Release date", "For full release")):
            continue
        summary = p[:300]
        break
    bullets = [clean(b) for b in buffer if b.startswith(("- ", "* "))][:6]
    return {**release, "date": date, "summary": summary, "highlights": bullets}


# ---------------------------------------------------------------- breaking changes
def build_breaking() -> List[Dict[str, Any]]:
    changelog = os.path.join(DOCS, "changelog")
    if not os.path.isdir(changelog):
        return []
    out: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(changelog)):
        m = re.match(r"^v(\d)(\d)?-breaking-changes\.md$", name)
        if not m:
            continue
        version = f"{m.group(1)}.{m.group(2) or 0}"
        path = os.path.join(changelog, name)
        text = read(path)
        url = frontmatter(text).get("url") or ""
        category = None
        title = None
        buffer: List[str] = []

        def flush():
            if title:
                detail = first_paragraph("\n".join(buffer))
                out.append({"version": version, "category": category or "General",
                            "title": clean(title), "detail": detail, "doc_url": url})

        for line in ANCHOR_RE.sub("", text).split("\n"):
            if line.startswith("## "):
                flush()
                category, title, buffer = clean(line[3:]), None, []
                continue
            if line.startswith("### "):
                flush()
                title, buffer = line[4:], []
                continue
            if title:
                buffer.append(line)
        flush()
    out.sort(key=lambda c: (c["version"], c["category"], c["title"]))
    return out


# ---------------------------------------------------------------- main
def main():
    global DOCS, OUT, REF
    ap = argparse.ArgumentParser(description="Build the reference layer from an n8n-docs clone.")
    ap.add_argument("--docs-repo", default=DOCS)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    DOCS, OUT = os.path.abspath(args.docs_repo), os.path.abspath(args.out)
    REF = os.path.join(OUT, "reference")
    # accept either the repository root or its docs/ directory
    if os.path.isdir(os.path.join(DOCS, "docs", "changelog")):
        DOCS = os.path.join(DOCS, "docs")
    if not os.path.isdir(DOCS):
        raise SystemExit(f"docs not found at {DOCS}\n"
                         f"clone it: git clone --depth 1 https://github.com/n8n-io/n8n-docs.git")
    os.makedirs(REF, exist_ok=True)

    expressions = build_expressions()
    env_vars = build_env_vars()
    releases = build_releases()
    breaking = build_breaking()

    today = time.strftime("%Y-%m-%d")
    docs = {
        "expressions.json": {
            "generated": today,
            "source": "n8n docs — expression reference",
            "note": "Variables, methods and functions available inside {{ … }} expressions.",
            "count": len(expressions), "entries": expressions},
        "env-vars.json": {
            "generated": today,
            "source": "n8n docs — environment variables",
            "note": "Self-hosting configuration reference.",
            "count": len(env_vars), "entries": env_vars},
        "releases.json": {
            "generated": today,
            "source": "n8n docs — release notes",
            "note": "Version history with the first highlights of each release.",
            "count": len(releases), "releases": releases},
        "breaking-changes.json": {
            "generated": today,
            "source": "n8n docs — breaking changes",
            "note": "What changed between major versions, by category.",
            "count": len(breaking), "changes": breaking},
    }
    for filename, payload in docs.items():
        with open(os.path.join(REF, filename), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1, ensure_ascii=False)

    index = {
        "generated": today,
        "note": "Reference layer: the knowledge the node records cannot carry.",
        "counts": {k.replace(".json", ""): v["count"] for k, v in docs.items()},
        "files": {k: f"reference/{k}" for k in docs},
        "sources": [
            "https://docs.n8n.io/build/work-with-data/transform-data/expression-reference",
            "https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/use-environment-variables",
            "https://docs.n8n.io/changelog/release-notes-2.x",
            "https://docs.n8n.io/changelog/v30-breaking-changes",
        ],
    }
    with open(os.path.join(REF, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1, ensure_ascii=False)
    print(json.dumps(index["counts"], indent=2))


if __name__ == "__main__":
    main()
