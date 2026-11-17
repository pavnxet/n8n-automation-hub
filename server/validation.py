"""Schema-aware workflow validation.

The first validator checked structure and secrets only. It accepted this without complaint:

    {"name": "HTTP Request", "type": "n8n-nodes-base.httpRequest", "parameters": {}}

…even though the node's own schema marks `url` as required. A workflow must not pass because
its node types and connections are recognisable; it has to pass because the nodes are actually
configured.

This module validates against the knowledge base schemas, in this order:

  1. structure          — nodes, connections, unique names and ids
  2. node types         — known built-in or recognisable community package
  3. versions           — typeVersion supported by the pinned schema
  4. required params    — visible, required, and still empty after defaults
  5. types and enums    — values match the declared type and the legal option values
  6. connections        — targets exist, branches well-formed, orphans reported
  7. expressions        — syntax, node references, unknown globals
  8. credentials        — reference present and structurally valid (never the secret itself)
  9. workflow shape     — trigger present, positions sane

Conditional parameters are the subtle part: `displayOptions` is evaluated before a parameter is
judged, so a body type that is not selected does not produce phantom "missing field" errors.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from server import expressions as expr
from server import schema as sch

try:  # one definition of "looks like a secret", shared with the repository scanner
    from tools.security_scan import SECRET_KEY_RE, SECRET_VALUE_PATTERNS
except Exception:  # pragma: no cover
    import re as _re
    SECRET_KEY_RE = _re.compile(r"(api[_-]?key|token|password|secret|private[_-]?key)", _re.I)
    SECRET_VALUE_PATTERNS = []

COSMETIC_TYPES = {"n8n-nodes-base.stickyNote"}
COSMETIC_OK = COSMETIC_TYPES | {"n8n-nodes-base.noOp", "n8n-nodes-base.function",
                                "n8n-nodes-base.functionItem", "n8n-nodes-base.start"}

_SHIPPED = None


def shipped_types(kb) -> set:
    """Node types the pinned packages actually ship (from the KB index)."""
    global _SHIPPED
    if _SHIPPED is None:
        import json as _json
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                             "knowledge-base", "indexes", "package-types.json")
        _SHIPPED = set()
        if _os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                _SHIPPED = set(_json.load(fh).get("types") or [])
    return _SHIPPED

COMMUNITY_RE = re.compile(r"^(@[a-z0-9._\-]+/)?n8n-nodes-[a-z0-9._\-]+$", re.I)
BUILTIN_PREFIX = ("n8n-nodes-base.", "@n8n/n8n-nodes-langchain.")

SEV_ERROR, SEV_WARNING, SEV_INFO = "error", "warning", "info"

# Codes that describe an incomplete-but-importable state rather than a broken one.
WARNING_CODES = {"empty_resource_locator", "undocumented_node_type", "community_node"}


class Finding(dict):
    """One validation finding, shaped for both humans and machines."""


def _finding(severity: str, code: str, message: str, node: Optional[str] = None,
             parameter: Optional[str] = None, suggestion: Optional[str] = None,
             doc: Optional[str] = None, node_type: Optional[str] = None) -> Finding:
    f = Finding(severity=severity, code=code, message=message)
    if node:
        f["node"] = node
    if node_type:
        f["node_type"] = node_type
    if parameter:
        f["parameter"] = parameter
    if suggestion:
        f["suggestion"] = suggestion
    if doc:
        f["doc"] = doc
    return f


def _type_version_bounds(record: Optional[dict]) -> tuple:
    if not record:
        return (None, None)
    versions = [v for v in (record.get("type_versions") or []) if isinstance(v, (int, float))]
    latest = record.get("type_version")
    if latest is not None and latest not in versions:
        versions.append(latest)
    if not versions:
        return (None, None)
    return (min(versions), max(versions))


def validate(workflow: Any, kb, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate a workflow dict. `kb` is a KnowledgeBase instance."""
    opts = {"expressions": True, "credentials": True, "connections": True,
            "types": True, "required": True, "versions": True}
    opts.update(options or {})

    errors: List[Finding] = []
    warnings: List[Finding] = []
    info: List[Finding] = []

    if not isinstance(workflow, dict):
        return {
            "valid": False,
            "errors": [_finding(SEV_ERROR, "invalid_workflow",
                                "Workflow must be a JSON object.")],
            "warnings": [], "info": [],
            "stats": {"nodes": 0, "errors": 1, "warnings": 0},
        }

    nodes = workflow.get("nodes")
    connections = workflow.get("connections")
    if not isinstance(nodes, list) or not nodes:
        errors.append(_finding(SEV_ERROR, "no_nodes", "Workflow has no nodes."))
        nodes = []
    if not isinstance(connections, dict):
        errors.append(_finding(SEV_ERROR, "no_connections",
                               "Workflow has no 'connections' object."))
        connections = {}

    names: Dict[str, int] = {}
    ids: Dict[str, int] = {}
    positions: Dict[tuple, str] = {}
    types_seen: List[str] = []
    has_trigger = False

    # ---------------------------------------------------------------- per node
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(_finding(SEV_ERROR, "invalid_node",
                                   f"Node at index {index} is not an object."))
            continue
        name = node.get("name")
        label = name or f"node[{index}]"
        ntype = node.get("type")
        params = node.get("parameters") or {}

        if not name:
            errors.append(_finding(SEV_ERROR, "missing_node_name",
                                   f"Node at index {index} has no name. Connections are keyed "
                                   f"by name, so an unnamed node cannot be wired."))
        else:
            names[name] = names.get(name, 0) + 1
            if names[name] == 2:
                errors.append(_finding(
                    SEV_ERROR, "duplicate_node_name",
                    f"Two nodes are named '{name}'. Connections are keyed by name, so they "
                    f"silently merge.", node=name,
                    suggestion="Give every node a unique, descriptive name."))

        node_id = node.get("id")
        if node_id:
            ids[str(node_id)] = ids.get(str(node_id), 0) + 1
            if ids[str(node_id)] == 2:
                errors.append(_finding(SEV_ERROR, "duplicate_node_id",
                                       f"Node id '{node_id}' is used more than once.", node=label))
        else:
            warnings.append(_finding(SEV_WARNING, "missing_node_id",
                                     "Node has no id; n8n will assign one on import.",
                                     node=label))

        if not ntype:
            errors.append(_finding(SEV_ERROR, "missing_node_type",
                                   "Node has no 'type'.", node=label))
            continue
        types_seen.append(ntype)

        pos = node.get("position")
        if isinstance(pos, list) and len(pos) == 2:
            key = (pos[0], pos[1])
            if key in positions:
                warnings.append(_finding(
                    SEV_WARNING, "duplicate_position",
                    f"'{label}' sits on top of '{positions[key]}' at {list(key)}.", node=label,
                    suggestion="Offset the node so both are visible on the canvas."))
            positions[key] = label
        else:
            warnings.append(_finding(SEV_WARNING, "missing_position",
                                     "Node has no position; the canvas will stack it at 0,0.",
                                     node=label))

        record = kb.record_by_type(ntype)
        known = record is not None
        community = bool(COMMUNITY_RE.match(ntype)) and not ntype.startswith(BUILTIN_PREFIX)

        shipped = shipped_types(kb)
        if (not known and not community and ntype.startswith(BUILTIN_PREFIX)
                and shipped and ntype not in shipped and ntype not in COSMETIC_OK):
            errors.append(_finding(
                SEV_ERROR, "unknown_node_type",
                f"'{ntype}' is not shipped by the pinned n8n packages, so it cannot load.",
                node=label, node_type=ntype,
                suggestion="Check the type string for a typo, or refresh the knowledge base "
                           "if this node is newer than the snapshot."))
            continue
        if not known and not community and not ntype.startswith(BUILTIN_PREFIX):
            errors.append(_finding(
                SEV_ERROR, "unknown_node_type",
                f"'{ntype}' is neither a built-in node nor a recognisable community package "
                f"(n8n-nodes-*).", node=label, node_type=ntype,
                suggestion="Check the type string, or install the community package."))
            continue
        if ntype in COSMETIC_TYPES:
            continue  # annotation only: no schema, no connections, no credentials
        if not known and ntype.startswith(BUILTIN_PREFIX):
            warnings.append(_finding(
                SEV_WARNING, "undocumented_node_type",
                f"'{ntype}' is built-in but has no knowledge-base record "
                f"(for example a sticky note or no-op).", node=label, node_type=ntype))
        if community:
            warnings.append(_finding(
                SEV_WARNING, "community_node",
                f"'{ntype}' is a third-party package. It is unverified and runs with full "
                f"host access.", node=label, node_type=ntype,
                suggestion="Pin an exact version and review the package before use."))

        if record and record.get("is_trigger"):
            has_trigger = True

        # ---- versions
        if opts["versions"] and record:
            tv = node.get("typeVersion")
            lo, hi = _type_version_bounds(record)
            if tv is None:
                errors.append(_finding(
                    SEV_ERROR, "missing_type_version",
                    "Node has no typeVersion; n8n will guess, and parameter names may not match.",
                    node=label, node_type=ntype,
                    suggestion=f"Set typeVersion to {hi}.", doc=record.get("doc_url")))
            elif hi is not None and isinstance(tv, (int, float)):
                if tv > hi + 1e-9:
                    errors.append(_finding(
                        SEV_ERROR, "unsupported_type_version",
                        f"typeVersion {tv} is newer than the highest version known to this "
                        f"knowledge base ({hi}).", node=label, node_type=ntype,
                        suggestion=f"Use typeVersion {hi}, or refresh the knowledge base.",
                        doc=record.get("doc_url")))
                elif lo is not None and tv < lo - 1e-9:
                    warnings.append(_finding(
                        SEV_WARNING, "deprecated_type_version",
                        f"typeVersion {tv} is older than the supported range ({lo}–{hi}); "
                        f"parameters may have been renamed.", node=label, node_type=ntype,
                        suggestion=f"Migrate to typeVersion {hi}.", doc=record.get("doc_url")))

        if not record:
            continue

        # ---- required parameters (visibility-aware)
        if opts["required"]:
            for p in sch.missing_required(record, params):
                desc = (p.get("description") or "").strip()
                errors.append(_finding(
                    SEV_ERROR, "missing_required_parameter",
                    f"The {p.get('displayName') or p['name']} parameter is required.",
                    node=label, node_type=ntype, parameter=p["name"],
                    suggestion=(f"Provide a value for '{p['name']}'"
                                + (f" — {desc}" if desc else "") + "."),
                    doc=record.get("doc_url")))

        # ---- types and enums on the values that are actually set
        if opts["types"]:
            values = sch.effective_values(params, record)
            for p in sch.visible_params(record, values):
                pname = p["name"]
                if pname not in (params or {}):
                    continue  # only judge values the workflow sets
                value = params[pname]
                if sch._empty(value):
                    continue
                for code, message in sch.check_value(p, value):
                    suggestion = None
                    if code == "invalid_enum":
                        allowed = sch.enum_values(p)
                        suggestion = ("Use an internal value, not the display label: "
                                      + ", ".join(str(a) for a in allowed[:8]))
                        # display label supplied instead of the internal value?
                        target = sch.normalise_label(value) if isinstance(value, str) else None
                        if target:
                            for o in p.get("options") or []:
                                if isinstance(o, dict) and "value" in o:
                                    if sch.normalise_label(o.get("name", "")) == target:
                                        suggestion = (f"'{value}' is the display label; the "
                                                      f"value n8n expects is "
                                                      f"'{o['value']}'.")
                                        break
                    elif code == "wrong_type":
                        suggestion = f"Expected type: {p.get('type')}."
                    elif code == "invalid_resource_locator":
                        suggestion = ('Use {"__rl": true, "mode": "list", "value": "…"}.')
                    bucket = warnings if code in WARNING_CODES else errors
                    bucket.append(_finding(
                        SEV_WARNING if code in WARNING_CODES else SEV_ERROR,
                        code, message, node=label, node_type=ntype,
                        parameter=pname, suggestion=suggestion, doc=record.get("doc_url")))

        # ---- secrets pasted into parameters (the file scanner's job too, but a workflow can
        # arrive here from an agent that never touched the filesystem)
        for pname, value in (params or {}).items():
            if isinstance(value, str) and value.strip() and SECRET_KEY_RE.search(pname):
                errors.append(_finding(
                    SEV_ERROR, "secret_in_parameters",
                    f"'{pname}' holds a literal value; secrets belong in a credential, not in "
                    f"workflow JSON.", node=label, node_type=ntype, parameter=pname,
                    suggestion="Remove the value and attach a credential after import."))
                continue
            if isinstance(value, str) and value.strip():
                for _rule, _sev, why, rx in SECRET_VALUE_PATTERNS:
                    if rx.search(value):
                        errors.append(_finding(
                            SEV_ERROR, "secret_in_parameters",
                            f"'{pname}' contains what looks like {why}.",
                            node=label, node_type=ntype, parameter=pname,
                            suggestion="Remove it, rotate the secret, and use a credential."))
                        break

        # ---- credentials
        if opts["credentials"]:
            required_creds = record.get("credential_types") or []
            node_creds = node.get("credentials") or {}
            if required_creds and not node_creds:
                warnings.append(_finding(
                    SEV_WARNING, "missing_credential_reference",
                    f"{record.get('name')} needs a credential ({', '.join(required_creds)}) but "
                    f"the node references none.", node=label, node_type=ntype,
                    suggestion=("Attach a credential after import; the workflow must not carry "
                                "secrets."), doc=record.get("doc_url")))
            elif node_creds:
                if not isinstance(node_creds, dict):
                    errors.append(_finding(SEV_ERROR, "invalid_credential_structure",
                                           "The 'credentials' field must be an object keyed by "
                                           "credential type.", node=label, node_type=ntype))
                else:
                    for ctype, ref in node_creds.items():
                        if required_creds and ctype not in required_creds:
                            warnings.append(_finding(
                                SEV_WARNING, "unexpected_credential_type",
                                f"Credential type '{ctype}' is not one this node declares "
                                f"({', '.join(required_creds)}).", node=label, node_type=ntype))
                        if not isinstance(ref, dict) or not (ref.get("id") or ref.get("name")):
                            errors.append(_finding(
                                SEV_ERROR, "invalid_credential_structure",
                                f"Credential '{ctype}' needs at least an id or a name.",
                                node=label, node_type=ntype,
                                suggestion='Use {"<type>": {"id": "…", "name": "…"}}.'))

        # ---- expressions
        if opts["expressions"]:
            reported_unterminated = set()
            for path, raw, inner in expr.iter_node_expressions(params):
                if expr.has_unterminated(raw) and path not in reported_unterminated:
                    reported_unterminated.add(path)
                    errors.append(_finding(
                        SEV_ERROR, "expression_syntax",
                        f"Expression problem in {path}: '{{{{' opened without a closing '}}}}'.",
                        node=label, node_type=ntype, parameter=path.split(".")[-1],
                        suggestion="Close the expression, e.g. ={{ $json.field }}"))
                    continue
                result = expr.analyse(inner)
                for issue in result["issues"]:
                    errors.append(_finding(
                        SEV_ERROR, issue["code"],
                        f"Expression problem in {path}: {issue['message']}",
                        node=label, node_type=ntype, parameter=path.split(".")[-1],
                        suggestion=f"Offending expression: {{{{ {inner.strip()[:120]} }}}}"))
                for ref in result["refs"]:
                    if ref["kind"] == "node" and ref["node"] not in names:
                        errors.append(_finding(
                            SEV_ERROR, "expression_unknown_node",
                            f"{path} references node '{ref['node']}', which does not exist.",
                            node=label, node_type=ntype,
                            suggestion="Reference an existing node by its exact name."))
            for pname, value in (params or {}).items():
                if isinstance(value, str) and expr.looks_hardcoded(value):
                    info.append(_finding(
                        SEV_INFO, "possible_hardcoded_value",
                        f"{pname} looks like a field path but is a plain string; it will be sent "
                        f"literally.", node=label, node_type=ntype, parameter=pname,
                        suggestion='Prefix the value with "=" to make it an expression.'))

    # ---------------------------------------------------------------- connections
    if opts["connections"]:
        outgoing: Dict[str, int] = {n.get("name"): 0 for n in nodes if isinstance(n, dict)}
        incoming: Dict[str, int] = {n.get("name"): 0 for n in nodes if isinstance(n, dict)}
        for source, outputs in (connections or {}).items():
            if source not in incoming:
                errors.append(_finding(SEV_ERROR, "connection_unknown_source",
                                       f"Connections reference '{source}', which is not a node.",
                                       node=source))
                continue
            if not isinstance(outputs, dict):
                errors.append(_finding(SEV_ERROR, "connection_invalid_structure",
                                       f"Connections for '{source}' must be an object of output "
                                       f"types.", node=source))
                continue
            for otype, branches in outputs.items():
                if not isinstance(branches, list):
                    errors.append(_finding(
                        SEV_ERROR, "connection_invalid_structure",
                        f"Output '{otype}' of '{source}' must be a list of branches.",
                        node=source))
                    continue
                for bi, branch in enumerate(branches):
                    if branch is None:
                        continue
                    if not isinstance(branch, list):
                        errors.append(_finding(
                            SEV_ERROR, "connection_invalid_structure",
                            f"Branch {bi} of '{source}' must be a list of targets.", node=source))
                        continue
                    for target in branch:
                        tname = target.get("node") if isinstance(target, dict) else None
                        if not tname:
                            errors.append(_finding(
                                SEV_ERROR, "connection_invalid_target",
                                f"Branch {bi} of '{source}' has a target without a node name.",
                                node=source))
                            continue
                        if tname not in incoming:
                            errors.append(_finding(
                                SEV_ERROR, "connection_unknown_target",
                                f"'{source}' connects to '{tname}', which is not a node.",
                                node=source, suggestion="Point the connection at a real node."))
                            continue
                        idx = target.get("index", 0)
                        if not isinstance(idx, int) or idx < 0:
                            errors.append(_finding(
                                SEV_ERROR, "connection_invalid_index",
                                f"'{source}' → '{tname}' has an invalid output index {idx!r}.",
                                node=source))
                        outgoing[source] = outgoing.get(source, 0) + 1
                        incoming[tname] = incoming.get(tname, 0) + 1

        for node in nodes:
            if not isinstance(node, dict):
                continue
            name = node.get("name")
            ntype = node.get("type") or ""
            record = kb.record_by_type(ntype)
            is_trigger = bool(record and record.get("is_trigger")) or "trigger" in ntype.lower()
            if not name:
                continue
            if not is_trigger and incoming.get(name, 0) == 0 and outgoing.get(name, 0) == 0:
                warnings.append(_finding(
                    SEV_WARNING, "orphan_node",
                    f"'{name}' is not connected to anything.", node=name,
                    suggestion="Connect it, or delete it if it is left over from editing."))
            elif is_trigger and outgoing.get(name, 0) == 0 and len(nodes) > 1:
                warnings.append(_finding(
                    SEV_WARNING, "trigger_not_connected",
                    f"Trigger '{name}' has no outgoing connection, so nothing runs after it.",
                    node=name))

    # ---------------------------------------------------------------- workflow shape
    if nodes and not has_trigger:
        warnings.append(_finding(
            SEV_WARNING, "no_trigger",
            "No trigger node found. The workflow can be imported but cannot run on its own.",
            suggestion=("Add a trigger (scheduleTrigger, webhook, formTrigger, chatTrigger) or "
                        "run it manually.")))

    if len(types_seen) != len(set(types_seen)):
        info.append(_finding(SEV_INFO, "repeated_node_type",
                             "The same node type is used more than once; that is normal for "
                             "multi-step workflows."))

    report = {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "stats": {
            "nodes": len(nodes),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info),
            "node_types": len(set(types_seen)),
        },
        "checked": {
            "structure": True,
            "node_types": True,
            "versions": opts["versions"],
            "required_parameters": opts["required"],
            "types_and_enums": opts["types"],
            "connections": opts["connections"],
            "expressions": opts["expressions"],
            "credentials": opts["credentials"],
        },
        "note": ("Static validation. A valid report means the workflow is configured against the "
                 "documented schemas — it does not mean the workflow has been executed."),
    }
    return report


def summarise(report: Dict[str, Any], limit: int = 5) -> str:
    """One-paragraph human summary of a report."""
    if report.get("valid"):
        return (f"Valid: {report['stats']['nodes']} nodes, "
                f"{report['stats']['warnings']} warning(s).")
    lines = [f"Invalid: {report['stats']['errors']} error(s) in "
             f"{report['stats']['nodes']} node(s)."]
    for e in report["errors"][:limit]:
        where = f"{e.get('node')}: " if e.get("node") else ""
        lines.append(f"- {where}{e['message']}")
    if len(report["errors"]) > limit:
        lines.append(f"- … and {len(report['errors']) - limit} more.")
    return "\n".join(lines)
