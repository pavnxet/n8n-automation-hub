#!/usr/bin/env python3
"""BM25 search over the n8n node knowledge base. Standard library only.

Usage:
    python tools/search.py "send whatsapp message"
    python tools/search.py "append row" --ops            # search operations only
    python tools/search.py "gmail" --category app-node --limit 5
    python tools/search.py "ai agent" --json             # machine readable

Run from the KB root (the folder containing catalog.json).
"""
import sys, os, json, math, re, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "indexes")
STOP = set("""a an and are as at be by for from has have how in into is it its of on or that the
this to use used using with you your the do does i we my can will not what which who node nodes""".split())


def toks(s):
    return [w for w in re.split(r"[^a-z0-9+#.]+", (s or "").lower()) if w and w not in STOP and len(w) > 1]


class BM25:
    def __init__(self, docs, k1=1.4, b=0.75):
        self.docs = docs
        self.k1, self.b = k1, b
        self.tf, self.df, self.len = [], {}, []
        for d in docs:
            t = toks(d["_text"])
            counts = {}
            for w in t:
                counts[w] = counts.get(w, 0) + 1
            self.tf.append(counts)
            self.len.append(len(t))
            for w in counts:
                self.df[w] = self.df.get(w, 0) + 1
        self.N = len(docs)
        self.avg = (sum(self.len) / self.N) if self.N else 0

    def search(self, query, limit=10):
        q = toks(query)
        if not q:
            return []
        scored = []
        for i, d in enumerate(self.docs):
            s = 0.0
            for w in q:
                if w not in self.tf[i]:
                    continue
                idf = math.log(1 + (self.N - self.df[w] + 0.5) / (self.df[w] + 0.5))
                f = self.tf[i][w]
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            if s > 0:
                scored.append((s, i))
        scored.sort(reverse=True)
        return [(round(s, 2), self.docs[i]) for s, i in scored[:limit]]


def load_jsonl(name):
    p = os.path.join(IDX, name)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="+")
    ap.add_argument("--ops", action="store_true", help="search the operation index")
    ap.add_argument("--category", default="")
    ap.add_argument("--trigger", action="store_true", help="only trigger nodes")
    ap.add_argument("--ai-tool", action="store_true", help="only nodes usable as AI tools")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    query = " ".join(a.query)

    if a.ops:
        rows = load_jsonl("operations.jsonl")
        docs = [{"_text": f"{r['name']} {r['resource']} {r['operation']} {r['description']}", **r}
                for r in rows]
        hits = BM25(docs).search(query, a.limit)
        if a.json:
            print(json.dumps([{"score": s, **{k: v for k, v in d.items() if k != "_text"}} for s, d in hits], indent=2))
            return
        for s, d in hits:
            op = f"{d['resource']} / {d['operation']}" if d["resource"] else d["operation"]
            vals = ""
            if d.get("resource_value") or d.get("operation_value"):
                vals = f"   [{d.get('resource_value') or ''}.{d.get('operation_value') or ''}]"
            print(f"{s:6.2f}  {d['node']:45s} {op}{vals}")
            if d["description"]:
                print(f"        {d['description'][:120]}")
        return

    rows = load_jsonl("nodes.jsonl")
    if a.category:
        rows = [r for r in rows if r["category"] == a.category]
    if a.trigger:
        rows = [r for r in rows if r["trigger"]]
    if a.ai_tool:
        rows = [r for r in rows if r["ai_tool"]]
    docs = [{"_text": f"{r['name']} {r['id']} {r.get('type','')} {r['category']} {r['desc']} {' '.join(r['ops'])}", **r}
            for r in rows]
    hits = BM25(docs).search(query, a.limit)
    if a.json:
        print(json.dumps([{"score": s, **{k: v for k, v in d.items() if k != "_text"}} for s, d in hits], indent=2))
        return
    for s, d in hits:
        flags = "".join(["T" if d["trigger"] else "-", "A" if d["ai_tool"] else "-"])
        print(f"{s:6.2f}  [{flags}] {d['name']}  ({d.get('type') or d['id']}, {d['category']}, tv {d.get('tv')})")
        print(f"        {d['desc'][:150]}")
        if d["ops"]:
            print(f"        ops: {', '.join(d['ops'][:8])}")
        print(f"        json: nodes/{d['category']}/{d['id']}.json")


if __name__ == "__main__":
    main()
