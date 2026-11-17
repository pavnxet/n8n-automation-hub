"""Data-flow analysis: what each node receives, what it emits, and whether the expressions
in the next node can actually read it.

This is simulation, not execution. The module knows a handful of node semantics from the
knowledge base (a Webhook emits body/headers/query; a Set node emits exactly the fields it
assigns; an HTTP Request emits whatever the API returns, so its shape is unknown), and it
reasons from there. Anything it cannot know is marked unknown rather than guessed, and every
report says `simulated: true`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from server import expressions as expr

UNKNOWN = "*"  # "shape not knowable statically"

# Nodes that pass the incoming item through untouched.
PASSTHROUGH = {
    "n8n-nodes-base.filter", "n8n-nodes-base.if", "n8n-nodes-base.switch",
    "n8n-nodes-base.removeDuplicates", "n8n-nodes-base.sort", "n8n-nodes-base.limit",
    "n8n-nodes-base.splitInBatches", "n8n-nodes-base.noOp", "n8n-nodes-base.wait",
    "n8n-nodes-base.merge",
}

# Nodes whose output shape is decided by an external system.
EXTERNAL = {
    "n8n-nodes-base.httpRequest", "n8n-nodes-base.graphql", "n8n-nodes-base.postgres",
    "n8n-nodes-base.mySql", "n8n-nodes-base.mongoDb", "n8n-nodes-base.redis",
    "n8n-nodes-base.googleSheets", "n8n-nodes-base.airtable", "n8n-nodes-base.notion",
    "n8n-nodes-base.slack", "n8n-nodes-base.telegram", "n8n-nodes-base.gmail",
    "n8n-nodes-base.discord", "n8n-nodes-base.whatsApp", "n8n-nodes-base.hubspot",
    "n8n-nodes-base.jira", "n8n-nodes-base.github", "n8n-nodes-base.stripe",
}


def _order(workflow: dict) -> List[str]:
    """Breadth-first order from the trigger(s); unreachable nodes appended at the end."""
    nodes = {n["name"]: n for n in workflow.get("nodes", []) if isinstance(n, dict) and n.get("name")}
    conns = workflow.get("connections") or {}
    incoming = {name: 0 for name in nodes}
    for src, outputs in conns.items():
        for branches in (outputs or {}).values():
            for branch in branches or []:
                for target in branch or []:
                    if isinstance(target, dict) and target.get("node") in incoming:
                        incoming[target["node"]] += 1
    starts = [n for n, c in incoming.items() if c == 0] or list(nodes)[:1]
    order, seen = [], set()
    queue = list(starts)
    while queue:
        name = queue.pop(0)
        if name in seen or name not in nodes:
            continue
        seen.add(name)
        order.append(name)
        for branches in (conns.get(name) or {}).values():
            for branch in branches or []:
                for target in branch or []:
                    if isinstance(target, dict) and target.get("node") not in seen:
                        queue.append(target["node"])
    order.extend(n for n in nodes if n not in seen)
    return order


def _fields_out(node: dict, kb) -> Set[str]:
    """Best-effort field set produced by a node. {UNKNOWN} means 'cannot know'."""
    ntype = node.get("type") or ""
    params = node.get("parameters") or {}
    record = kb.record_by_type(ntype)

    if ntype in PASSTHROUGH:
        return set()  # caller substitutes the input fields
    if ntype == "n8n-nodes-base.set":
        names = set()
        assignments = (params.get("assignments") or {}).get("assignments") or []
        for a in assignments:
            if isinstance(a, dict) and a.get("name"):
                names.add(a["name"])
        # "include other fields" keeps everything else
        if params.get("includeOtherFields"):
            return names | {UNKNOWN}
        return names or {UNKNOWN}
    if ntype.endswith("webhook") or ntype.endswith("Trigger"):
        return {"body", "headers", "query", "params", "webhookUrl"}
    if ntype in EXTERNAL:
        return {UNKNOWN}
    if record and record.get("category") == "trigger-node":
        return {UNKNOWN}
    return {UNKNOWN}


def analyze(workflow: dict, kb, fixtures: Optional[Dict[str, List[dict]]] = None) -> Dict[str, Any]:
    """Map the data flow and report places where an expression cannot be satisfied."""
    fixtures = fixtures or {}
    nodes = {n["name"]: n for n in workflow.get("nodes", [])
             if isinstance(n, dict) and n.get("name")}
    conns = workflow.get("connections") or {}
    order = _order(workflow)

    upstream_of: Dict[str, List[str]] = {name: [] for name in nodes}
    for src, outputs in conns.items():
        for branches in (outputs or {}).values():
            for branch in branches or []:
                for target in branch or []:
                    if isinstance(target, dict) and target.get("node") in upstream_of:
                        upstream_of[target["node"]].append(src)

    findings: List[Dict[str, Any]] = []
    available: Dict[str, Set[str]] = {}
    report_nodes: List[Dict[str, Any]] = []

    for name in order:
        node = nodes.get(name)
        if not node:
            continue
        ntype = node.get("type") or ""
        params = node.get("parameters") or {}

        # ---- what arrives here
        incoming_fields: Set[str] = set()
        unknown_input = False
        for up in upstream_of.get(name, []):
            fields = available.get(up, {UNKNOWN})
            if UNKNOWN in fields:
                unknown_input = True
            incoming_fields |= {f for f in fields if f != UNKNOWN}
        if not upstream_of.get(name):
            incoming_fields = set()  # a trigger starts empty

        produced = _fields_out(node, kb)
        if not produced:
            produced = set(incoming_fields) | ({UNKNOWN} if unknown_input else set())
        available[name] = produced

        # ---- expressions in this node
        node_expressions = []
        for path, raw, inner in expr.iter_node_expressions(params):
            analysis = expr.analyse(inner)
            entry = {"parameter": path, "expression": raw[:200],
                     "references": analysis["refs"], "issues": analysis["issues"]}
            node_expressions.append(entry)

            for ref in analysis["refs"]:
                if ref["kind"] != "json_path" or not ref.get("path"):
                    continue
                head = ref["path"][0]
                if unknown_input or not incoming_fields:
                    continue  # cannot judge
                if head not in incoming_fields:
                    findings.append({
                        "severity": "warning",
                        "code": "field_not_upstream",
                        "node": name,
                        "parameter": path,
                        "message": (f"{raw[:80]} reads '{head}', but the upstream node(s) "
                                    f"{', '.join(upstream_of.get(name, [])) or '(none)'} do not "
                                    f"produce it."),
                        "suggestion": (f"Upstream fields seen: "
                                       f"{', '.join(sorted(incoming_fields)) or 'none'}. "
                                       f"Check the field name, or add a Set node to shape it."),
                    })

        # ---- fixtures, when supplied. A fixture belongs to the node that produces the data,
        # so a node with no fixture of its own inherits its upstream node's sample.
        fixture_rows = fixtures.get(name) or []
        if not fixture_rows:
            for up in upstream_of.get(name, []):
                if fixtures.get(up):
                    fixture_rows = fixtures[up]
                    break
        resolved = []
        if fixture_rows and node_expressions:
            sample = fixture_rows[0] if isinstance(fixture_rows[0], dict) else {}
            for entry in node_expressions:
                for ref in entry["references"]:
                    if ref["kind"] != "json_path" or not ref.get("path"):
                        continue
                    value: Any = sample
                    ok = True
                    for seg in ref["path"]:
                        if isinstance(value, dict) and seg in value:
                            value = value[seg]
                        elif isinstance(value, list) and seg.isdigit() and int(seg) < len(value):
                            value = value[int(seg)]
                        else:
                            ok = False
                            break
                    resolved.append({"node": name, "parameter": entry["parameter"],
                                     "path": ref["path"], "resolved": ok,
                                     "value": None if not ok else str(value)[:60]})

        report_nodes.append({
            "node": name,
            "type": ntype,
            "upstream": upstream_of.get(name, []),
            "input_fields": sorted(incoming_fields) if not unknown_input else
                            sorted(incoming_fields) + [UNKNOWN],
            "output_fields": sorted(produced),
            "expressions": node_expressions,
            "fixture_resolved": resolved,
        })

    # ---- structural data-flow risks
    for name, node in nodes.items():
        ntype = node.get("type") or ""
        params = node.get("parameters") or {}
        if ntype == "n8n-nodes-base.splitInBatches":
            back = [t for t in (conns.get(name) or {}).get("main", [[]])[0] or []
                    if isinstance(t, dict) and t.get("node") == name]
            loop_targets = (conns.get(name) or {}).get("main", [])
            if not loop_targets or len(loop_targets) < 2:
                findings.append({
                    "severity": "warning", "code": "loop_without_close", "node": name,
                    "message": ("Loop Over Items usually needs two outputs: the done branch and "
                                "the loop branch, with the last node wired back into the loop."),
                    "suggestion": "Connect the final node back to the loop node's input.",
                })
        if ntype == "n8n-nodes-base.aggregate" and not params.get("fieldsToAggregate"):
            findings.append({
                "severity": "info", "code": "aggregate_without_fields", "node": name,
                "message": "Aggregate has no field selection, so it will aggregate everything.",
            })
        if ntype in ("n8n-nodes-base.telegram", "n8n-nodes-base.slack",
                     "n8n-nodes-base.discord", "n8n-nodes-base.gmail"):
            text_like = [k for k in params if k in ("text", "message", "markdown", "html")]
            if not text_like:
                findings.append({
                    "severity": "warning", "code": "message_without_body", "node": name,
                    "message": (f"{node.get('name')} has no message body parameter set, so "
                                f"nothing will be sent."),
                    "suggestion": "Set the text/message parameter, usually "
                                  "'={{ $json.<field> }}'.",
                })

    return {
        "simulated": True,
        "execution_order": order,
        "nodes": report_nodes,
        "findings": findings,
        "fixtures_used": bool(fixtures),
        "note": ("Static data-flow simulation. Field shapes are inferred from node semantics; "
                 "external APIs are treated as unknown. Nothing here ran against n8n — use "
                 "test_workflow for a real execution."),
    }
