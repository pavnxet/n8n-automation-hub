"""Reference layer: expressions, environment variables, releases and breaking changes.

The node knowledge base answers "which node, which parameters". This module answers the
questions that sit around it:

  * is `$fromAI()` real, and what does it return?           → expressions
  * what does N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS do?      → env vars
  * which release introduced or removed something?           → releases
  * did 3.0 remove the node this workflow uses?              → breaking changes

All four come from the n8n documentation, parsed by `tools/build_reference.py` into
`knowledge-base/reference/`. Nothing here is generated on the fly: the files are committed, so
answers are reproducible and reviewable.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "knowledge-base", "reference")

KINDS = ("expressions", "env-vars", "releases", "breaking-changes")

TOKEN_RE = re.compile(r"[a-z0-9_$]+")


def _tokens(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if len(t) > 1]


class Reference:
    """Lazy access to the four reference files, with a small ranked search."""

    def __init__(self, base: str = REF):
        self.base = base
        self._cache: Dict[str, List[dict]] = {}

    # ------------------------------------------------------------------ loading
    def load(self, kind: str) -> List[dict]:
        if kind in self._cache:
            return self._cache[kind]
        path = os.path.join(self.base, f"{kind}.json")
        if not os.path.exists(path):
            self._cache[kind] = []
            return []
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        rows = doc.get("entries") or doc.get("releases") or doc.get("changes") or []
        self._cache[kind] = rows
        return rows

    def counts(self) -> Dict[str, int]:
        return {k: len(self.load(k)) for k in KINDS}

    def index(self) -> Dict[str, Any]:
        path = os.path.join(self.base, "index.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        return {"counts": self.counts(), "files": {k: f"reference/{k}.json" for k in KINDS}}

    # ------------------------------------------------------------------ search
    def search(self, query: str, kind: Optional[str] = None, limit: int = 8) -> Dict[str, Any]:
        q = _tokens(query)
        kinds = [kind] if kind in KINDS else list(KINDS)
        hits: List[Dict[str, Any]] = []

        for k in kinds:
            for row in self.load(k):
                haystack = " ".join(str(row.get(f, "")) for f in
                                    ("name", "description", "category", "section", "summary",
                                     "title", "detail", "type", "version"))
                low = haystack.lower()
                if not q:
                    score = 0
                else:
                    score = sum(2 if t in low else 0 for t in q)
                    if q and str(row.get("name", "")).lower() == query.strip().lower():
                        score += 6
                    if score == 0:
                        continue
                hits.append({"kind": k, "score": score, **row})

        hits.sort(key=lambda h: (-h["score"], h["kind"]))
        # keep one row per (kind, name/version) so a repeated entry does not fill the list
        seen, out = set(), []
        for h in hits:
            key = (h["kind"], h.get("name") or h.get("version") or h.get("title"))
            if key in seen:
                continue
            seen.add(key)
            out.append(h)
            if len(out) >= limit:
                break
        return {"query": query, "count": len(out), "results": out}

    # ------------------------------------------------------------------ lookups
    def get(self, kind: str, name: str) -> Optional[Dict[str, Any]]:
        if kind not in KINDS:
            return None
        want = (name or "").strip().lower()
        for row in self.load(kind):
            candidates = [str(row.get(f, "")) for f in ("name", "version", "title")]
            if any(c.lower() == want for c in candidates if c):
                return {"kind": kind, **row}
        for row in self.load(kind):
            blob = " ".join(str(row.get(f, "")) for f in ("name", "version", "title")).lower()
            if want and want in blob:
                return {"kind": kind, **row}
        return None

    # ------------------------------------------------------------------ helpers
    def expression_names(self) -> List[str]:
        """Every `$…` name the docs document, for expression validation."""
        names = set()
        for row in self.load("expressions"):
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            base = re.split(r"[.(]", name)[0]
            if base.startswith("$"):
                names.add(base)
        return sorted(names)

    def removed_nodes(self) -> List[Dict[str, str]]:
        """Breaking-change entries that look like a node removal."""
        out = []
        for row in self.load("breaking-changes"):
            blob = f"{row.get('title','')} {row.get('detail','')}".lower()
            if "removed" in blob and "node" in blob:
                out.append({"version": row.get("version"), "title": row.get("title"),
                            "detail": row.get("detail"), "doc_url": row.get("doc_url")})
        return out
