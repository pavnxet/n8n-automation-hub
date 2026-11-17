#!/usr/bin/env python3
"""Enrich the docs-based KB with exact node schemas from the published
n8n-nodes-base / @n8n/n8n-nodes-langchain packages.

Adds per node: workflow_type, type_version(s), groups, usable_as_tool,
credential_types, defaults, parameter schema (names + internal option values),
and writes indexes/resources-operations.json.
"""
import json, os, re, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.environ.get("N8N_KB_OUT", os.path.join(ROOT, "knowledge-base"))
BASE = os.environ.get("N8N_BASE_NODES_JSON",
                      os.path.join(ROOT, "vendor", "n8n-nodes-base.nodes.json"))
LC = os.environ.get("N8N_LC_NODES_JSON",
                    os.path.join(ROOT, "vendor", "n8n-nodes-langchain.nodes.json"))
TODAY = "2026-11-17"


def vmax(x):
    v = x.get("version")
    if isinstance(v, list):
        return max([float(i) for i in v] or [0])
    try:
        return float(v or 0)
    except Exception:
        return 0


def load(path, prefix):
    """norm(suffix) -> entry, keeping the highest version."""
    if not os.path.exists(path):
        return {}
    out = {}
    for n in json.load(open(path)):
        key = norm(n["name"])
        if key not in out or vmax(n) > vmax(out[key]):
            out[key] = n
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def compact_opts(opts, depth=0):
    res = []
    for o in opts or []:
        if not isinstance(o, dict):
            continue
        e = {"name": o.get("name") or o.get("displayName")}
        if "value" in o:
            v = o["value"]
            if isinstance(v, (str, int, float, bool)) or v is None:
                e["value"] = v
        if o.get("values") and depth == 0:
            e["values"] = [{"name": s.get("name"), "displayName": s.get("displayName"),
                            "type": s.get("type")} for s in o["values"] if isinstance(s, dict)][:40]
        if o.get("description") and depth == 0:
            e["description"] = str(o["description"])[:160]
        res.append(e)
        if len(res) >= 120:
            break
    return res


def compact_display_options(do):
    if not isinstance(do, dict):
        return None
    out = {}
    for key in ("show", "hide"):
        if isinstance(do.get(key), dict):
            out[key] = {k: (v if isinstance(v, list) else [v]) for k, v in do[key].items()}
    return out or None


def compact_props(props):
    out = []
    for p in props or []:
        if not isinstance(p, dict) or not p.get("name"):
            continue
        e = {"name": p["name"]}
        if p.get("displayName"):
            e["displayName"] = p["displayName"]
        e["type"] = p.get("type")
        if p.get("required"):
            e["required"] = True
        if "default" in p and p["default"] not in ("", None, {}, []):
            d = p["default"]
            if isinstance(d, (str, int, float, bool)):
                e["default"] = d if not isinstance(d, str) or len(d) < 300 else d[:300]
            elif isinstance(d, dict) and len(json.dumps(d)) < 500:
                e["default"] = d
        if isinstance(p.get("options"), list) and p["options"]:
            opts = compact_opts(p["options"])
            if opts:
                e["options"] = opts
        do = compact_display_options(p.get("displayOptions"))
        if do:
            e["displayOptions"] = do
        if p.get("description"):
            e["description"] = str(p["description"])[:220]
        out.append(e)
    return out


def enum_map(entry):
    """resources / operations / authentication with internal values."""
    props = entry.get("properties") or []
    resources, auth = [], []
    ops = {}
    for p in props:
        if p.get("name") == "resource" and p.get("options"):
            resources = [{"name": o.get("name"), "value": o.get("value")}
                         for o in p["options"] if isinstance(o, dict)]
        if p.get("name") == "authentication" and p.get("options"):
            auth = [{"name": o.get("name"), "value": o.get("value")}
                    for o in p["options"] if isinstance(o, dict)]
        if p.get("name") == "operation" and p.get("options"):
            do = p.get("displayOptions") or {}
            shows = (do.get("show") or {}).get("resource")
            keys = shows if isinstance(shows, list) else ([""] if not shows else [shows])
            for k in keys:
                ops.setdefault(str(k), []).extend(
                    [{"name": o.get("name"), "value": o.get("value")}
                     for o in p["options"] if isinstance(o, dict)])
    return resources, ops, auth


def configure(kb=None, base=None, langchain=None):
    global KB, BASE, LC
    if kb:
        KB = os.path.abspath(kb)
    if base:
        BASE = os.path.abspath(base)
    if langchain:
        LC = os.path.abspath(langchain)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Add exact node schemas from the npm packages.")
    ap.add_argument("--kb", help="knowledge base directory (default: ./knowledge-base)")
    ap.add_argument("--base-nodes", help="dist/types/nodes.json from n8n-nodes-base")
    ap.add_argument("--langchain-nodes", help="same, from @n8n/n8n-nodes-langchain")
    a = ap.parse_args()
    configure(a.kb, a.base_nodes, a.langchain_nodes)
    for label, path in (("n8n-nodes-base", BASE), ("@n8n/n8n-nodes-langchain", LC)):
        if not os.path.exists(path):
            raise SystemExit(f"missing {label} nodes.json at {path}\n"
                             f"extract it with: npm pack {label} && tar -xzf *.tgz "
                             f"--wildcards 'package/dist/types/nodes.json'")

    index = {}
    index.update(load(BASE, "n8n-nodes-base."))
    index.update(load(LC, "@n8n/n8n-nodes-langchain."))
    print("package entries:", len(index))

    # exact display-name index (unambiguous only) as a fallback for renamed nodes
    by_display, best = {}, {}
    for path, pkg in ((BASE, "n8n-nodes-base"), (LC, "@n8n/n8n-nodes-langchain")):
        if not os.path.exists(path):
            continue
        for n in json.load(open(path)):
            key = (pkg, n["name"])
            if key not in best or vmax(n) > vmax(best[key]):
                best[key] = n
    for (pkg, _), n in best.items():
        by_display.setdefault(norm(n.get("displayName")), []).append((pkg, n))
    by_display = {k: v[0] for k, v in by_display.items() if len(v) == 1}

    enum_out = {}
    matched = unmatched = 0
    files = glob.glob(os.path.join(KB, "nodes", "*", "*.json"))

    for f in files:
        rec = json.load(open(f))
        nid = rec["id"]
        if nid.startswith("n8n-nodes-base."):
            suffix = nid[len("n8n-nodes-base."):]
            base_prefix = "n8n-nodes-base."
        elif nid.startswith("n8n-nodes-langchain."):
            suffix = nid[len("n8n-nodes-langchain."):]
            base_prefix = "@n8n/n8n-nodes-langchain."
        else:
            suffix = nid
            base_prefix = ""
        entry = index.get(norm(suffix))
        if not entry:
            hit = by_display.get(norm(rec.get("name")))
            if hit:
                entry = hit[1]
                base_prefix = hit[0] + "."
        wt = (base_prefix + entry["name"]) if entry else (base_prefix + suffix)
        if not entry:
            rec["workflow_type"] = wt
            rec["node_schema"] = None
            json.dump(rec, open(f, "w"), indent=2, ensure_ascii=False)
            unmatched += 1
            continue
        matched += 1

        ver = entry.get("version")
        versions = ver if isinstance(ver, list) else [ver]
        rec["workflow_type"] = wt
        rec["type_version"] = max([float(v) for v in versions if v is not None] or [0]) or None
        rec["type_versions"] = versions
        rec["groups"] = entry.get("group") or []
        rec["usable_as_tool"] = bool(entry.get("usableAsTool"))
        if rec["usable_as_tool"]:
            rec["is_ai_tool"] = True
        rec["package"] = "n8n-nodes-base" if wt.startswith("n8n-nodes-base.") else "@n8n/n8n-nodes-langchain"
        rec["credential_types"] = [c.get("name") for c in (entry.get("credentials") or []) if isinstance(c, dict)]
        rec["credential_details"] = [
            {"name": c.get("name"), "required": bool(c.get("required")),
             **({"displayOptions": compact_display_options(c.get("displayOptions"))}
                if c.get("displayOptions") else {})}
            for c in (entry.get("credentials") or []) if isinstance(c, dict)
        ]
        rec["defaults"] = entry.get("defaults")
        rec["subtitle"] = entry.get("subtitle")
        rec["io"] = {"inputs": entry.get("inputs"), "outputs": entry.get("outputs")}
        rec["node_schema"] = {
            "source": f"{rec['package']} node description",
            "parameter_count": len(entry.get("properties") or []),
            "parameters": compact_props(entry.get("properties")),
        }

        resources, ops, auth = enum_map(entry)
        if True:
            enum_out[wt] = {"name": rec["name"], "category": rec["category"],
                            "has_resource_parameter": bool(resources)}
            if resources:
                enum_out[wt]["resources"] = resources
            if ops:
                enum_out[wt]["operations"] = ops
            if auth:
                enum_out[wt]["authentication"] = auth

        # attach internal values to documented operations
        if resources or ops:
            res_by = {norm(r["name"]): r["value"] for r in resources}
            for o in rec.get("operations", []):
                rv = res_by.get(norm(o.get("resource", "")))
                if rv is None:
                    for k, v in res_by.items():
                        if k and (k in norm(o.get("resource", "")) or norm(o.get("resource", "")) in k):
                            rv = v
                            break
                if rv is not None:
                    o["resource_value"] = rv
                key = rv if rv is not None else (resources and resources[0]["value"]) or ""
                cand = ops.get(str(key)) or ops.get("") or []
                ov = None
                for c in cand:
                    if norm(c["name"]) == norm(o.get("operation", "")):
                        ov = c["value"]
                        break
                if ov is None:
                    for c in cand:
                        if norm(c["name"]) and norm(c["name"]) in norm(o.get("operation", "")):
                            ov = c["value"]
                            break
                if ov is not None:
                    o["operation_value"] = ov

        json.dump(rec, open(f, "w"), indent=2, ensure_ascii=False)

    json.dump({"generated": TODAY,
               "note": "Internal values for resource/operation/authentication parameters, "
                       "taken from the published node descriptions. Use these values in workflow JSON.",
               "nodes": dict(sorted(enum_out.items()))},
              open(os.path.join(KB, "indexes", "resources-operations.json"), "w"),
              indent=1, ensure_ascii=False)

    # refresh catalog + nodes.jsonl with the new fields
    cat = json.load(open(os.path.join(KB, "catalog.json")))
    recs = {r["id"]: r for r in (json.load(open(f)) for f in files)}
    for e in cat["nodes"]:
        r = recs.get(e["id"])
        if not r:
            continue
        e["workflow_type"] = r.get("workflow_type")
        e["type_version"] = r.get("type_version")
        e["credential_types"] = r.get("credential_types", [])
        e["groups"] = r.get("groups", [])
        e["usable_as_tool"] = r.get("usable_as_tool", False)
    cat["generated"] = TODAY
    cat["enriched_from"] = {"n8n-nodes-base": "2.15.1", "@n8n/n8n-nodes-langchain": "2.48.3"}
    json.dump(cat, open(os.path.join(KB, "catalog.json"), "w"), indent=2, ensure_ascii=False)

    with open(os.path.join(KB, "indexes", "nodes.jsonl"), "w") as fh:
        for r in sorted(recs.values(), key=lambda x: x["id"]):
            fh.write(json.dumps({
                "id": r["id"], "type": r.get("workflow_type"), "name": r["name"],
                "category": r["category"], "trigger": r["is_trigger"],
                "ai_tool": r.get("is_ai_tool"), "tv": r.get("type_version"),
                "cred": r.get("credential_types") or ([r["credentials"]["name"]] if r.get("credentials") else []),
                "ops": [f"{o['resource']}/{o['operation']}" if o["resource"] else o["operation"]
                        for o in r["operations"]][:60],
                "desc": r["description"], "doc": r["doc_url"],
            }, ensure_ascii=False) + "\n")

    # operations index with internal values
    with open(os.path.join(KB, "indexes", "operations.jsonl"), "w") as fh:
        for r in sorted(recs.values(), key=lambda x: x["id"]):
            for o in r["operations"]:
                fh.write(json.dumps({
                    "node": r["id"], "type": r.get("workflow_type"), "name": r["name"],
                    "category": r["category"], "resource": o["resource"],
                    "operation": o["operation"],
                    "resource_value": o.get("resource_value"),
                    "operation_value": o.get("operation_value"),
                    "description": o["description"], "doc": r["doc_url"],
                }, ensure_ascii=False) + "\n")

    man = json.load(open(os.path.join(KB, "manifest.json")))
    man["version"] = "1.1.0"
    man["generated"] = TODAY
    man["enriched_from"] = cat["enriched_from"]
    man["layout"]["indexes/resources-operations.json"] = (
        "internal values for resource/operation/authentication options per node")
    man["coverage"] = {"docs_nodes": len(files), "package_nodes_matched": matched,
                       "package_nodes_missing": unmatched}
    json.dump(man, open(os.path.join(KB, "manifest.json"), "w"), indent=2, ensure_ascii=False)
    print("matched:", matched, "unmatched:", unmatched, "enum nodes:", len(enum_out))


if __name__ == "__main__":
    main()
