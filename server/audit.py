"""Security and reliability audit for a workflow.

Reuses the repository's security scanner (`tools/security_scan.py`) so there is one definition
of "dangerous", then adds workflow-specific checks the file scanner cannot see: plain-HTTP
endpoints, public webhooks, data written to logs, and credentials that look over-scoped.

Severities follow the scanner: critical, high, medium, low, info. Discovered secret values are
redacted before they reach the caller.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

# scanner rule → (severity, category, remediation)
RULE_MAP = {
    "SEC001": ("high", "secrets", "Remove the literal value; attach a credential instead."),
    "SEC002": ("critical", "secrets",
               "Remove the secret, rotate it, and purge it from git history."),
    "SEC003": ("critical", "secrets",
               "Remove the webhook URL, rotate it in Slack/Discord, and use a credential."),
    "SEC004": ("high", "dangerous_node",
               "Remove the node, or restrict who can edit this workflow."),
    "SEC005": ("high", "dangerous_code",
               "Review the code; avoid process/network access from a Code node."),
    "SEC006": ("medium", "ssrf",
               "Do not let workflow input choose the target host of an HTTP Request."),
    "SEC007": ("medium", "exposure",
               "Add authentication to the webhook, or restrict it to a private network."),
    "SEC008": ("low", "pii", "Remove or parameterise the personal data."),
    "SEC009": ("medium", "tls", "Do not disable certificate validation."),
    "SEC011": ("low", "secrets", "Confirm this value is not a key."),
    "SEC012": ("medium", "supply_chain",
               "Pin an exact version of the community package and review its source."),
}


def _scan_workflow(workflow: dict) -> List[Dict[str, Any]]:
    """Run the repository scanner over an in-memory workflow."""
    try:
        from tools.security_scan import scan_workflow
    except Exception:  # pragma: no cover
        return []
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(workflow, fh)
        raw: List[Dict[str, Any]] = []
        scan_workflow(path, raw)
        return raw
    finally:
        if os.path.exists(path):
            os.remove(path)


def audit(workflow: dict, kb=None) -> Dict[str, Any]:
    """Audit a workflow for security and reliability problems."""
    findings: List[Dict[str, Any]] = []
    nodes = [n for n in workflow.get("nodes", []) if isinstance(n, dict)]

    # ---- 1. the repository scanner
    for hit in _scan_workflow(workflow):
        sev, category, fix = RULE_MAP.get(hit["rule"], ("medium", "other",
                                                       "Review this finding."))
        findings.append({
            "severity": sev,
            "category": category,
            "rule": hit["rule"],
            "node": hit.get("node"),
            "message": hit["message"],
            "evidence": hit.get("evidence"),  # already redacted by the scanner
            "remediation": fix,
        })

    # ---- 2. workflow-level checks the file scanner cannot do
    for node in nodes:
        ntype = node.get("type") or ""
        params = node.get("parameters") or {}
        name = node.get("name")

        if ntype.endswith("httpRequest"):
            url = params.get("url")
            if isinstance(url, str) and url.lower().startswith("http://"):
                findings.append({
                    "severity": "medium", "category": "tls", "rule": "AUD001", "node": name,
                    "message": "HTTP Request uses plain http://, so the payload and headers "
                               "travel unencrypted.",
                    "evidence": url[:80],
                    "remediation": "Use https:// unless the endpoint is on localhost.",
                })
            if params.get("allowUnauthorizedCerts") is True:
                findings.append({
                    "severity": "medium", "category": "tls", "rule": "AUD002", "node": name,
                    "message": "Certificate validation is disabled on this request.",
                    "remediation": "Re-enable certificate validation and fix the certificate.",
                })

        if ntype.endswith("webhook"):
            auth = params.get("authentication")
            if auth in (None, "none"):
                findings.append({
                    "severity": "medium", "category": "exposure", "rule": "AUD003", "node": name,
                    "message": "Webhook has no authentication: anyone with the URL can trigger "
                               "the workflow.",
                    "remediation": "Set authentication to Basic/Header auth, or keep the "
                                   "instance private.",
                })

        if ntype.endswith(".code"):
            code = json.dumps(params)
            if re.search(r"console\.log|console\.error", code):
                findings.append({
                    "severity": "low", "category": "data_leak", "rule": "AUD004", "node": name,
                    "message": "Code node writes to the console; log output can contain item "
                               "data and lands in instance logs.",
                    "remediation": "Remove console logging, or log only identifiers.",
                })
            if re.search(r"\$json\b.*(password|token|secret|apikey)", code, re.I):
                findings.append({
                    "severity": "medium", "category": "data_leak", "rule": "AUD005", "node": name,
                    "message": "Code node handles fields that look like credentials.",
                    "remediation": "Avoid passing secrets through item data; use credentials.",
                })

        if kb and (node.get("type") or "").startswith(("n8n-nodes-", "@")):
            record = kb.record_by_type(node.get("type") or "")
            if not record:
                findings.append({
                    "severity": "medium", "category": "supply_chain", "rule": "AUD006",
                    "node": name,
                    "message": f"{node.get('type')} is a third-party package with full host "
                               f"access.",
                    "remediation": "Pin an exact version and check it against "
                                   "community-nodes/shortlist.json.",
                })

    # ---- 3. reliability, not security, but it belongs in the same report
    error_workflow = (workflow.get("settings") or {}).get("errorWorkflow")
    has_external = any((n.get("type") or "").endswith(("httpRequest", "graphql"))
                       for n in nodes)
    if has_external and not error_workflow:
        findings.append({
            "severity": "low", "category": "reliability", "rule": "AUD010", "node": None,
            "message": "The workflow calls external services but has no error workflow set.",
            "remediation": "Set Workflow settings → Error Workflow so failures are reported.",
        })
    for node in nodes:
        if (node.get("type") or "").endswith(("httpRequest", "graphql")):
            if not node.get("retryOnFail"):
                findings.append({
                    "severity": "info", "category": "reliability", "rule": "AUD011",
                    "node": node.get("name"),
                    "message": "No retry policy on a network call.",
                    "remediation": "Enable retryOnFail with 3 tries and a short wait.",
                })

    findings.sort(key=lambda f: -SEVERITY_ORDER.get(f["severity"], 0))
    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    return {
        "workflow": workflow.get("name"),
        "findings": findings,
        "counts": counts,
        "risk": ("critical" if counts.get("critical") else
                 "high" if counts.get("high") else
                 "medium" if counts.get("medium") else
                 "low" if counts.get("low") else "clean"),
        "passed": not (counts.get("critical") or counts.get("high")),
        "note": ("Static audit. Secret values are redacted. A clean report means no known "
                 "pattern matched — it is not a penetration test."),
    }
