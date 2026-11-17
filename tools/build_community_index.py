#!/usr/bin/env python3
"""Build community-nodes/index.json from the npm registry.

Community nodes are npm packages tagged with the keyword
`n8n-community-node-package` - that keyword is exactly what n8n's
Settings > Community Nodes > Browse searches.

Usage:
    python tools/build_community_index.py [--pages 6] [--downloads 300]

Network: registry.npmjs.org and api.npmjs.org only.
"""
import json, os, sys, time, urllib.parse, urllib.request, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "community-nodes", "index.json")
KEYWORD = "n8n-community-node-package"
UA = {"User-Agent": "n8n-automation-hub-indexer/1.0"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def search(pages, size=250):
    seen, out, total = set(), [], None
    for p in range(pages):
        url = ("https://registry.npmjs.org/-/v1/search?text=keywords:" + KEYWORD +
               f"&size={size}&from={p * size}")
        try:
            d = get(url)
        except Exception as e:
            print(f"  page {p} failed: {e}", file=sys.stderr)
            break
        total = d.get("total", total)
        for o in d.get("objects", []):
            pkg = o.get("package", {})
            name = pkg.get("name")
            kws = pkg.get("keywords") or []
            if not name or name in seen or KEYWORD not in kws:
                continue
            seen.add(name)
            out.append({
                "name": name,
                "version": pkg.get("version"),
                "description": (pkg.get("description") or "").strip()[:300],
                "author": (pkg.get("author") or {}).get("name") if isinstance(pkg.get("author"), dict) else pkg.get("author"),
                "date": pkg.get("date"),
                "links": pkg.get("links") or {},
                "score": round((o.get("score") or {}).get("final", 0), 4),
                "official_scope": name.startswith("@n8n/"),
            })
        time.sleep(0.4)
    return out, total


def downloads(names):
    """Monthly download counts.

    The bulk endpoint rejects scoped packages, so unscoped names are batched
    100 at a time and scoped names are fetched one by one.
    """
    out, plain, scoped = {}, [], []
    for n in names:
        (scoped if n.startswith("@") else plain).append(n)

    for i in range(0, len(plain), 100):
        chunk = plain[i:i + 100]
        url = "https://api.npmjs.org/downloads/point/last-month/" + ",".join(chunk)
        try:
            d = get(url)
        except Exception as e:
            print(f"  downloads batch {i} failed: {e}", file=sys.stderr)
            continue
        for name, v in d.items():
            if isinstance(v, dict) and "downloads" in v:
                out[name] = v["downloads"]
        time.sleep(0.3)

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
    ap.add_argument("--pages", type=int, default=6)
    ap.add_argument("--downloads", type=int, default=300,
                    help="how many of the top results to enrich with download counts")
    a = ap.parse_args()

    print(f"searching npm for keyword:{KEYWORD} ({a.pages} pages)")
    pkgs, total = search(a.pages)
    print(f"  unique packages collected: {len(pkgs)} (npm reports {total} matches)")

    dl = downloads([p["name"] for p in pkgs[:a.downloads]])
    for p in pkgs:
        if p["name"] in dl:
            p["downloads_last_month"] = dl[p["name"]]

    pkgs.sort(key=lambda p: (p.get("downloads_last_month") or 0, p.get("score") or 0), reverse=True)

    doc = {
        "generated": time.strftime("%Y-%m-%d"),
        "source": "https://registry.npmjs.org/-/v1/search?text=keywords:" + KEYWORD,
        "keyword": KEYWORD,
        "note": ("Community nodes are unverified third-party npm packages. n8n's own docs warn they "
                 "have full access to the host and to workflow data. The 'verified' flag below means "
                 "the package is published under the @n8n scope, not that n8n has vetted it - check "
                 "the shield icon in the n8n node panel for verified status."),
        "npm_total_matches": total,
        "collected": len(pkgs),
        "packages": pkgs,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {OUT} ({len(pkgs)} packages)")


if __name__ == "__main__":
    main()
