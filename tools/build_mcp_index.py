#!/usr/bin/env python3
"""Build the MCP server index.

n8n can consume MCP servers two ways: an **MCP Client Tool** node attached to an AI Agent, or an
**MCP Server Trigger** node exposing a workflow as tools. Both need a catalogue of servers to
choose from, and n8n's own docs do not provide one. This script builds it from three sources:

  1. `modelcontextprotocol/servers`      — the official reference servers (highest trust)
  2. `punkpeye/awesome-mcp-servers`      — the largest curated community list (~5k entries)
  3. npm, keyword `mcp-server`           — what is actually published and downloaded

Entries are merged by repository slug so one server appears once, with every source that listed
it and its npm download count when it has one.

Usage
    git clone --depth 1 https://github.com/modelcontextprotocol/servers.git
    git clone --depth 1 https://github.com/punkpeye/awesome-mcp-servers.git
    python3 tools/build_mcp_index.py --official ./servers --curated ./awesome-mcp-servers
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mcp-servers", "index.json")
KEYWORD = "mcp-server"
UA = {"User-Agent": "n8n-automation-hub/1.5"}

LANG_FLAGS = {
    "🐍": "python", "📇": "typescript", "🏎️": "go", "🦀": "rust", "☕": "java",
    "💎": "ruby", "🎖️": "official", "📟": "cli", "#️⃣": "csharp", "🌊": "php",
    "🏗️": "build", "🔗": "aggregator", "🍎": "macos", "🪟": "windows", "🐧": "linux",
}

BADGE_RE = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")
LINK_RE = re.compile(r"^- \[([^\]]+)\]\((https?://[^)]+)\)\s*(.*)$")
CATEGORY_RE = re.compile(r"^###\s*(?:[^\w<]*)?(?:<a name=\"[^\"]+\"></a>)?\s*(.+?)\s*$")


def fetch_json(url: str, timeout: int = 40) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ! {url}: {e}")
        return None


def repo_slug(url: str) -> Optional[str]:
    """github.com/owner/repo → owner/repo (lowercased)."""
    if not url:
        return None
    m = re.search(r"github\.com[/:]([^/]+)/([^/#?]+)", url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}".lower()


OFFICIAL_FALLBACK = {
    "fetch": "Fetches a URL and converts the page to markdown for the model.",
    "filesystem": "Secure file operations with configurable access controls.",
    "git": "Tools to read, search and manipulate git repositories.",
    "memory": "Persistent memory using a local knowledge graph.",
    "sequentialthinking": "Dynamic, reflective problem solving through thought sequences.",
    "time": "Time and timezone conversion capabilities.",
    "everything": "Reference server that exercises every MCP feature (prompts, tools, resources).",
}


def clean_description(text: str) -> str:
    text = BADGE_RE.sub("", text)
    for flag in LANG_FLAGS:
        text = text.replace(flag, "")
    text = re.sub(r"\[!\[[^\]]*\]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)   # keep link text, drop the URL
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip(" -—|")


# ---------------------------------------------------------------- official
def build_official(path: str) -> List[Dict[str, Any]]:
    src = os.path.join(path, "src")
    if not os.path.isdir(src):
        return []
    out = []
    for name in sorted(os.listdir(src)):
        readme = os.path.join(src, name, "README.md")
        description = ""
        if os.path.exists(readme):
            with open(readme, encoding="utf-8") as fh:
                text = fh.read()
            body = re.sub(r"^#.*$", "", text, count=1, flags=re.M).strip()
            para = next((p.strip() for p in re.split(r"\n\s*\n", body)
                         if p.strip() and not p.strip().startswith(("#", "[", ">", "|"))), "")
            description = clean_description(para)[:400]
            if (len(description) < 25 or description.count("(") > 3
                    or "|" in description or description.startswith("**")):
                description = OFFICIAL_FALLBACK.get(name, description)
        out.append({
            "id": f"modelcontextprotocol/servers/{name}",
            "name": name,
            "repo": "modelcontextprotocol/servers",
            "url": f"https://github.com/modelcontextprotocol/servers/tree/main/src/{name}",
            "description": description,
            "category": "official-reference",
            "sources": ["modelcontextprotocol/servers"],
            "trust": "official",
        })
    return out


# ---------------------------------------------------------------- curated list
def build_curated(path: str) -> List[Dict[str, Any]]:
    readme = os.path.join(path, "README.md")
    if not os.path.exists(readme):
        return []
    out: List[Dict[str, Any]] = []
    category = "Uncategorised"
    with open(readme, encoding="utf-8") as fh:
        for line in fh:
            m = CATEGORY_RE.match(line.strip())
            if m and not line.strip().startswith("###  "):
                candidate = clean_description(m.group(1))
                if candidate and len(candidate) < 80:
                    category = candidate
                continue
            entry = LINK_RE.match(line.strip())
            if not entry:
                continue
            name, url, rest = entry.groups()
            if "glama.ai/mcp/servers" in url and "github.com" not in url:
                continue
            description = clean_description(rest)
            if not description:
                continue
            languages = [lang for flag, lang in LANG_FLAGS.items() if flag in rest]
            out.append({
                "id": (repo_slug(url) or name).lower(),
                "name": name,
                "repo": repo_slug(url),
                "url": url,
                "description": description[:400],
                "category": category,
                "languages": sorted(set(languages)),
                "sources": ["punkpeye/awesome-mcp-servers"],
                "trust": "community",
            })
    return out


# ---------------------------------------------------------------- npm
def build_npm(pages: int, enrich: int) -> List[Dict[str, Any]]:
    seen, out = set(), []
    for page in range(pages):
        data = fetch_json("https://registry.npmjs.org/-/v1/search?"
                          f"text=keywords:{KEYWORD}&size=250&from={page * 250}")
        if not data:
            break
        for obj in data.get("objects", []):
            pkg = obj.get("package", {})
            name = pkg.get("name")
            keywords = pkg.get("keywords") or []
            if not name or name in seen or KEYWORD not in keywords:
                continue
            seen.add(name)
            links = pkg.get("links") or {}
            out.append({
                "package": name,
                "version": pkg.get("version"),
                "description": (pkg.get("description") or "")[:300],
                "repo": repo_slug(links.get("repository") or ""),
                "url": links.get("npm") or f"https://www.npmjs.com/package/{name}",
                "date": pkg.get("date"),
            })
        time.sleep(0.3)
    print(f"  npm packages: {len(out)}")

    # downloads for the strongest candidates
    names = [p["package"] for p in out[:enrich]]
    plain = [n for n in names if not n.startswith("@")]
    scoped = [n for n in names if n.startswith("@")]
    counts: Dict[str, int] = {}
    for i in range(0, len(plain), 100):
        data = fetch_json("https://api.npmjs.org/downloads/point/last-month/" +
                          ",".join(plain[i:i + 100]))
        if not data:
            continue
        for name, v in data.items():
            if isinstance(v, dict) and "downloads" in v:
                counts[name] = v["downloads"]
        time.sleep(0.2)
    for name in scoped:
        data = fetch_json("https://api.npmjs.org/downloads/point/last-month/" +
                          urllib.parse.quote(name, safe=""))
        if data and "downloads" in data:
            counts[name] = data["downloads"]
        time.sleep(0.2)
    for p in out:
        if p["package"] in counts:
            p["downloads_last_month"] = counts[p["package"]]
    print(f"  download counts: {len(counts)}")
    return out


# ---------------------------------------------------------------- merge
def merge(official, curated, npm_pkgs) -> List[Dict[str, Any]]:
    servers: Dict[str, Dict[str, Any]] = {}

    for entry in official + curated:
        # official reference servers all live in one repository, so they key on their own id
        key = entry["id"] if entry.get("trust") == "official" else (entry.get("repo") or entry["id"])
        if key in servers:
            existing = servers[key]
            existing["sources"] = sorted(set(existing["sources"]) | set(entry["sources"]))
            if entry.get("category") and existing.get("category") in ("", "Uncategorised"):
                existing["category"] = entry["category"]
            if len(entry.get("description", "")) > len(existing.get("description", "")):
                existing["description"] = entry["description"]
            existing["languages"] = sorted(set(existing.get("languages") or [])
                                           | set(entry.get("languages") or []))
        else:
            servers[key] = dict(entry)

    for pkg in npm_pkgs:
        key = pkg.get("repo")
        if key and key in servers:
            servers[key]["npm_package"] = pkg["package"]
            servers[key]["downloads_last_month"] = pkg.get("downloads_last_month")
            servers[key]["sources"] = sorted(set(servers[key]["sources"]) | {"npm"})
            continue
        if key:
            servers[key] = {
                "id": key,
                "name": pkg["package"],
                "repo": key,
                "url": pkg["url"],
                "description": pkg["description"],
                "category": "npm-only",
                "languages": [],
                "sources": ["npm"],
                "trust": "community",
                "npm_package": pkg["package"],
                "version": pkg.get("version"),
                "downloads_last_month": pkg.get("downloads_last_month"),
            }
        else:
            servers[f"npm:{pkg['package']}"] = {
                "id": f"npm:{pkg['package']}",
                "name": pkg["package"],
                "repo": None,
                "url": pkg["url"],
                "description": pkg["description"],
                "category": "npm-only",
                "languages": [],
                "sources": ["npm"],
                "trust": "community",
                "npm_package": pkg["package"],
                "version": pkg.get("version"),
                "downloads_last_month": pkg.get("downloads_last_month"),
            }

    rows = list(servers.values())
    # a package that only matched the npm keyword is self-declared: keep it, but separately,
    # because "keywords: mcp-server" is a claim, not a review
    listed, keyword_only = [], []
    for row in rows:
        (keyword_only if row.get("sources") == ["npm"] else listed).append(row)
    for bucket in (listed, keyword_only):
        bucket.sort(key=lambda r: (-(r.get("downloads_last_month") or 0),
                                   -len(r.get("sources") or []),
                                   (r.get("name") or "").lower()))
    return listed, keyword_only


def main():
    ap = argparse.ArgumentParser(description="Build the MCP server index.")
    ap.add_argument("--official", default=os.path.join(ROOT, "vendor", "mcp-servers"),
                    help="clone of modelcontextprotocol/servers")
    ap.add_argument("--curated", default=os.path.join(ROOT, "vendor", "awesome-mcp-servers"),
                    help="clone of punkpeye/awesome-mcp-servers")
    ap.add_argument("--pages", type=int, default=4, help="npm search pages (250 each)")
    ap.add_argument("--enrich", type=int, default=400, help="npm download lookups")
    ap.add_argument("--offline", action="store_true", help="skip npm entirely")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    official = build_official(args.official) if os.path.isdir(args.official) else []
    curated = build_curated(args.curated) if os.path.isdir(args.curated) else []
    print(f"official reference servers: {len(official)}")
    print(f"curated list entries: {len(curated)}")
    npm_pkgs = [] if args.offline else build_npm(args.pages, args.enrich)

    servers, keyword_only = merge(official, curated, npm_pkgs)
    doc = {
        "generated": time.strftime("%Y-%m-%d"),
        "note": ("MCP servers you can attach to an n8n AI Agent through the MCP Client Tool "
                 "node, or expose from n8n with the MCP Server Trigger node. Trust is not "
                 "uniform: 'official' means published by the MCP project, 'community' means "
                 "someone published it to a list or npm. Read the source before you connect "
                 "one, and never give a server credentials it does not need."),
        "counts": {
            "servers": len(servers),
            "official": sum(1 for s in servers if s.get("trust") == "official"),
            "from_curated_list": sum(1 for s in servers
                                     if "punkpeye/awesome-mcp-servers" in s.get("sources", [])),
            "on_npm": sum(1 for s in servers if "npm" in s.get("sources", [])),
            "npm_packages_scanned": len(npm_pkgs),
            "keyword_only": len(keyword_only),
        },
        "sources": [
            "https://github.com/modelcontextprotocol/servers",
            "https://github.com/punkpeye/awesome-mcp-servers",
            "https://registry.npmjs.org/-/v1/search?text=keywords:mcp-server",
        ],
        "servers": servers,
        "keyword_only_packages": keyword_only,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
    print(json.dumps(doc["counts"], indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
