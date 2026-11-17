"""Turn a natural-language automation request into a technical plan.

The planner is deliberately conservative. It only names nodes that exist in the knowledge base,
only assigns operations that node actually documents, and when a request mentions something
with no dedicated node it says so instead of inventing one. Every step carries its evidence and
a confidence, and anything unresolved becomes an explicit open question.

A plan is a *proposal*. It has not been executed, and `generate_workflow` still has to build
JSON that validates.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from server.search import SearchEngine, norm, tokens

CLAUSE_SPLIT = re.compile(r"\b(?:and then|then|after that|followed by|next|finally)\b|;|,\s*(?=\w)", re.I)

# Verbs that usually mean "call an API" when no app-specific node is named.
GENERIC_VERBS = {
    "fetch": "get", "call": "get", "request": "get", "download": "get",
    "summarize": "post", "summarise": "post", "translate": "post", "classify": "post",
    "generate": "post", "analyze": "post", "analyse": "post", "embed": "post",
}

VERB_TO_OPS = {
    "save": ["insert", "upsert", "create", "append", "add", "post"],
    "store": ["insert", "upsert", "create", "append"],
    "insert": ["insert", "upsert", "create", "append"],
    "send": ["send", "post", "notify", "reply"],
    "post": ["post", "send"],
    "get": ["get", "getAll", "list", "read", "search"],
    "fetch": ["get", "getAll", "list", "search"],
    "list": ["getAll", "list", "get"],
    "summarize": ["post", "send"],
    "summarise": ["post", "send"],
    "update": ["update", "patch", "edit"],
    "delete": ["delete", "remove"],
    "create": ["create", "add", "insert"],
    "download": ["download", "get"],
    "upload": ["upload", "create"],
}

API_PHRASES = ("using an api", "via api", "call an api", "using the api", "api call",
               "through an api", "with an api", "rest api")

DB_WORDS = ["database", "db", "table", "sql", "store", "save", "persist", "insert", "upsert"]
NOTIFY_WORDS = ["telegram", "slack", "email", "discord", "whatsapp", "notify", "alert", "message"]
FILTER_WORDS = ["filter", "only", "exclude", "where", "if", "dedupe", "deduplicate", "unique",
                "previously", "already", "seen"]


ACTION_WORDS = ("send", "post", "fetch", "get", "save", "store", "filter", "summarize",
                "summarise", "create", "update", "delete", "notify", "upload", "download",
                "query", "insert", "append", "call", "run", "check", "write", "read")


def _clauses(request: str, se: Optional["SearchEngine"] = None) -> List[str]:
    """Split a request into actionable clauses.

    `and` is only a boundary when the second half starts a new action or names a new app —
    "post it to Slack and Telegram" is one step, "fetch the weather and post it to Slack" is two.
    """
    parts = [p.strip(" .") for p in CLAUSE_SPLIT.split(request) if p and p.strip(" .")]
    if len(parts) <= 1:
        parts = [p.strip(" .") for p in re.split(r"\band\b", request) if p and p.strip(" .")]
        merged: List[str] = []
        for part in parts:
            low = part.lower()
            starts_action = any(re.match(rf"^{w}\b", low) for w in ACTION_WORDS)
            names_app = bool(se and _find_mentions(part, se))
            if merged and not (starts_action or names_app):
                merged[-1] = f"{merged[-1]} and {part}"
            else:
                merged.append(part)
        parts = merged
    refined: List[str] = []
    for part in parts:
        low = part.lower()
        generic = next((v for v in GENERIC_VERBS if re.search(rf"\b{v}\b", low)), None)
        mention_pos = None
        if se:
            ms = _find_mentions(part, se)
            if ms:
                mention_pos = low.find(ms[0]["matched_text"])
        if generic and " and " in low and mention_pos is not None:
            gpos = low.find(generic)
            if gpos < mention_pos:
                head, _, tail = part.rpartition(" and ")
                refined.extend([head.strip(" ."), tail.strip(" .")])
                continue
        refined.append(part)
    return refined or [request]


def _find_mentions(text: str, se: SearchEngine) -> List[Dict[str, Any]]:
    """Every node whose name or alias appears in the text, longest match first."""
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    hits: Dict[str, Dict[str, Any]] = {}

    for node in se.nodes:
        ntype = node.get("type") or node["id"]
        name = (node.get("name") or "").lower()
        best_len = 0
        matched = None
        if name and len(name) >= 4 and f" {name} " in low:
            best_len, matched = len(name), name
        for alias in se.aliases.get(ntype, []):
            a = alias.lower()
            if len(a) >= 4 and f" {a} " in low and len(a) > best_len:
                best_len, matched = len(a), a
        if matched:
            hits[ntype] = {"node_type": ntype, "name": node.get("name"),
                           "matched_text": matched, "length": best_len,
                           "is_trigger": bool(node.get("trigger"))}
    return sorted(hits.values(), key=lambda h: -h["length"])


def _trigger_for(request: str, se: SearchEngine) -> Dict[str, Any]:
    low = request.lower()
    intent = se.classify(request)

    explicit = [m for m in _find_mentions(request, se) if m["is_trigger"]]
    if explicit:
        m = explicit[0]
        out = {"node_type": m["node_type"], "name": m["name"],
               "reason": f"the request names '{m['matched_text']}'", "confidence": 0.9}
        if "scheduletrigger" in m["node_type"].lower():
            out["parameter_hint"] = _schedule_hint(request.lower())
        return out

    if re.search(r"\b(every|each|daily|hourly|weekly|monthly|morning|midnight|cron|schedule)\b", low):
        res = se.search("schedule trigger", limit=1, trigger_only=True)
        if res["results"]:
            r = res["results"][0]
            return {"node_type": r["workflow_type"], "name": r["name"],
                    "reason": "the request describes a recurring schedule",
                    "confidence": r["confidence"],
                    "parameter_hint": _schedule_hint(low)}

    # "when a new row appears in Google Sheets" is that app's trigger, not a manual start
    if re.search(r"\b(when|whenever|on new|new row|new message|new item|appears|arrives|"
                 r"receives|is created|is updated)\b", low):
        res = se.search(request, limit=5, trigger_only=True)
        if res["results"]:
            best = res["results"][0]
            if best["confidence"] >= 0.3:
                return {"node_type": best["workflow_type"], "name": best["name"],
                        "reason": "the request describes an app event that starts the workflow",
                        "confidence": best["confidence"]}

    if re.search(r"\b(webhook|incoming|http call|callback|post request)\b", low):
        res = se.search("webhook", limit=1, trigger_only=True)
        if res["results"]:
            r = res["results"][0]
            return {"node_type": r["workflow_type"], "name": r["name"],
                    "reason": "the request describes an inbound HTTP call",
                    "confidence": r["confidence"]}

    if re.search(r"\b(form|submission|survey)\b", low):
        res = se.search("form trigger", limit=1, trigger_only=True)
        if res["results"]:
            r = res["results"][0]
            return {"node_type": r["workflow_type"], "name": r["name"],
                    "reason": "the request describes a form submission",
                    "confidence": r["confidence"]}

    if intent["intent"] == "trigger":
        res = se.search(request, limit=1, trigger_only=True)
        if res["results"]:
            r = res["results"][0]
            return {"node_type": r["workflow_type"], "name": r["name"],
                    "reason": "closest trigger match", "confidence": r["confidence"]}

    return {"node_type": "n8n-nodes-base.manualTrigger", "name": "Manual Trigger",
            "reason": "no schedule, webhook or app event was described; a manual trigger keeps "
                      "the workflow runnable while you decide",
            "confidence": 0.35,
            "assumption": True}


def _schedule_hint(low: str) -> Dict[str, Any]:
    m = re.search(r"\b(?:at|around)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", low)
    if m:
        hour = int(m.group(1)) % 24
        if m.group(3) == "pm" and hour < 12:
            hour += 12
        return {"field": "hours", "triggerAtHour": hour,
                "triggerAtMinute": int(m.group(2) or 0)}
    if "hour" in low:
        return {"field": "hours", "hoursInterval": 1}
    return {"field": "days", "triggerAtHour": 9}


def _step_operation(clause: str, node_type: str, se: SearchEngine,
                    record: Optional[dict] = None) -> Optional[Dict[str, Any]]:
    """Pick the operation that best fits the clause, preferring the clause's own verb."""
    ops = se.operations_of(node_type) if hasattr(se, "operations_of") else []
    if not ops and record:
        ops = record.get("operations") or []
    if not ops:
        return None

    low = clause.lower()
    preferred = []
    for verb, values in VERB_TO_OPS.items():
        if re.search(rf"\b{verb}(?:s|es)?\b", low):
            preferred.extend(values)

    # the node's own schema defaults are authoritative for "the usual operation"
    defaults = {}
    if record:
        for p in (record.get("node_schema") or {}).get("parameters", []):
            if p.get("name") in ("resource", "operation") and "default" in p:
                defaults[p["name"]] = str(p["default"]).lower()

    def rank(o):
        name = (o.get("operation_value") or o.get("operation") or "").lower()
        res = (o.get("resource_value") or "").lower()
        score = 0
        if defaults.get("operation") and name == defaults["operation"]:
            score += 40
        if defaults.get("resource") and res == defaults["resource"]:
            score += 25
        for i, pref in enumerate(preferred):
            if pref.lower() == name:
                score += 100 - 10 * i
            elif pref.lower() in name:
                score += 40 - 10 * i
        return score

    best = max(ops, key=rank)
    if rank(best) > 0:
        op = best
    else:
        op = se.best_operation(node_type, clause)
    if not op:
        return None
    return {
        "resource": op.get("resource"),
        "operation": op.get("operation"),
        "resource_value": op.get("resource_value"),
        "operation_value": op.get("operation_value"),
        "doc": op.get("doc"),
    }


def plan(request: str, kb, se: Optional[SearchEngine] = None, max_steps: int = 8) -> Dict[str, Any]:
    """Build a workflow plan from a natural-language request."""
    se = se or SearchEngine(kb)
    request = (request or "").strip()
    if not request:
        return {"error": "empty request"}

    intent = se.classify(request)
    clauses = _clauses(request, se)

    # Pick the trigger from the clause that describes one, so "when a new row appears in
    # Google Sheets" pairs with Google Sheets Trigger rather than whichever trigger the whole
    # request happens to mention.
    trigger = None
    trigger_clause = None
    for clause in clauses:
        if re.search(r"\b(when|whenever|on new|new row|new message|appears|arrives|receives|"
                     r"every|each|daily|hourly|schedule|cron|webhook|form)\b", clause.lower()):
            candidate = _trigger_for(clause, se)
            if candidate.get("node_type") != "n8n-nodes-base.manualTrigger":
                trigger = candidate
                # Only drop the clause if it is *purely* about the trigger. "Every morning at 8
                # fetch the weather and post it to Slack" both schedules and acts, so the action
                # still has to become a step.
                has_action = any(re.search(rf"\b{w}\b", clause.lower()) for w in ACTION_WORDS)
                trigger_clause = None if has_action else clause
                break
    if trigger is None:
        trigger = _trigger_for(request, se)

    steps: List[Dict[str, Any]] = []
    open_questions: List[str] = []
    assumptions: List[str] = []
    risks: List[str] = []
    credentials: Dict[str, List[str]] = {}

    for clause in clauses:
        if len(steps) >= max_steps:
            open_questions.append(f"Request truncated at {max_steps} steps: '{clause}'")
            break

        mentions = [m for m in _find_mentions(clause, se) if not m["is_trigger"]]
        low = clause.lower()

        # the clause that produced the trigger is not also an action step
        if trigger_clause and clause == trigger_clause:
            continue

        # the trigger already covers "when a new row appears in Google Sheets"
        if (trigger.get("node_type", "").endswith("Trigger")
                and re.search(r"\b(when|whenever|on new|new row|new message|appears|arrives|"
                              r"receives)\b", low)
                and any(m["node_type"].split(".")[-1].lower().rstrip("trigger")
                        in trigger["node_type"].split(".")[-1].lower()
                        or m["matched_text"] in trigger.get("name", "").lower()
                        for m in mentions)):
            continue

        dedupe_words = ("dedupe", "deduplicate", "duplicate", "previously", "already",
                        "seen", "unique")
        if any(w in low for w in dedupe_words):
            # "filter out the ones we have already seen" is cross-run deduplication, which a
            # Filter node cannot do — it has no memory of previous executions.
            rec = kb.record_by_type("n8n-nodes-base.removeDuplicates")
            if rec:
                steps.append({
                    "order": len(steps) + 1,
                    "purpose": clause,
                    "node_type": "n8n-nodes-base.removeDuplicates",
                    "node_name": _unique_name(rec.get("name"), steps),
                    "category": rec.get("category"),
                    "type_version": rec.get("type_version"),
                    "operation": _step_operation(clause, "n8n-nodes-base.removeDuplicates",
                                                 se, rec),
                    "confidence": 0.75,
                    "why": [f"'{clause}' implies deduplication",
                            "a Filter node has no memory of earlier executions"],
                    "note": ("Cross-run deduplication needs a stable key and stored history; "
                             "confirm how history is persisted."),
                })
                risks.append("Deduplication across runs needs the node's history store "
                             "(or a database of processed ids) to survive restarts.")
                continue

        # A clause about filtering becomes a logic node, not an app call.
        if any(w in low for w in FILTER_WORDS) and not mentions:
            target = "n8n-nodes-base.removeDuplicates" if any(
                w in low for w in ("dedupe", "deduplicate", "duplicate", "previously",
                                   "already", "unique", "seen")) else "n8n-nodes-base.filter"
            rec = kb.record_by_type(target)
            res = {"results": [{"workflow_type": target,
                                "name": (rec or {}).get("name") or target,
                                "category": (rec or {}).get("category"),
                                "confidence": 0.8}]} if rec else se.search(target, limit=1)
            if res["results"]:
                r = res["results"][0]
                steps.append({
                    "order": len(steps) + 1,
                    "purpose": clause,
                    "node_type": r["workflow_type"],
                    "node_name": _unique_name(r["name"], steps),
                    "category": r["category"],
                    "confidence": round(min(1.0, r["confidence"] + 0.1), 3),
                    "why": [f"'{clause}' describes a filtering step", "matched a logic node"],
                })
                continue

        # "summarize using an API" is an HTTP call, not the Summarize node
        if mentions and any(p in low for p in API_PHRASES):
            mentions = []

        if not mentions:
            verb = next((v for v in GENERIC_VERBS if v in low), None)
            if verb:
                res = se.search("http request", limit=1)
                if res["results"]:
                    r = res["results"][0]
                    steps.append({
                        "order": len(steps) + 1,
                        "purpose": clause,
                        "node_type": r["workflow_type"],
                        "node_name": _unique_name("HTTP Request", steps),
                        "category": r["category"],
                        "confidence": 0.45,
                        "why": [f"no dedicated node is named for '{verb}'",
                                "HTTP Request is the general-purpose fallback"],
                        "note": "Confirm the endpoint, method and response shape.",
                    })
                    open_questions.append(
                        f"Which API or service should '{clause}' call? "
                        f"No dedicated node was named.")
                    continue

        for m in mentions[:2]:
            node_type = m["node_type"]
            record = kb.record_by_type(node_type) or {}
            op = _step_operation(clause, node_type, se, record)
            required = [p["name"] for p in (record.get("node_schema") or {}).get("parameters", [])
                        if p.get("required")]
            creds = record.get("credential_types") or []
            for c in creds:
                credentials.setdefault(c, []).append(record.get("name") or node_type)
            if m["matched_text"] in ("database", "db", "sql", "table", "store"):
                open_questions.append(
                    f"Which database should '{clause}' write to? "
                    f"{record.get('name')} is shown as the default choice.")
                assumptions.append(
                    f"{record.get('name')} used for '{m['matched_text']}'; confirm the product.")
            steps.append({
                "order": len(steps) + 1,
                "purpose": clause,
                "node_type": node_type,
                "node_name": _unique_name(record.get("name") or m["name"], steps),
                "category": record.get("category"),
                "type_version": record.get("type_version"),
                "operation": op,
                "required_parameters": required,
                "credentials": creds,
                "confidence": round(min(1.0, 0.55 + 0.1 * (1 if op else 0)
                                        + (0.15 if m["length"] > 8 else 0)), 3),
                "why": [f"the request names '{m['matched_text']}'"]
                       + ([f"closest operation: {op['resource']} / {op['operation']}"]
                          if op else ["no operation matched; the node's default applies"]),
            })

    # ---- data contracts and risk heuristics
    if any("dedupe" in s.get("node_type", "") for s in steps):
        risks.append("Deduplication needs a stable key. Without one, duplicates will still slip "
                     "through — consider a database lookup of processed ids.")
    if any("splitinbatches" in s.get("node_type", "").lower() for s in steps):
        risks.append("Loop Over Items needs a matching connection back to the loop node, "
                     "otherwise only the first batch is processed.")
    if any("httprequest" in s.get("node_type", "").lower() for s in steps):
        risks.append("HTTP calls need a timeout and retry policy; add an error workflow.")
    if any(w in request.lower() for w in ("paginate", "pagination", "all pages", "next page")):
        risks.append("Pagination is not automatic: the API's cursor or page parameter has to be "
                     "threaded through a loop.")
    if re.search(r"\b(rate limit|429|throttle)\b", request.lower()):
        risks.append("Rate limits: add a Wait node or retry with backoff between calls.")
    if not any(s.get("node_type", "").endswith("Trigger") or "trigger" in s.get("node_type", "")
               for s in steps):
        pass
    if trigger.get("assumption"):
        assumptions.append("Trigger chosen is a placeholder; confirm how the workflow should start.")

    external = [s for s in steps if "httprequest" in (s.get("node_type") or "").lower()
                or s.get("credentials")]
    error_handling = {
        "workflow_error_workflow": True,
        "retry_on_network_nodes": bool(external),
        "retry_policy": {"maxTries": 3, "waitBetweenTries": 2000} if external else None,
        "failure_notification": "send a message to the same channel used for results"
                                if any(w in request.lower() for w in NOTIFY_WORDS) else None,
    }

    for s in steps:
        if not s.get("operation") and s.get("category") == "app-node":
            open_questions.append(
                f"{s['node_name']}: which operation? The request does not say what to do with "
                f"'{s['purpose']}'.")

    data_flow = []
    prev = trigger.get("name") or "trigger"
    for s in steps:
        data_flow.append({"from": prev, "to": s["node_name"],
                          "carries": "item data (JSON)"})
        prev = s["node_name"]

    return {
        "objective": request,
        "intent": intent,
        "trigger": trigger,
        "steps": steps,
        "sequence": [trigger.get("name") or "trigger"] + [s["node_name"] for s in steps],
        "connections": data_flow,
        "credentials": [{"type": k, "used_by": sorted(set(v))} for k, v in credentials.items()],
        "error_handling": error_handling,
        "risks": risks,
        "open_questions": open_questions,
        "assumptions": assumptions,
        "data_transformations": [
            {"step": s["node_name"], "purpose": s["purpose"]}
            for s in steps if any(w in s["purpose"].lower()
                                  for w in ("filter", "summar", "transform", "format", "map"))
        ],
        "confidence": round(sum(s["confidence"] for s in steps) / len(steps), 3) if steps else 0.0,
        "status": "proposed",
        "note": ("Plan only — nothing has been executed. Steps come from the knowledge base; "
                 "verify credentials, endpoints and field names before running."),
    }


def _unique_name(base: str, steps: List[Dict[str, Any]]) -> str:
    name = (base or "Step").strip()
    existing = {s["node_name"] for s in steps}
    if name not in existing:
        return name
    i = 2
    while f"{name} {i}" in existing:
        i += 1
    return f"{name} {i}"
