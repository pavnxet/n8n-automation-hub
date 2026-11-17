"""Workflow debugging: turn a validation report and/or a runtime error message into a
root cause, the evidence for it, and a concrete fix.

Nothing here is executed, and nothing is applied silently. When a corrected workflow is
produced it is returned as a proposal with `requires_approval: true`; the caller decides.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from server import schema as sch
from server.validation import validate

# (pattern, category, root cause, fix, confidence)
ERROR_PATTERNS = [
    (r"\b401\b|unauthori[sz]ed|invalid[_ ]token|authentication failed|forbidden\b|\b403\b",
     "authentication",
     "The remote API rejected the credential (401/403).",
     "Re-select the credential on this node, confirm it has the scopes the operation needs, "
     "and check whether the token expired. A structurally valid credential reference is not a "
     "working credential.", 0.8),
    (r"\b429\b|rate limit|too many requests|quota exceeded",
     "rate_limit",
     "The API rate limit was hit.",
     "Add a Wait node (or retry with backoff) before this node, and reduce the batch size.",
     0.85),
    (r"ECONNREFUSED|ENOTFOUND|EAI_AGAIN|getaddrinfo|socket hang up|ETIMEDOUT|timeout",
     "network",
     "The connection to the host failed: DNS, refused connection, or a timeout.",
     "Check the URL, confirm the host is reachable from the n8n instance (not just your "
     "machine), and set a timeout plus retries on the node.", 0.8),
    (r"Cannot read propert(y|ies) of (undefined|null)|is not a function|undefined is not",
     "expression_data",
     "An expression read a field that does not exist on the incoming item.",
     "Run the previous node and inspect its output. The field name or nesting is wrong, or the "
     "previous node returned an empty item list.", 0.85),
    (r"JSON parameter needs to be valid JSON|Unexpected token .* in JSON|invalid json",
     "data_format",
     "A parameter that must contain JSON was given something else.",
     "Wrap the value in an expression that produces an object, e.g. "
     "'={{ JSON.stringify($json) }}', or fix the literal JSON.", 0.8),
    (r"credentials? not found|credential.*not.*(found|exists)|no credential",
     "authentication",
     "The credential referenced by the node does not exist on this instance.",
     "Credentials do not travel with an exported workflow. Create the credential on the target "
     "instance, then select it on the node.", 0.9),
    (r"could not find (workflow|node)|workflow could not be started|no trigger",
     "configuration",
     "The workflow has no usable trigger, or a referenced workflow/node is missing.",
     "Add a trigger node, and check that any Execute Workflow node points at a workflow that "
     "exists on this instance.", 0.7),
    (r"SQL|syntax error|relation .* does not exist|column .* does not exist",
     "query",
     "The database rejected the query: syntax, missing table, or missing column.",
     "Run the query by hand against the same database, then fix the SQL or the table mapping.",
     0.75),
    (r"permission denied|insufficient (scope|permission)s?|not authorized to",
     "authentication",
     "The credential is valid but lacks a permission the operation needs.",
     "Add the missing scope to the OAuth app or token, then re-connect the credential.", 0.8),
    (r"ETIMEDOUT|socket.*timeout|request timed out",
     "network",
     "The request took longer than the configured timeout.",
     "Raise the node timeout, or split the work into smaller batches.", 0.7),
    (r"binary|buffer|file.*(too large|not found)|ENOENT",
     "file",
     "A file or binary property referenced by the node is missing or too large.",
     "Check the binary property name, and whether the previous node actually produced a file.",
     0.7),
]


def _match_pattern(text: str) -> Optional[Dict[str, Any]]:
    for pattern, category, cause, fix, conf in ERROR_PATTERNS:
        if re.search(pattern, text, re.I):
            return {"category": category, "root_cause": cause, "fix": fix,
                    "confidence": conf, "matched_pattern": pattern}
    return None


def _find_node(workflow: dict, node_name: Optional[str], error_text: str) -> Optional[dict]:
    nodes = [n for n in workflow.get("nodes", []) if isinstance(n, dict)]
    if node_name:
        for n in nodes:
            if n.get("name") == node_name:
                return n
    # n8n errors often quote the node name: "Node: Telegram"
    m = re.search(r"(?:node|Node)[:\s]+[\"']?([\w \-\./]+)", error_text or "")
    if m:
        candidate = m.group(1).strip()
        for n in nodes:
            if n.get("name") == candidate:
                return n
    return None


def debug(workflow: dict, kb, error_text: Optional[str] = None,
          node_name: Optional[str] = None) -> Dict[str, Any]:
    """Diagnose a workflow, optionally with the error an execution produced."""
    report = validate(workflow, kb)
    findings: List[Dict[str, Any]] = []
    node = _find_node(workflow, node_name, error_text or "")

    # ---- static problems come first: they explain most "it does not work" reports
    for err in report["errors"]:
        findings.append({
            "severity": "high",
            "category": "configuration" if err["code"] != "expression_unknown_node" else "expression",
            "node": err.get("node"),
            "parameter": err.get("parameter"),
            "root_cause": err["message"],
            "evidence": f"validation: {err['code']}",
            "fix": err.get("suggestion") or "Correct the parameter value.",
            "confidence": 0.9,
        })

    # ---- runtime error text, when given
    if error_text:
        match = _match_pattern(error_text)
        if match:
            findings.append({
                "severity": "high",
                "category": match["category"],
                "node": (node or {}).get("name") or node_name,
                "root_cause": match["root_cause"],
                "evidence": error_text.strip()[:500],
                "fix": match["fix"],
                "confidence": match["confidence"],
            })
        else:
            findings.append({
                "severity": "medium",
                "category": "unclassified",
                "node": (node or {}).get("name") or node_name,
                "root_cause": "The error message did not match a known failure pattern.",
                "evidence": error_text.strip()[:500],
                "fix": ("Inspect the failing node's input in the n8n execution view, then check "
                        "the parameters this server reports as incomplete."),
                "confidence": 0.4,
            })

    # ---- node-level detail for the node that failed
    if node:
        record = kb.record_by_type(node.get("type") or "")
        params = node.get("parameters") or {}
        missing = sch.missing_required(record, params) if record else []
        for p in missing:
            findings.append({
                "severity": "high", "category": "configuration", "node": node.get("name"),
                "parameter": p["name"],
                "root_cause": f"Required parameter '{p['name']}' is empty.",
                "evidence": "node schema marks it required",
                "fix": f"Set '{p['name']}' — {p.get('description', '')}".strip(),
                "confidence": 0.95,
            })
        if record and record.get("credential_types") and not node.get("credentials"):
            findings.append({
                "severity": "medium", "category": "authentication", "node": node.get("name"),
                "root_cause": f"{record.get('name')} has no credential attached.",
                "evidence": "node has no 'credentials' key",
                "fix": f"Attach one of: {', '.join(record['credential_types'])}.",
                "confidence": 0.8,
            })

    # ---- a corrected workflow, as a proposal only
    corrected, applied = _propose_fix(workflow, report, kb)

    return {
        "diagnosed": bool(findings),
        "node": (node or {}).get("name") or node_name,
        "findings": findings,
        "validation": report,
        "corrected_workflow": corrected,
        "fixes_proposed": applied,
        "requires_approval": True,
        "note": ("Diagnosis is static unless an execution error was supplied. Any corrected "
                 "workflow is a proposal: review it before importing, and never push it over a "
                 "production workflow without approval."),
        "executed": False,
    }


def _propose_fix(workflow: dict, report: dict, kb) -> tuple:
    """Apply only mechanical, reversible repairs to a copy of the workflow."""
    if report["valid"]:
        return None, []
    import copy
    wf = copy.deepcopy(workflow)
    by_name = {n["name"]: n for n in wf.get("nodes", []) if isinstance(n, dict)}
    applied: List[str] = []

    for err in report["errors"]:
        node = by_name.get(err.get("node"))
        if not node or not err.get("parameter"):
            continue
        record = kb.record_by_type(node.get("type") or "")
        param = sch.param_map(record).get(err["parameter"]) if record else None
        if not param:
            continue
        params = node.setdefault("parameters", {})
        if err["code"] == "invalid_enum":
            allowed = sch.enum_values(param)
            if allowed and params.get(err["parameter"]) not in allowed:
                params[err["parameter"]] = allowed[0]
                applied.append(f"{node['name']}.{err['parameter']} → '{allowed[0]}'")
        elif err["code"] == "wrong_type":
            ptype = param.get("type")
            if ptype == "number":
                try:
                    params[err["parameter"]] = float(params[err["parameter"]])
                    applied.append(f"{node['name']}.{err['parameter']} → number")
                except (TypeError, ValueError):
                    pass
            elif ptype == "string" and not isinstance(params.get(err["parameter"]), str):
                params[err["parameter"]] = json.dumps(params[err["parameter"]])
                applied.append(f"{node['name']}.{err['parameter']} → string")
    return (wf, applied) if applied else (None, [])
