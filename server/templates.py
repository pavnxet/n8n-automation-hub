"""Template library: reusable workflow patterns with honest provenance.

Each entry declares how far it has been verified:

  validated  — passed this repository's static schema validation
  documented — shipped by n8n as an example; not executed here
  executed   — ran successfully against a real instance (nothing here yet)
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INDEX = os.path.join(ROOT, "templates", "index.json")

STATUS_RANK = {"executed": 3, "validated": 2, "documented": 1}


class TemplateLibrary:
    def __init__(self, path: str = INDEX):
        self.path = path
        self._doc: Optional[dict] = None

    @property
    def doc(self) -> dict:
        if self._doc is None:
            self._doc = json.load(open(self.path, encoding="utf-8")) if os.path.exists(self.path) \
                else {"templates": [], "count": 0}
        return self._doc

    @property
    def templates(self) -> List[dict]:
        return self.doc.get("templates", [])

    def search(self, query: str, tag: Optional[str] = None,
               limit: int = 5) -> List[dict]:
        q = [w for w in (query or "").lower().split() if len(w) > 2]
        out = []
        for t in self.templates:
            if tag and tag.lower() not in [x.lower() for x in t.get("tags", [])]:
                continue
            haystack = " ".join([
                t.get("name", ""), t.get("purpose", ""), " ".join(t.get("tags", [])),
                " ".join(t.get("node_types", [])),
            ]).lower()
            score = sum(1 for w in q if w in haystack)
            if q and score == 0:
                continue
            out.append({
                "id": t["id"],
                "name": t.get("name"),
                "purpose": t.get("purpose"),
                "tags": t.get("tags", []),
                "status": t.get("status"),
                "nodes": t.get("nodes"),
                "node_types": t.get("node_types", []),
                "placeholders": t.get("placeholders", []),
                "file": t.get("file"),
                "score": score,
            })
        out.sort(key=lambda r: (-r["score"], -STATUS_RANK.get(r["status"], 0)))
        return out[:limit]

    def get(self, template_id: str) -> Optional[Dict[str, Any]]:
        entry = next((t for t in self.templates if t["id"] == template_id), None)
        if not entry:
            return None
        path = os.path.join(ROOT, entry["file"])
        workflow = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                workflow = json.load(fh)
        return {**entry, "workflow": workflow,
                "verified_note": {
                    "validated": "Passed static schema validation in this repository. Not executed.",
                    "documented": "Published by n8n as an example. Not executed here.",
                    "executed": "Ran successfully against a real instance.",
                }.get(entry.get("status"), "Verification level unknown.")}
