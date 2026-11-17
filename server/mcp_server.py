#!/usr/bin/env python3
"""MCP server for the n8n Automation Hub: a workflow engineering assistant.

Speaks the Model Context Protocol over stdio — newline-delimited JSON-RPC 2.0, one message per
line, nothing but protocol messages on stdout (logs go to stderr).

    python3 server/mcp_server.py

Twenty tools in five groups:

    discovery   search_operations, search_nodes, get_node, get_operation, list_triggers,
                resolve_enum, search_community_nodes, search_templates, get_template
    validation  validate_workflow, audit_workflow, analyze_data_flow, debug_workflow
    authoring   plan_workflow, generate_workflow
    live n8n    test_workflow, execute_workflow, get_execution_status, get_execution_data,
                get_execution_error   (all require N8N_BASE_URL + N8N_API_KEY)

Every tool returns the same envelope: `content[0].text` holds pretty JSON for clients that
only read text, and `structuredContent` carries the same object for clients that support it.
"""
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server import analysis, audit as audit_mod, debugger, generator, planner, validation
from server.kb import KnowledgeBase
from server.n8n_api import N8nClient, N8nError, N8nNotConfigured
from server.search import SearchEngine
from server.templates import TemplateLibrary

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "n8n-automation-hub", "version": "1.3.0"}
MAX_TEXT = 60000

KB = KnowledgeBase()
SE = SearchEngine(KB)
TEMPLATES = TemplateLibrary()
N8N = N8nClient.from_env()


# ---------------------------------------------------------------- envelope
def ok(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def err(msg_id, code, message, data=None):
    e = {"code": code, "message": message}
    if data:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": e}


def result(payload, is_error=False):
    """Uniform tool result: text JSON plus structuredContent."""
    if isinstance(payload, str):
        structured = {"text": payload}
        body = payload
    else:
        structured = payload
        body = json.dumps(payload, indent=2, ensure_ascii=False)
    if len(body) > MAX_TEXT:
        body = body[:MAX_TEXT] + f"\n\n[truncated: {len(body)} chars total]"
    out = {"content": [{"type": "text", "text": body}], "isError": is_error}
    if not is_error:
        out["structuredContent"] = structured
    return out


def as_workflow(value):
    """Accept a workflow as an object or as a JSON string."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    raise ValueError("workflow must be an object or a JSON string")


def with_docs(rows):
    """Attach the documentation URL from the knowledge base to search rows."""
    for r in rows:
        rec = KB.record_by_type(r.get("workflow_type") or r.get("node"))
        if rec:
            r.setdefault("doc", rec.get("doc_url"))
            r.setdefault("credential_types", rec.get("credential_types") or [])
    return rows


# ---------------------------------------------------------------- tool schemas
CATEGORY_ENUM = ["app-node", "trigger-node", "core-node", "cluster-root-node", "cluster-sub-node"]
WORKFLOW_PARAM = {
    "type": ["object", "string"],
    "description": "Workflow JSON as an object or a JSON string",
}

TOOLS = [
    # ---------------- discovery
    {
        "name": "search_operations",
        "description": (
            "Find which n8n node performs an action. Hybrid search: exact node names, aliases "
            "('rest api' → HTTP Request), operation names, fuzzy terms and intent routing. "
            "Returns the internal resource/operation values workflow JSON needs, a confidence, "
            "and why each result was chosen. Weak matches are dropped rather than padding the "
            "list."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "What you want to do, e.g. 'append a row to a sheet'"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 50},
                "category": {"type": "string", "enum": CATEGORY_ENUM},
                "trigger_only": {"type": "boolean", "default": False},
                "min_confidence": {"type": "number", "default": 0.28, "minimum": 0,
                                   "maximum": 1,
                                   "description": "Results below this are omitted"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_nodes",
        "description": (
            "Find nodes by name or capability without pinning an operation. Same hybrid "
            "ranking as search_operations, node-level results only."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 50},
                "category": {"type": "string", "enum": CATEGORY_ENUM},
                "min_confidence": {"type": "number", "default": 0.28},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_node",
        "description": (
            "Read one node record: identity, versions, credential types and operation list by "
            "default. Add sections for depth: operations, schema (exact parameter schema with "
            "internal option values), params, events, issues, examples."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string",
                         "description": "Node id, workflow type or display name, e.g. Gmail"},
                "sections": {"type": "array",
                             "items": {"type": "string",
                                       "enum": ["operations", "schema", "params", "events",
                                                "issues", "examples"]}},
            },
            "required": ["node"],
        },
    },
    {
        "name": "get_operation",
        "description": "Parameters and options for one operation of a node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "operation": {"type": "string"},
                "resource": {"type": "string", "description": "Optional, to disambiguate"},
            },
            "required": ["node", "operation"],
        },
    },
    {
        "name": "list_triggers",
        "description": "List trigger nodes — how a workflow can start. Filter by app or keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 200},
            },
        },
    },
    {
        "name": "resolve_enum",
        "description": (
            "Translate a display label into the internal value workflow JSON needs "
            "('Append Row' → 'append'). Returns the node's full resource/operation/"
            "authentication option tables."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "label": {"type": "string", "description": "Optional label to match"},
            },
            "required": ["node"],
        },
    },
    {
        "name": "search_community_nodes",
        "description": (
            "Search third-party n8n community node packages, with download counts and top-100 "
            "rank. These are unverified code with full host access: check the repository and "
            "pin an exact version."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 30},
                "min_downloads": {"type": "integer", "default": 0},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_templates",
        "description": (
            "Search reusable workflow templates (pagination, deduplication, scheduled "
            "collection, error notification). Each entry states whether it is validated, "
            "documented by n8n, or actually executed."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tag": {"type": "string", "description": "e.g. pagination, dedupe, error"},
                "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_template",
        "description": "Fetch one template's workflow JSON and its verification status.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    # ---------------- validation and analysis
    {
        "name": "validate_workflow",
        "description": (
            "Schema-aware validation. Checks structure, node types, typeVersion support, "
            "required parameters (visibility-aware, so hidden conditional fields are not "
            "flagged), value types, enum values, connections, expressions (parsed, not "
            "regex-swept), credential references and workflow shape. Returns structured "
            "errors/warnings with a suggestion and documentation link per finding."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": WORKFLOW_PARAM,
                "checks": {
                    "type": "object",
                    "description": ("Toggle checks: required, types, expressions, credentials, "
                                    "connections, versions"),
                    "properties": {k: {"type": "boolean"} for k in
                                   ("required", "types", "expressions", "credentials",
                                    "connections", "versions")},
                },
            },
            "required": ["workflow"],
        },
    },
    {
        "name": "audit_workflow",
        "description": (
            "Security and reliability audit: hardcoded secrets (redacted), dangerous nodes and "
            "code, plain-HTTP endpoints, unauthenticated webhooks, disabled TLS, PII, "
            "third-party packages, log leakage, missing error handling. Findings carry a "
            "severity and a remediation."),
        "inputSchema": {
            "type": "object",
            "properties": {"workflow": WORKFLOW_PARAM},
            "required": ["workflow"],
        },
    },
    {
        "name": "analyze_data_flow",
        "description": (
            "Trace data between nodes: what each node receives, what it emits, which "
            "expressions it uses, and where an expression reads a field the upstream node does "
            "not produce. Accepts optional fixtures to test expressions against sample items. "
            "Simulation only — nothing is executed."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": WORKFLOW_PARAM,
                "fixtures": {
                    "type": "object",
                    "description": "Optional sample items per node name, e.g. "
                                   "{\"HTTP Request\": [{\"id\": 1}]}",
                },
            },
            "required": ["workflow"],
        },
    },
    {
        "name": "debug_workflow",
        "description": (
            "Diagnose a failing workflow from its JSON and an optional execution error message: "
            "root cause, evidence, recommended fix, and a corrected workflow when the repair is "
            "mechanical. Proposals require approval — nothing is applied automatically."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": WORKFLOW_PARAM,
                "error_text": {"type": "string",
                               "description": "The error message an execution produced"},
                "node": {"type": "string", "description": "Node that failed, if known"},
            },
            "required": ["workflow"],
        },
    },
    # ---------------- authoring
    {
        "name": "plan_workflow",
        "description": (
            "Turn a natural-language automation request into a technical plan: trigger, node "
            "sequence, operations, credentials, data flow, error handling, risks and open "
            "questions. Only uses nodes and operations that exist in the knowledge base, and "
            "says so when something has no dedicated node."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {"type": "string"},
                "max_steps": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
            },
            "required": ["request"],
        },
    },
    {
        "name": "generate_workflow",
        "description": (
            "Generate importable workflow JSON from a request or a plan, using real node "
            "schemas: correct types, typeVersion, internal enum values, parameters, "
            "connections, positions, a sticky note, and marked placeholders for values the "
            "request did not supply. Validates the result and repairs mechanical errors. Never "
            "invents credentials and never claims the workflow was executed."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "request": {"type": "string", "description": "Natural-language request"},
                "plan": {"type": "object", "description": "A plan from plan_workflow"},
                "name": {"type": "string"},
            },
        },
    },
    # ---------------- live n8n
    {
        "name": "test_workflow",
        "description": (
            "Validate a workflow and, if an n8n instance is configured, create it as an "
            "inactive draft so you can inspect it in the editor. Never activates, never "
            "overwrites, never deletes. Reports exactly what could not be checked without an "
            "instance."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": WORKFLOW_PARAM,
                "name": {"type": "string"},
                "create_draft": {"type": "boolean", "default": True},
            },
            "required": ["workflow"],
        },
    },
    {
        "name": "execute_workflow",
        "description": (
            "Run a workflow that already exists on the configured instance. Disabled unless "
            "N8N_ALLOW_EXECUTE=1, and requires confirm=true. Returns an execution id to poll."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string"},
                "confirm": {"type": "boolean", "default": False,
                            "description": "Explicit approval to run it"},
            },
            "required": ["workflow_id"],
        },
    },
    {
        "name": "get_execution_status",
        "description": "Status summary of one execution: result, per-node timings, error.",
        "inputSchema": {
            "type": "object",
            "properties": {"execution_id": {"type": "string"}},
            "required": ["execution_id"],
        },
    },
    {
        "name": "get_execution_data",
        "description": (
            "Execution data for one execution, trimmed to per-node item counts and error "
            "state so item payloads do not flood the context."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "execution_id": {"type": "string"},
                "include_items": {"type": "boolean", "default": False,
                                  "description": "Include a small sample of item data"},
                "max_items": {"type": "integer", "default": 3, "minimum": 1, "maximum": 20},
            },
            "required": ["execution_id"],
        },
    },
    {
        "name": "get_execution_error",
        "description": "Just the failure of one execution: node, message, description, and a "
                       "matching fix from the debugger.",
        "inputSchema": {
            "type": "object",
            "properties": {"execution_id": {"type": "string"}},
            "required": ["execution_id"],
        },
    },
]


# ---------------------------------------------------------------- handlers: discovery
def tool_search_operations(a):
    out = SE.search_operations(a["query"], int(a.get("limit", 8)), a.get("category"),
                               bool(a.get("trigger_only")),
                               float(a.get("min_confidence", 0.28)))
    out["results"] = with_docs(out["results"])
    return result(out)


def tool_search_nodes(a):
    out = SE.search_nodes(a["query"], int(a.get("limit", 8)), a.get("category"),
                          float(a.get("min_confidence", 0.28)))
    out["results"] = with_docs(out["results"])
    return result(out)


def tool_get_node(a):
    nid = KB.find_node_id(a["node"])
    if not nid:
        return result({"error": f"unknown node: {a['node']}",
                       "hint": "Use search_nodes to find the id."}, is_error=True)
    rec = KB.record(nid) or {}
    out = {
        "id": rec.get("id"),
        "name": rec.get("name"),
        "category": rec.get("category"),
        "workflow_type": rec.get("workflow_type"),
        "type_version": rec.get("type_version"),
        "type_versions": rec.get("type_versions"),
        "is_trigger": rec.get("is_trigger"),
        "is_ai_tool": rec.get("is_ai_tool"),
        "credential_types": rec.get("credential_types") or [],
        "description": rec.get("description"),
        "operation_count": rec.get("operation_count"),
        "operations": [f"{o['resource']} / {o['operation']}" if o.get("resource")
                       else o["operation"] for o in (rec.get("operations") or [])],
        "doc_url": rec.get("doc_url"),
        "markdown": (rec.get("files") or {}).get("markdown"),
    }
    for s in a.get("sections") or []:
        if s == "operations":
            out["operations_detail"] = rec.get("operations") or []
        elif s == "schema":
            out["node_schema"] = rec.get("node_schema")
        elif s == "params":
            out["parameters"] = rec.get("parameters") or []
        elif s == "events":
            out["events"] = rec.get("events") or []
            out["trigger_methods"] = rec.get("trigger_methods") or []
        elif s == "issues":
            out["common_issues"] = rec.get("common_issues") or []
        elif s == "examples":
            out["examples"] = [{"name": e.get("name"), "node_count": e.get("node_count"),
                                "source_url": e.get("source_url")}
                               for e in (rec.get("examples") or [])]
    out["enums"] = "call resolve_enum for internal resource/operation values"
    return result(out)


def tool_get_operation(a):
    nid = KB.find_node_id(a["node"])
    if not nid:
        return result({"error": f"unknown node: {a['node']}"}, is_error=True)
    rec = KB.record(nid) or {}
    want_op = a["operation"].strip().lower()
    want_res = (a.get("resource") or "").strip().lower()
    matches = [o for o in rec.get("operations") or []
               if o["operation"].strip().lower() == want_op
               and (not want_res or (o.get("resource") or "").strip().lower() == want_res)]
    if not matches:
        matches = [o for o in rec.get("operations") or [] if want_op in o["operation"].lower()]
    if not matches:
        return result({"error": f"no operation '{a['operation']}' on {rec.get('name')}",
                       "available": sorted({o["operation"] for o in rec.get("operations") or []})},
                      is_error=True)
    return result({
        "node": rec.get("workflow_type"),
        "matches": [{
            "resource": o.get("resource"), "operation": o.get("operation"),
            "resource_value": o.get("resource_value"),
            "operation_value": o.get("operation_value"),
            "description": o.get("description"), "parameters": o.get("parameters"),
            "options": o.get("options"), "doc": o.get("doc"),
        } for o in matches],
    })


def tool_list_triggers(a):
    rows = KB.list_triggers(a.get("query"), int(a.get("limit", 50)))
    return result({"count": len(rows), "triggers": rows})


def tool_resolve_enum(a):
    out = KB.resolve_enum(a["node"], a.get("label"))
    return result(out, is_error="error" in out)


def tool_search_community_nodes(a):
    rows = KB.search_community(a["query"], int(a.get("limit", 8)), int(a.get("min_downloads", 0)))
    if not rows:
        return result({"results": [], "hint": "Try a shorter or broader term."})
    return result({
        "count": len(rows),
        "warning": ("Community nodes are unverified third-party code with full host access. "
                    "Pin an exact version and read the source before installing."),
        "results": rows,
    })


def tool_search_templates(a):
    rows = TEMPLATES.search(a["query"], a.get("tag"), int(a.get("limit", 5)))
    return result({"count": len(rows), "templates": rows,
                   "status_legend": {"validated": "static schema validation passed here",
                                     "documented": "shipped by n8n as an example",
                                     "executed": "ran successfully on a real instance"}})


def tool_get_template(a):
    t = TEMPLATES.get(a["id"])
    if not t:
        return result({"error": f"unknown template: {a['id']}",
                       "available": [x["id"] for x in TEMPLATES.templates]}, is_error=True)
    return result(t)


# ---------------------------------------------------------------- handlers: validation
def tool_validate_workflow(a):
    try:
        wf = as_workflow(a["workflow"])
    except Exception as e:
        return result({"valid": False, "errors": [
            {"severity": "error", "code": "invalid_json", "message": f"not valid JSON: {e}"}]},
            is_error=True)
    checks = a.get("checks") or {}
    report = validation.validate(wf, KB, checks)
    report["summary"] = validation.summarise(report)
    return result(report, is_error=not report["valid"])


def tool_audit_workflow(a):
    try:
        wf = as_workflow(a["workflow"])
    except Exception as e:
        return result({"error": f"not valid JSON: {e}"}, is_error=True)
    return result(audit_mod.audit(wf, KB))


def tool_analyze_data_flow(a):
    try:
        wf = as_workflow(a["workflow"])
    except Exception as e:
        return result({"error": f"not valid JSON: {e}"}, is_error=True)
    return result(analysis.analyze(wf, KB, a.get("fixtures") or {}))


def tool_debug_workflow(a):
    try:
        wf = as_workflow(a["workflow"])
    except Exception as e:
        return result({"error": f"not valid JSON: {e}"}, is_error=True)
    return result(debugger.debug(wf, KB, a.get("error_text"), a.get("node")))


# ---------------------------------------------------------------- handlers: authoring
def tool_plan_workflow(a):
    p = planner.plan(a["request"], KB, SE, int(a.get("max_steps", 8)))
    return result(p, is_error="error" in p)


def tool_generate_workflow(a):
    plan = a.get("plan")
    request = a.get("request")
    if not plan and not request:
        return result({"error": "provide 'request' or 'plan'"}, is_error=True)
    out = generator.generate(request=request, plan=plan, name=a.get("name"), kb=KB, se=SE)
    return result(out, is_error=bool(out.get("error")))


# ---------------------------------------------------------------- handlers: live n8n
def _not_configured(payload):
    payload.update({"configured": False,
                    "how_to_configure": ("set N8N_BASE_URL and N8N_API_KEY, then restart the "
                                         "MCP server")})
    return result(payload)


def tool_test_workflow(a):
    try:
        wf = as_workflow(a["workflow"])
    except Exception as e:
        return result({"error": f"not valid JSON: {e}"}, is_error=True)

    report = validation.validate(wf, KB)
    out = {"validation": report, "summary": validation.summarise(report),
           "executed": False, "created": False}

    if not N8N.configured:
        out["configured"] = False
        out["note"] = ("No n8n instance configured: the workflow was validated statically only. "
                       "Set N8N_BASE_URL and N8N_API_KEY to create a draft and run it.")
        return result(out, is_error=not report["valid"])

    if not a.get("create_draft", True):
        out["configured"] = True
        out["note"] = "Draft creation skipped by request."
        return result(out, is_error=not report["valid"])

    if not report["valid"]:
        out["configured"] = True
        out["note"] = "Not uploaded: fix the validation errors first."
        return result(out, is_error=True)

    try:
        created = N8N.create_draft(wf, a.get("name"))
        out.update({"configured": True, "created": True, **created})
        out["next"] = ("Open the workflow in n8n, attach credentials, fill placeholders, then "
                       "call execute_workflow with confirm=true.")
    except N8nNotConfigured as e:
        out["configured"] = False
        out["note"] = str(e)
    except N8nError as e:
        out["error"] = str(e)
        out["http_status"] = e.status
    return result(out, is_error=bool(out.get("error")))


def tool_execute_workflow(a):
    if not N8N.configured:
        return _not_configured({"executed": False, "reason": "no n8n instance configured"})
    try:
        return result(N8N.execute(a["workflow_id"], bool(a.get("confirm", False))))
    except N8nError as e:
        return result({"executed": False, "error": str(e), "http_status": e.status},
                      is_error=True)


def tool_get_execution_status(a):
    if not N8N.configured:
        return _not_configured({"status": None})
    try:
        execution = N8N.get_execution(a["execution_id"], include_data=False)
        return result(N8N.summarise_execution(execution))
    except N8nError as e:
        return result({"error": str(e), "http_status": e.status}, is_error=True)


def tool_get_execution_data(a):
    if not N8N.configured:
        return _not_configured({"data": None})
    try:
        execution = N8N.get_execution(a["execution_id"], include_data=True)
    except N8nError as e:
        return result({"error": str(e), "http_status": e.status}, is_error=True)

    summary = N8N.summarise_execution(execution)
    data = (execution.get("data") or {}).get("resultData") or {}
    if a.get("include_items"):
        max_items = int(a.get("max_items", 3))
        samples = {}
        for node_name, runs in (data.get("runData") or {}).items():
            items = []
            for run in runs if isinstance(runs, list) else []:
                main = ((run or {}).get("data") or {}).get("main") or [[]]
                for branch in main:
                    for item in (branch or [])[:max_items]:
                        if isinstance(item, dict) and "json" in item:
                            items.append(item["json"])
            if items:
                samples[node_name] = items[:max_items]
        summary["sample_items"] = samples
    else:
        summary["note"] = ("Item payloads omitted. Call again with include_items=true for up "
                          "to max_items samples per node.")
    return result(summary)


def tool_get_execution_error(a):
    if not N8N.configured:
        return _not_configured({"error": None})
    try:
        execution = N8N.get_execution(a["execution_id"], include_data=True)
    except N8nError as e:
        return result({"error": str(e), "http_status": e.status}, is_error=True)

    summary = N8N.summarise_execution(execution)
    failure = summary.get("error")
    if not failure or not failure.get("message"):
        return result({"execution_id": a["execution_id"], "status": summary.get("status"),
                       "failed": False, "note": "This execution did not record an error."})

    workflow = ((execution.get("data") or {}).get("workflowData")) or {}
    diagnosis = debugger.debug(workflow, KB, failure.get("message"), failure.get("node")) \
        if workflow.get("nodes") else None
    return result({"execution_id": a["execution_id"], "status": summary.get("status"),
                   "failed": True, "error": failure,
                   "diagnosis": ({"findings": diagnosis["findings"]} if diagnosis else None)})


HANDLERS = {
    "search_operations": tool_search_operations,
    "search_nodes": tool_search_nodes,
    "get_node": tool_get_node,
    "get_operation": tool_get_operation,
    "list_triggers": tool_list_triggers,
    "resolve_enum": tool_resolve_enum,
    "search_community_nodes": tool_search_community_nodes,
    "search_templates": tool_search_templates,
    "get_template": tool_get_template,
    "validate_workflow": tool_validate_workflow,
    "audit_workflow": tool_audit_workflow,
    "analyze_data_flow": tool_analyze_data_flow,
    "debug_workflow": tool_debug_workflow,
    "plan_workflow": tool_plan_workflow,
    "generate_workflow": tool_generate_workflow,
    "test_workflow": tool_test_workflow,
    "execute_workflow": tool_execute_workflow,
    "get_execution_status": tool_get_execution_status,
    "get_execution_data": tool_get_execution_data,
    "get_execution_error": tool_get_execution_error,
}


# ---------------------------------------------------------------- protocol
def handle(msg):
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return ok(msg_id, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False},
                             "resources": {"subscribe": False, "listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": (
                "n8n workflow engineering assistant. Typical flow: plan_workflow to turn a "
                "request into steps, search_operations/get_operation to confirm nodes and "
                "parameters, resolve_enum for internal values, generate_workflow to build JSON, "
                "validate_workflow and audit_workflow to check it, then test_workflow (and "
                "execute_workflow if an instance is configured) to run it. Resource "
                "n8n://guide/agent explains the workflow format. Live tools need "
                "N8N_BASE_URL and N8N_API_KEY; without them everything else still works."),
        })

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None

    if method == "ping":
        return ok(msg_id, {})

    if method == "tools/list":
        return ok(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if not fn:
            return err(msg_id, -32602, f"unknown tool: {name}", {"available": list(HANDLERS)})
        try:
            return ok(msg_id, fn(args))
        except KeyError as e:
            return err(msg_id, -32602, f"missing argument: {e}")
        except json.JSONDecodeError as e:
            return ok(msg_id, result({"error": f"invalid JSON input: {e}"}, is_error=True))
        except Exception as e:
            traceback.print_exc(file=sys.stderr)  # detail stays in the log, not the response
            return ok(msg_id, result({"error": f"{type(e).__name__}: {e}"}, is_error=True))

    if method == "resources/list":
        return ok(msg_id, {"resources": [
            {"uri": uri, "name": name, "mimeType": "text/markdown", "description": desc}
            for uri, name, desc in [
                ("n8n://guide/agent", "AGENT-GUIDE.md",
                 "How to turn this knowledge base into a valid n8n workflow"),
                ("n8n://guide/knowledge-base", "README.md",
                 "Field-by-field reference for a node record"),
                ("n8n://guide/workflow-conventions", "workflow-conventions.md",
                 "Repository rules for workflow JSON"),
                ("n8n://guide/security", "SECURITY.md",
                 "Secret handling and import safety"),
                ("n8n://guide/mcp-tools", "mcp-tools.md",
                 "Every MCP tool with input and output examples"),
            ]
        ]})

    if method == "resources/templates/list":
        return ok(msg_id, {"resourceTemplates": [
            {"uriTemplate": "n8n://node/{id}", "name": "Node reference",
             "mimeType": "text/markdown",
             "description": "Full Markdown reference for one node, e.g. "
                            "n8n://node/n8n-nodes-base.gmail"},
        ]})

    if method == "resources/read":
        uri = params.get("uri") or ""
        if uri.startswith("n8n://node/"):
            body = KB.node_markdown(uri[len("n8n://node/"):])
            if body is None:
                return err(msg_id, -32602, f"unknown node in uri: {uri}")
            return ok(msg_id, {"contents": [{"uri": uri, "mimeType": "text/markdown",
                                             "text": body[:MAX_TEXT]}]})
        guides = KB.guides()
        if uri == "n8n://guide/mcp-tools":
            guides[uri] = os.path.join(ROOT, "docs", "mcp-tools.md")
        path = guides.get(uri)
        if not path or not os.path.exists(path):
            return err(msg_id, -32602, f"unknown resource: {uri}")
        return ok(msg_id, {"contents": [{"uri": uri, "mimeType": "text/markdown",
                                         "text": open(path, encoding="utf-8").read()[:MAX_TEXT]}]})

    if method == "prompts/list":
        return ok(msg_id, {"prompts": []})

    if method == "shutdown":
        return ok(msg_id, {})

    return err(msg_id, -32601, f"method not found: {method}")


def main():
    print(f"n8n-automation-hub MCP server ready (stdio) — {SERVER_INFO['version']}, "
          f"{len(TOOLS)} tools, n8n {'configured' if N8N.configured else 'not configured'}",
          file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception as e:
            sys.stdout.write(json.dumps(err(None, -32700, f"parse error: {e}")) + "\n")
            sys.stdout.flush()
            continue
        try:
            reply = handle(msg)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            reply = err(msg.get("id"), -32603, f"internal error: {e}")
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
