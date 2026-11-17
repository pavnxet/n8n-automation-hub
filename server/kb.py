"""Data layer for the MCP server: search and lookups over the knowledge base.

Standard library only. Every path is resolved relative to the repository root, so the
server works from a clone with no configuration.

The BM25 scorer is the same one used by tools/search.py — one ranking, two front doors.
"""
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(ROOT, "knowledge-base")
IDX = os.path.join(KB, "indexes")

STOP = set("""a an and are as at be by for from has have how in into is it its of on or that the
this to use used using with you your do does i we my can will not what which who node nodes""".split())


def toks(s):
    return [w for w in re.split(r"[^a-z0-9+#.]+", (s or "").lower())
            if w and w not in STOP and len(w) > 1]


class BM25:
    def __init__(self, docs, k1=1.4, b=0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.tf, self.df, self.lens = [], {}, []
        for d in docs:
            counts = {}
            t = toks(d.get("_text", ""))
            for w in t:
                counts[w] = counts.get(w, 0) + 1
            self.tf.append(counts)
            self.lens.append(len(t))
            for w in counts:
                self.df[w] = self.df.get(w, 0) + 1
        self.N = len(docs)
        self.avg = (sum(self.lens) / self.N) if self.N else 0.0

    def search(self, query, limit=8):
        q = toks(query)
        if not q:
            return []
        scored = []
        for i in range(self.N):
            s = 0.0
            for w in q:
                f = self.tf[i].get(w)
                if not f:
                    continue
                idf = math.log(1 + (self.N - self.df[w] + 0.5) / (self.df[w] + 0.5))
                s += idf * (f * (self.k1 + 1)) / (
                    f + self.k1 * (1 - self.b + self.b * self.lens[i] / (self.avg or 1)))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [(round(s, 3), self.docs[i]) for s, i in scored[:limit]]


class KnowledgeBase:
    """Lazy-loaded indexes. One instance per process."""

    def __init__(self):
        self._ops = None
        self._nodes = None
        self._op_index = None
        self._node_index = None
        self._enums = None
        self._catalog = None

    # ---------------------------------------------------------------- loading
    def _jsonl(self, name):
        path = os.path.join(IDX, name)
        return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]

    @property
    def operations(self):
        if self._ops is None:
            self._ops = self._jsonl("operations.jsonl")
        return self._ops

    @property
    def nodes(self):
        if self._nodes is None:
            self._nodes = self._jsonl("nodes.jsonl")
        return self._nodes

    @property
    def enums(self):
        if self._enums is None:
            path = os.path.join(IDX, "resources-operations.json")
            self._enums = json.load(open(path, encoding="utf-8")).get("nodes", {})
        return self._enums

    @property
    def catalog(self):
        if self._catalog is None:
            self._catalog = json.load(open(os.path.join(KB, "catalog.json"), encoding="utf-8"))
        return self._catalog

    def _op_bm25(self):
        if self._op_index is None:
            docs = []
            for r in self.operations:
                docs.append({
                    "_text": f"{r.get('name','')} {r.get('resource','')} "
                             f"{r.get('operation','')} {r.get('description','')}",
                    **r,
                })
            self._op_index = BM25(docs)
        return self._op_index

    def _node_bm25(self):
        if self._node_index is None:
            docs = []
            for r in self.nodes:
                docs.append({
                    "_text": f"{r.get('name','')} {r.get('id','')} {r.get('desc','')} "
                             f"{' '.join(r.get('ops') or [])}",
                    **r,
                })
            self._node_index = BM25(docs)
        return self._node_index

    # ---------------------------------------------------------------- lookups
    def record_path(self, node_id):
        """Locate nodes/<category>/<id>.json without scanning everything."""
        for cat in ("app-node", "trigger-node", "core-node",
                    "cluster-root-node", "cluster-sub-node"):
            p = os.path.join(KB, "nodes", cat, f"{node_id}.json")
            if os.path.exists(p):
                return p
        for cat in ("app-node", "trigger-node", "core-node",
                    "cluster-root-node", "cluster-sub-node"):
            d = os.path.join(KB, "nodes", cat)
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.lower() == f"{node_id.lower()}.json":
                    return os.path.join(d, f)
        return None

    def record(self, node_id):
        p = self.record_path(node_id)
        if not p:
            return None
        return json.load(open(p, encoding="utf-8"))

    def find_node_id(self, needle):
        """Accept an id, a display name, or a workflow type."""
        needle = (needle or "").strip()
        if not needle:
            return None
        if self.record_path(needle):
            return needle
        low = needle.lower()
        for r in self.nodes:
            if low in (r.get("name", "").lower(), (r.get("type") or "").lower()):
                return r["id"]
        for r in self.nodes:
            if low in r["id"].lower() or low in r.get("name", "").lower():
                return r["id"]
        return None

    # ---------------------------------------------------------------- queries
    def search_operations(self, query, limit=8, category=None, trigger_only=False):
        hits = self._op_bm25().search(query, limit * 4 if (category or trigger_only) else limit)
        out = []
        for score, r in hits:
            if category and r.get("category") != category:
                continue
            if trigger_only and r.get("category") != "trigger-node":
                continue
            out.append({
                "score": score,
                "node": r["node"],
                "workflow_type": r.get("type"),
                "name": r.get("name"),
                "category": r.get("category"),
                "resource": r.get("resource"),
                "operation": r.get("operation"),
                "resource_value": r.get("resource_value"),
                "operation_value": r.get("operation_value"),
                "description": r.get("description"),
                "doc": r.get("doc"),
            })
            if len(out) >= limit:
                break
        return out

    def search_nodes(self, query, limit=8, category=None):
        hits = self._node_bm25().search(query, limit * 3 if category else limit)
        out = []
        for score, r in hits:
            if category and r.get("category") != category:
                continue
            out.append({
                "score": score,
                "id": r["id"],
                "workflow_type": r.get("type"),
                "name": r.get("name"),
                "category": r.get("category"),
                "type_version": r.get("tv"),
                "trigger": r.get("trigger"),
                "ai_tool": r.get("ai_tool"),
                "description": (r.get("desc") or "")[:200],
            })
            if len(out) >= limit:
                break
        return out

    def list_triggers(self, query=None, limit=100):
        rows = [n for n in self.nodes if n.get("trigger")]
        if query:
            q = toks(query)
            rows = [n for n in rows
                    if any(w in toks(f"{n['name']} {n.get('desc','')} {' '.join(n.get('ops') or [])}")
                           for w in q)]
        return [{
            "id": n["id"], "workflow_type": n.get("type"), "name": n["name"],
            "type_version": n.get("tv"), "category": n["category"],
            "description": (n.get("desc") or "")[:160],
        } for n in rows[:limit]]

    def resolve_enum(self, node_id, label=None):
        nid = self.find_node_id(node_id)
        if not nid:
            return {"error": f"unknown node: {node_id}"}
        rec = self.record(nid) or {}
        wt = rec.get("workflow_type") or nid
        table = self.enums.get(wt) or {}
        if not table:
            return {"workflow_type": wt, "has_resource_parameter": False,
                    "note": "this node has no resource/operation dropdowns; "
                            "use its parameters directly"}
        result = {"workflow_type": wt,
                  "has_resource_parameter": table.get("has_resource_parameter", False)}
        if table.get("resources"):
            result["resources"] = table["resources"]
        if table.get("authentication"):
            result["authentication"] = table["authentication"]
        if table.get("operations"):
            result["operations"] = table["operations"]
        if label:
            want = re.sub(r"[^a-z0-9]+", "", label.lower())
            found = []
            for res, ops in (table.get("operations") or {}).items():
                for o in ops:
                    if re.sub(r"[^a-z0-9]+", "", (o.get("name") or "").lower()) == want:
                        found.append({"resource_value": res,
                                      "operation": o.get("name"),
                                      "operation_value": o.get("value")})
            for r in table.get("resources") or []:
                if re.sub(r"[^a-z0-9]+", "", (r.get("name") or "").lower()) == want:
                    found.append({"resource": r.get("name"), "resource_value": r.get("value")})
            result["matched"] = found
        return result

    def guides(self):
        return {
            "n8n://guide/agent": os.path.join(KB, "AGENT-GUIDE.md"),
            "n8n://guide/knowledge-base": os.path.join(KB, "README.md"),
            "n8n://guide/workflow-conventions": os.path.join(ROOT, "docs", "workflow-conventions.md"),
            "n8n://guide/security": os.path.join(ROOT, "SECURITY.md"),
        }

    def read_guide(self, uri):
        path = self.guides().get(uri)
        if not path or not os.path.exists(path):
            return None
        return open(path, encoding="utf-8").read()

    def node_markdown(self, node_id):
        nid = self.find_node_id(node_id)
        if not nid:
            return None
        rec = self.record(nid) or {}
        md = (rec.get("files") or {}).get("markdown")
        if not md:
            return None
        p = os.path.join(KB, md)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None
