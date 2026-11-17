"""Catalogue of external MCP servers.

n8n consumes MCP two ways: an MCP Client Tool node calls an outside server, and an MCP Server
Trigger node exposes a workflow as tools. This module answers the first case — what exists, who
listed it, and how much it is actually used.

Two lists, deliberately separate:

  servers                 — from the official reference set or the curated community list
  keyword_only_packages   — npm packages that only *claim* the `mcp-server` keyword

The second list is not endorsed by anyone, so it is excluded unless explicitly requested.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "mcp-servers", "index.json")

TOKEN_RE = re.compile(r"[a-z0-9_.]+")


def _tokens(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if len(t) > 1]


class McpCatalog:
    def __init__(self, path: str = INDEX):
        self.path = path
        self._doc: Optional[dict] = None

    @property
    def doc(self) -> dict:
        if self._doc is None:
            if os.path.exists(self.path):
                with open(self.path, encoding="utf-8") as fh:
                    self._doc = json.load(fh)
            else:
                self._doc = {"servers": [], "keyword_only_packages": [], "counts": {}}
        return self._doc

    def counts(self) -> Dict[str, int]:
        return self.doc.get("counts") or {}

    def categories(self) -> List[Dict[str, Any]]:
        tally: Dict[str, int] = {}
        for row in self.doc.get("servers", []):
            cat = row.get("category") or "Uncategorised"
            tally[cat] = tally.get(cat, 0) + 1
        return [{"category": c, "count": n}
                for c, n in sorted(tally.items(), key=lambda kv: -kv[1])]

    def search(self, query: str = "", category: Optional[str] = None, limit: int = 8,
               include_keyword_only: bool = False, min_downloads: int = 0) -> Dict[str, Any]:
        q = _tokens(query)
        rows = list(self.doc.get("servers", []))
        if include_keyword_only:
            rows += [{**r, "keyword_only": True}
                     for r in self.doc.get("keyword_only_packages", [])]

        hits = []
        for row in rows:
            if category and (row.get("category") or "").lower() != category.lower():
                continue
            downloads = row.get("downloads_last_month") or 0
            if downloads < min_downloads:
                continue
            haystack = " ".join(str(row.get(f, "")) for f in
                                ("name", "description", "category", "repo", "npm_package")).lower()
            if q:
                score = sum(2 if t in haystack else 0 for t in q)
                if not score:
                    continue
                if row.get("name", "").lower() == query.strip().lower():
                    score += 8
                if row.get("repo", "").lower() == query.strip().lower():
                    score += 8
            else:
                score = 0
            hits.append((score, downloads, row))

        hits.sort(key=lambda h: (-h[0], -h[1]))
        results = [{
            "id": r.get("id"),
            "name": r.get("name"),
            "description": (r.get("description") or "")[:240],
            "category": r.get("category"),
            "url": r.get("url"),
            "repo": r.get("repo"),
            "npm_package": r.get("npm_package"),
            "downloads_last_month": r.get("downloads_last_month"),
            "trust": r.get("trust"),
            "sources": r.get("sources"),
            "keyword_only": bool(r.get("keyword_only")),
        } for _s, _d, r in hits[:limit]]

        return {"query": query, "count": len(results), "results": results,
                "counts": self.counts()}

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        want = (name or "").strip().lower()
        if not want:
            return None
        pool = list(self.doc.get("servers", [])) + list(self.doc.get("keyword_only_packages", []))
        for row in pool:
            for field in ("id", "name", "repo", "npm_package"):
                if str(row.get(field) or "").lower() == want:
                    return row
        for row in pool:
            if want in str(row.get("name", "")).lower() or want in str(row.get("repo", "")).lower():
                return row
        return None
