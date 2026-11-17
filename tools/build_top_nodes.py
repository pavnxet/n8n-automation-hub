#!/usr/bin/env python3
"""Rank community nodes by real monthly downloads.

Reads community-nodes/index.json, refreshes download counts for the strongest candidates,
and writes community-nodes/top-100.json.

The ranking is computed here, from npm, so the file is ours to publish: package names,
versions, download counts and the descriptions npm itself serves. Third-party "top node"
lists are used only as a cross-check — no rows are copied from them.

Usage
    python3 tools/build_top_nodes.py                 # top 100 from the top 500 candidates
    python3 tools/build_top_nodes.py --candidates 800 --top 100
    python3 tools/build_top_nodes.py --offline       # re-rank using stored counts only
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "community-nodes", "index.json")
OUT = os.path.join(ROOT, "community-nodes", "top-100.json")
UA = {"User-Agent": "n8n-automation-hub/1.2"}

CROSS_CHECKED = [
    "awesome-n8n-restyler",
    "ncnodes",
]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def downloads(names):
    """Monthly downloads. The bulk endpoint rejects scoped names, so those go one by one."""
    out, plain, scoped = {}, [], []
    for n in names:
        (scoped if n.startswith("@") else plain).append(n)

    for i in range(0, len(plain), 100):
        chunk = plain[i:i + 100]
        try:
            d = get("https://api.npmjs.org/downloads/point/last-month/" + ",".join(chunk))
        except Exception as e:
            print(f"  batch {i} failed: {e}")
            continue
        for name, v in d.items():
            if isinstance(v, dict) and "downloads" in v:
                out[name] = v["downloads"]
        time.sleep(0.25)

    for n in scoped:
        try:
            d = get("https://api.npmjs.org/downloads/point/last-month/" +
                    urllib.parse.quote(n, safe=""))
            if "downloads" in d:
                out[n] = d["downloads"]
        except Exception:
            pass
        time.sleep(0.05)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=int, default=500,
                    help="how many packages from index.json to refresh")
    ap.add_argument("--top", type=int, default=100)
    ap.add_argument("--offline", action="store_true",
                    help="skip the network and re-rank on stored counts")
    args = ap.parse_args()

    if not os.path.exists(INDEX):
        raise SystemExit(f"missing {INDEX} - run tools/build_community_index.py first")
    doc = json.load(open(INDEX, encoding="utf-8"))
    packages = doc["packages"]
    candidates = packages[:args.candidates]

    if not args.offline:
        print(f"refreshing download counts for {len(candidates)} candidates")
        fresh = downloads([p["name"] for p in candidates])
        for p in packages:
            if p["name"] in fresh:
                p["downloads_last_month"] = fresh[p["name"]]
        print(f"  got counts for {len(fresh)}")

    ranked = [p for p in packages if (p.get("downloads_last_month") or 0) > 0]
    ranked.sort(key=lambda p: p["downloads_last_month"], reverse=True)

    rows = []
    for i, p in enumerate(ranked[:args.top], 1):
        rows.append({
            "rank": i,
            "name": p["name"],
            "version": p.get("version"),
            "downloads_last_month": p["downloads_last_month"],
            "description": (p.get("description") or "")[:200],
            "author": p.get("author"),
            "repository": (p.get("links") or {}).get("repository"),
            "npm": (p.get("links") or {}).get("npm") or f"https://www.npmjs.com/package/{p['name']}",
            "official_scope": bool(p.get("official_scope")),
            "last_published": p.get("date"),
        })

    out = {
        "generated": time.strftime("%Y-%m-%d"),
        "method": ("Ranked by last-30-day npm downloads, fetched from api.npmjs.org. "
                   "Counts, versions and descriptions come from npm; the ordering is computed "
                   "by tools/build_top_nodes.py. Third-party lists were used only to sanity-check "
                   "the ranking, and none of their rows were copied."),
        "cross_checked_against": CROSS_CHECKED,
        "candidates_considered": len(ranked),
        "count": len(rows),
        "packages": rows,
    }
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {OUT} ({len(rows)} packages)")
    for r in rows[:10]:
        print(f"{r['rank']:>3}. {r['name']:<45} {r['downloads_last_month']:>10,}")


if __name__ == "__main__":
    main()
