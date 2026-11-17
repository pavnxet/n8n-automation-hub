"""Generate importable n8n workflow JSON from a plan or a plain request.

The generator never invents a parameter name: every key it writes comes from the node's schema,
and every value is either a schema default, an internal enum value from the knowledge base, or
an explicit placeholder that is reported back to the caller.

Two things it refuses to do:

  * fabricate credentials, tokens, chat ids or endpoints — placeholders are marked, listed, and
    validated as "still to fill in";
  * claim a workflow works. `executed` is always false: this is generated and statically
    validated JSON, nothing more.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from server import planner as planner_mod
from server import schema as sch
from server.validation import validate

BRANCHING = ("n8n-nodes-base.if", "n8n-nodes-base.filter", "n8n-nodes-base.switch",
             "n8n-nodes-base.compareDatasets")

PLACEHOLDERS = {
    "url": "https://example.com/api/endpoint",
    "chatId": "REPLACE_WITH_CHAT_ID",
    "channel": "REPLACE_WITH_CHANNEL",
    "text": "REPLACE_WITH_MESSAGE_TEXT",
    "subject": "REPLACE_WITH_SUBJECT",
    "toEmail": "REPLACE_WITH_RECIPIENT",
    "database": "REPLACE_WITH_DATABASE",
    "table": "REPLACE_WITH_TABLE",
    "query": "REPLACE_WITH_SQL_QUERY",
    "documentId": "REPLACE_WITH_DOCUMENT_ID",
    "sheetName": "REPLACE_WITH_SHEET_NAME",
}


def _placeholder(param: dict, node_type: str) -> Any:
    """A clearly-marked value for a required parameter we cannot know."""
    name = param.get("name", "")
    ptype = param.get("type") or "string"

    if name in PLACEHOLDERS:
        return PLACEHOLDERS[name]
    if ptype == "options":
        allowed = sch.enum_values(param)
        return allowed[0] if allowed else "REPLACE_ME"
    if ptype == "multiOptions":
        return []
    if ptype == "number":
        return 0
    if ptype == "boolean":
        return False
    if ptype == "json":
        return "{}"
    if ptype == "collection":
        return {}
    if ptype == "fixedCollection":
        return {}
    if ptype == "resourceLocator":
        return {"__rl": True, "mode": "list", "value": ""}
    return f"REPLACE_WITH_{re.sub(r'[^A-Z0-9]+', '_', name.upper())}"


def _base_parameters(record: dict, step: Optional[dict]) -> tuple:
    """Schema defaults plus the resolved operation, and the placeholders we had to add."""
    params: Dict[str, Any] = {}
    placeholders: List[Dict[str, str]] = []

    # Seed only the discriminators n8n itself pre-fills (resource, operation, authentication).
    # Seeding every default cascades: one default can make a dozen conditional parameters
    # visible, and their defaults then contradict the chosen operation.
    base: Dict[str, Any] = {}
    for p in sch.params_of(record):
        if p.get("name") in ("resource", "operation", "authentication") and "default" in p:
            base[p["name"]] = p["default"]
    if step:
        op = step.get("operation") or {}
        if op.get("resource_value"):
            base["resource"] = op["resource_value"]
        if op.get("operation_value"):
            base["operation"] = op["operation_value"]

    # Now take defaults only for parameters that are visible for that base configuration.
    for p in sch.params_of(record):
        name = p["name"]
        if p.get("type") in sch.NON_INPUT_TYPES or name in base:
            continue
        if "default" in p and p["default"] not in ("", None, {}, []):
            if sch.is_visible(p, base):
                value = p["default"]
                if p.get("type") == "resourceLocator" and isinstance(value, dict):
                    # n8n stores locators with an explicit __rl marker; a bare default is
                    # structurally invalid until the user picks a resource
                    value = {**value, "__rl": True}
                base[name] = value
    params.update(base)

    # required, visible, and still empty → placeholder
    values = sch.effective_values(params, record)
    for p in sch.visible_params(record, values):
        if not p.get("required"):
            continue
        if sch._empty(values.get(p["name"])):
            value = _placeholder(p, record.get("workflow_type", ""))
            params[p["name"]] = value
            placeholders.append({
                "node": step.get("node_name") if step else record.get("name"),
                "parameter": p["name"],
                "display_name": p.get("displayName"),
                "value": value if isinstance(value, (str, int, float, bool)) else "<object>",
                "why": "required by the node schema and not supplied by the request",
            })
    return params, placeholders


def _node_id() -> str:
    return str(uuid.uuid4())


def generate(request: Optional[str] = None, plan: Optional[dict] = None, name: Optional[str] = None,
             kb=None, se=None, max_fix_rounds: int = 2) -> Dict[str, Any]:
    """Build a workflow from a request or an existing plan, then validate it."""
    from server.search import SearchEngine
    se = se or SearchEngine(kb)

    if plan is None:
        if not request:
            return {"error": "provide either a request or a plan"}
        plan = planner_mod.plan(request, kb, se)

    if plan.get("error"):
        return {"error": plan["error"]}

    nodes: List[Dict[str, Any]] = []
    placeholders: List[Dict[str, str]] = []
    assumptions: List[str] = list(plan.get("assumptions") or [])

    trigger = plan.get("trigger") or {}
    trigger_type = trigger.get("node_type")
    record = kb.record_by_type(trigger_type) if trigger_type else None
    if record:
        params, ph = _base_parameters(record, None)
        hint = trigger.get("parameter_hint") or {}
        if hint:
            rule = params.get("rule") if isinstance(params.get("rule"), dict) else {}
            rule["interval"] = [hint]
            params["rule"] = rule
        nodes.append({
            "parameters": params,
            "id": _node_id(),
            "name": trigger.get("name") or record.get("name") or "Trigger",
            "type": record.get("workflow_type") or trigger_type,
            "typeVersion": record.get("type_version"),
            "position": [0, 0],
        })
        placeholders.extend(ph)
    else:
        assumptions.append(
            f"Trigger '{trigger_type}' has no knowledge-base record; a Manual Trigger was used.")

    x = 220
    for step in plan.get("steps") or []:
        node_type = step.get("node_type")
        record = kb.record_by_type(node_type)
        if not record:
            assumptions.append(
                f"Step '{step.get('node_name')}' ({node_type}) is not in the knowledge base and "
                f"was skipped.")
            continue
        params, ph = _base_parameters(record, step)
        placeholders.extend(ph)
        nodes.append({
            "parameters": params,
            "id": _node_id(),
            "name": step.get("node_name") or record.get("name"),
            "type": record.get("workflow_type"),
            "typeVersion": record.get("type_version"),
            "position": [x, 0],
        })
        x += 220

    if not nodes:
        return {"error": "nothing to generate: the plan produced no resolvable nodes",
                "plan": plan}

    # ---- connections: straight chain, with an empty second branch for branching nodes
    connections: Dict[str, Any] = {}
    for i, node in enumerate(nodes[:-1]):
        nxt = nodes[i + 1]
        target = {"node": nxt["name"], "type": "main", "index": 0}
        if node["type"] in BRANCHING:
            connections[node["name"]] = {"main": [[target], []]}
        else:
            connections[node["name"]] = {"main": [[target]]}

    # ---- sticky note: objective, credentials, placeholders
    note_lines = [f"## {name or plan.get('objective', 'Workflow')[:80]}", ""]
    note_lines.append(f"**Objective:** {plan.get('objective', '')[:300]}")
    creds = plan.get("credentials") or []
    if creds:
        note_lines.append("")
        note_lines.append("**Credentials to attach after import:**")
        for c in creds:
            note_lines.append(f"- `{c['type']}` → {', '.join(c['used_by'])}")
    if placeholders:
        note_lines.append("")
        note_lines.append("**Fill in before running:**")
        for p in placeholders[:10]:
            note_lines.append(f"- {p['node']} → {p['parameter']}")
    if plan.get("open_questions"):
        note_lines.append("")
        note_lines.append("**Open questions:**")
        for q in plan["open_questions"][:5]:
            note_lines.append(f"- {q}")

    nodes.append({
        "parameters": {"content": "\n".join(note_lines), "height": 320, "width": 460,
                       "color": 4},
        "id": _node_id(),
        "name": "Notes",
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [-260, -60],
    })

    workflow = {
        "name": name or _default_name(plan),
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"},
        "pinData": {},
    }

    # ---- validate, then try to fix what is mechanically fixable
    report = validate(workflow, kb)
    fixes: List[str] = []
    for _ in range(max_fix_rounds):
        if report["valid"]:
            break
        changed = _apply_fixes(workflow, report, kb, fixes)
        if not changed:
            break
        report = validate(workflow, kb)

    return {
        "workflow": workflow,
        "name": workflow["name"],
        "plan": {
            "objective": plan.get("objective"),
            "sequence": plan.get("sequence"),
            "risks": plan.get("risks"),
            "open_questions": plan.get("open_questions"),
            "confidence": plan.get("confidence"),
        },
        "validation": report,
        "placeholders": placeholders,
        "assumptions": assumptions,
        "fixes_applied": fixes,
        "importable": report["valid"],
        "executed": False,
        "note": ("Generated and statically validated against the node schemas. It has not been "
                 "executed: import it, attach credentials, fill the placeholders, and test in a "
                 "staging instance before activating."),
    }


def _default_name(plan: dict) -> str:
    objective = (plan.get("objective") or "Generated workflow").strip()
    short = re.sub(r"\s+", " ", objective)[:60].rstrip(" .,")
    return short[:1].upper() + short[1:]


def _apply_fixes(workflow: dict, report: dict, kb, fixes: List[str]) -> bool:
    """Mechanical repairs only: placeholders for missing required params, valid enum values."""
    changed = False
    by_name = {n["name"]: n for n in workflow["nodes"]}

    for err in report["errors"]:
        node = by_name.get(err.get("node"))
        if not node:
            continue
        record = kb.record_by_type(node.get("type"))
        if not record:
            continue
        pname = err.get("parameter")
        if not pname:
            continue
        params = node.setdefault("parameters", {})

        if err["code"] == "missing_required_parameter":
            param = sch.param_map(record).get(pname)
            if param:
                params[pname] = _placeholder(param, node.get("type", ""))
                fixes.append(f"{node['name']}.{pname}: added a marked placeholder")
                changed = True
        elif err["code"] == "invalid_enum":
            param = sch.param_map(record).get(pname)
            if param:
                allowed = sch.enum_values(param)
                if allowed:
                    params[pname] = allowed[0]
                    fixes.append(f"{node['name']}.{pname}: replaced with the valid value "
                                 f"'{allowed[0]}'")
                    changed = True
        elif err["code"] == "missing_type_version":
            if record.get("type_version") is not None:
                node["typeVersion"] = record["type_version"]
                fixes.append(f"{node['name']}: set typeVersion {record['type_version']}")
                changed = True
    return changed
