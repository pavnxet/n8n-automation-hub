#!/usr/bin/env python3
"""Validate every workflow in automations/ and regenerate automations/registry.json.

Checks
  1. file is valid JSON with `nodes` and `connections`
  2. node names are unique (connections are keyed by name)
  3. every node has a `type`, and the type is known to the knowledge base or looks
     like a community node package
  4. every node has a `typeVersion`
  5. connections only point at node names that exist
  6. no secret-shaped parameter keys carry a literal value
  7. no value looks like a live credential
  8. no two nodes share a position

Exit code 1 if any workflow fails, after writing the registry for the files that passed.

Usage:
    python3 tools/validate_repo.py            # validate + write registry
    python3 tools/validate_repo.py --check    # validate only, do not write
"""
import json, os, re, sys, glob, hashlib, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO = os.path.join(ROOT, "automations")
CATALOG = os.path.join(ROOT, "knowledge-base", "catalog.json")
REGISTRY = os.path.join(AUTO, "registry.json")

SECRET_KEYS = {"apikey", "api_key", "token", "accesstoken", "access_token", "password",
               "secret", "clientsecret", "client_secret", "privatekey", "private_key",
               "bearertoken", "authtoken", "auth_token", "webhooksecret"}

SECRET_VALUE = [
    re.compile(r"^sk-[A-Za-z0-9_\-]{16,}"),          # OpenAI-style
    re.compile(r"^ghp_[A-Za-z0-9]{20,}"),            # GitHub PAT
    re.compile(r"^xox[baprs]-[A-Za-z0-9\-]{10,}"),   # Slack
    re.compile(r"^AKIA[0-9A-Z]{16}$"),               # AWS access key id
    re.compile(r"^eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\."),  # JWT
    re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),       # long base64 blob
]

COMMUNITY = re.compile(r"^(@[a-z0-9._\-]+/)?n8n-nodes-[a-z0-9._\-]+$", re.I)
BUILTIN_PREFIX = ("n8n-nodes-base.", "@n8n/n8n-nodes-langchain.")


def load_known_types():
    known = set()
    if os.path.exists(CATALOG):
        for n in json.load(open(CATALOG))["nodes"]:
            known.add(n.get("workflow_type") or n["id"])
    return known


def walk_strings(obj, path=""):
    """Yield (path, key, value) for every string leaf."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                yield path, k, v
            else:
                yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                yield path, "", v
            else:
                yield from walk_strings(v, f"{path}[{i}]")


def looks_secret(value):
    v = value.strip()
    if len(v) < 20:
        return False
    for rx in SECRET_VALUE:
        if rx.match(v):
            return True
    # high entropy heuristic: long, no spaces, mixed classes
    if len(v) >= 48 and " " not in v and not v.startswith(("http", "{{", "=")):
        classes = sum([any(c.islower() for c in v), any(c.isupper() for c in v),
                       any(c.isdigit() for c in v)])
        if classes >= 2:
            return True
    return False


def validate_workflow(path, known):
    errs, warns = [], []
    try:
        wf = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"{path}: invalid JSON — {e}"], [], {}

    nodes = wf.get("nodes")
    conns = wf.get("connections")
    if not isinstance(nodes, list) or not nodes:
        errs.append(f"{path}: missing or empty 'nodes'")
        return errs, warns, {}
    if not isinstance(conns, dict):
        errs.append(f"{path}: missing 'connections' object")

    names, positions, types, triggers = set(), set(), [], None
    undocumented, community = set(), set()

    for i, n in enumerate(nodes):
        label = n.get("name") or f"node[{i}]"
        name = n.get("name")
        if not name:
            errs.append(f"{path}: node[{i}] has no name")
        elif name in names:
            errs.append(f"{path}: duplicate node name '{name}' (connections are keyed by name)")
        else:
            names.add(name)

        ntype = n.get("type")
        if not ntype:
            errs.append(f"{path}: '{label}' has no type")
        else:
            types.append(ntype)
            if ntype not in known:
                if ntype.startswith(BUILTIN_PREFIX):
                    # real built-in that the docs do not give a page of its own
                    # (sticky notes, noOp, legacy function node, ...)
                    undocumented.add(ntype)
                elif COMMUNITY.match(ntype):
                    community.add(ntype)
                else:
                    errs.append(f"{path}: '{label}' has unknown node type '{ntype}' "
                                f"(not in knowledge base, not a community package)")
            if ntype in ("n8n-nodes-base.manualTrigger", "n8n-nodes-base.webhook",
                         "n8n-nodes-base.scheduleTrigger", "n8n-nodes-base.formTrigger",
                         "n8n-nodes-base.chatTrigger", "n8n-nodes-base.executeWorkflowTrigger",
                         "n8n-nodes-base.errorTrigger") or "trigger" in ntype.lower():
                triggers = triggers or ntype

        if "typeVersion" not in n:
            errs.append(f"{path}: '{label}' has no typeVersion")

        pos = n.get("position")
        if isinstance(pos, list) and len(pos) == 2:
            key = (pos[0], pos[1])
            if key in positions:
                errs.append(f"{path}: '{label}' shares position {key} with another node")
            positions.add(key)

        for parent, key, val in walk_strings(n.get("parameters", {})):
            if key and key.lower().replace("-", "_") in SECRET_KEYS and val.strip():
                errs.append(f"{path}: '{label}' has a literal value in secret-shaped field "
                            f"'{parent}.{key}'")
            elif looks_secret(val):
                warns.append(f"{path}: '{label}' field '{parent}' holds a credential-shaped "
                             f"value — confirm it is a placeholder")
            if re.match(r"^https?://hooks\.slack\.com/services/\S{10,}", val):
                errs.append(f"{path}: '{label}' contains a live Slack webhook URL")

    for src, outputs in (conns or {}).items():
        if src not in names:
            errs.append(f"{path}: connection from unknown node '{src}'")
        for _otype, branches in (outputs or {}).items():
            for branch in branches:
                for target in branch or []:
                    tname = target.get("node")
                    if tname and tname not in names:
                        errs.append(f"{path}: connection '{src}' points at unknown node '{tname}'")

    if not triggers:
        warns.append(f"{path}: no trigger node — importable, but it cannot run on its own")

    kb_records = sorted({t for t in types if t in known})
    info = {
        "name": wf.get("name") or os.path.basename(path),
        "node_count": len(nodes),
        "node_types": sorted(set(types)),
        "trigger": triggers,
        "kb_records": kb_records,
        "community_nodes": sorted(community),
        "undocumented_builtin": sorted(undocumented),
    }
    return errs, warns, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only, do not write the registry")
    args = ap.parse_args()

    known = load_known_types()
    files = sorted(f for f in glob.glob(os.path.join(AUTO, "**", "*.json"), recursive=True)
                   if not f.endswith("registry.json"))
    if not files:
        print("no workflows found under automations/")
        return 0

    all_errs, all_warns, entries = [], [], []
    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        errs, warns, info = validate_workflow(path, known)
        all_errs += errs
        all_warns += warns
        if info:
            info["file"] = rel
            info["sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
            entries.append(info)

    for w in all_warns:
        print(f"warning: {w}")
    for e in all_errs:
        print(f"error:   {e}")

    print(f"\n{len(files)} workflows · {len(all_errs)} errors · {len(all_warns)} warnings")

    if not args.check:
        doc = {
            "generated_by": "tools/validate_repo.py",
            "note": "Generated file. Do not edit by hand — run the validator instead.",
            "workflow_count": len(entries),
            "workflows": entries,
        }
        json.dump(doc, open(REGISTRY, "w"), indent=2, ensure_ascii=False)
        print(f"wrote {os.path.relpath(REGISTRY, ROOT)}")

    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())
