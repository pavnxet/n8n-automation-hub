#!/usr/bin/env python3
"""MCP server for the n8n Automation Hub knowledge base.

Speaks the Model Context Protocol over stdio: newline-delimited JSON-RPC 2.0, one
message per line, nothing but protocol messages on stdout (logs go to stderr).

Run it directly:

    python3 server/mcp_server.py

or install it (adds an `n8n-hub-mcp` command):

    pip install -e .

Seven tools, two of them the reason this exists:

    search_operations  which node can do X, with the internal values the JSON needs
    validate_workflow  the same lint CI runs, callable before you hand the JSON over
"""
import json
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.kb import KnowledgeBase  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "n8n-automation-hub", "version": "1.1.0"}
MAX_TEXT = 60000  # characters per tool result; keeps a greedy call from flooding context

KB = KnowledgeBase()


# ---------------------------------------------------------------- helpers
def ok(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def err(msg_id, code, message, data=None):
    e = {"code": code, "message": message}
    if data:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": e}


def text_result(payload, is_error=False):
    if not isinstance(payload, str):
        payload = json.dumps(payload, indent=2, ensure_ascii=False)
    if len(payload) > MAX_TEXT:
        payload = payload[:MAX_TEXT] + f"\n\n[truncated: {len(payload)} chars total]"
    return {"content": [{"type": "text", "text": payload}], "isError": is_error}


def node_summary(rec):
    return {
        "id": rec.get("id"),
        "name": rec.get("name"),
        "category": rec.get("category"),
        "workflow_type": rec.get("workflow_type"),
        "type_version": rec.get("type_version"),
        "is_trigger": rec.get("is_trigger"),
        "is_ai_tool": rec.get("is_ai_tool"),
        "credential_types": rec.get("credential_types") or [],
        "description": rec.get("description"),
        "operation_count": rec.get("operation_count"),
        "operations": [f"{o['resource']} / {o['operation']}" if o.get("resource") else o["operation"]
                       for o in (rec.get("operations") or [])],
        "doc_url": rec.get("doc_url"),
        "markdown": (rec.get("files") or {}).get("markdown"),
    }


# ---------------------------------------------------------------- tool definitions
TOOLS = [
    {
        "name": "search_operations",
        "description": (
            "Find which n8n node can perform an action. Returns ranked resource/operation "
            "pairs with the internal values (resource_value, operation_value) that workflow "
            "JSON requires. Use this first for any 'which node does X' question."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "What you want to do, e.g. 'append row to spreadsheet'"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 50},
                "category": {"type": "string",
                             "enum": ["app-node", "trigger-node", "core-node",
                                      "cluster-root-node", "cluster-sub-node"]},
                "trigger_only": {"type": "boolean", "default": False,
                                 "description": "Only trigger nodes (workflow entry points)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_nodes",
        "description": (
            "Find nodes by name or capability, without pinning an operation. Returns id, "
            "workflow_type, typeVersion, trigger/ai-tool flags and a short description."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 50},
                "category": {"type": "string",
                             "enum": ["app-node", "trigger-node", "core-node",
                                      "cluster-root-node", "cluster-sub-node"]},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_node",
        "description": (
            "Read one node record. Defaults to a compact summary (identity, versions, "
            "credentials, operation list). Add sections for depth: 'operations' (full "
            "operation detail), 'schema' (exact parameter schema with option values), "
            "'params' (documented node-level parameters), 'events', 'issues' (common "
            "errors), 'examples' (bundled example workflows)."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string",
                         "description": "Node id, workflow type or display name, "
                                        "e.g. n8n-nodes-base.gmail, Gmail"},
                "sections": {
                    "type": "array",
                    "items": {"type": "string",
                              "enum": ["operations", "schema", "params", "events",
                                       "issues", "examples"]},
                    "description": "Extra sections to include. Omit for the summary.",
                },
            },
            "required": ["node"],
        },
    },
    {
        "name": "get_operation",
        "description": (
            "Get the documented parameters and options for one specific operation of a node, "
            "e.g. node='n8n-nodes-base.gmail', operation='Send'."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "operation": {"type": "string"},
                "resource": {"type": "string",
                             "description": "Optional resource label to disambiguate, "
                                            "e.g. 'Message'"},
            },
            "required": ["node", "operation"],
        },
    },
    {
        "name": "list_triggers",
        "description": (
            "List trigger nodes — the nodes that start a workflow. Filter by app or keyword. "
            "Use this when deciding how an automation should begin."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional keyword, e.g. 'slack'"},
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 200},
            },
        },
    },
    {
        "name": "resolve_enum",
        "description": (
            "Translate a human label into the internal value a workflow needs. "
            "'Append Row' -> 'append', 'Sheet Within Document' -> 'sheet'. Also returns the "
            "node's full resource/operation/authentication option tables."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node": {"type": "string"},
                "label": {"type": "string",
                          "description": "Optional display label to match, e.g. 'Append Row'"},
            },
            "required": ["node"],
        },
    },
    {
        "name": "validate_workflow",
        "description": (
            "Validate a workflow JSON before handing it to a human. Runs the same checks as "
            "CI: unique node names, known node types, typeVersion present, connections "
            "resolvable, no secret-shaped values, no duplicate positions. Pass the workflow "
            "as an object or a JSON string."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": ["object", "string"],
                    "description": "The workflow JSON, as an object or a JSON string",
                },
            },
            "required": ["workflow"],
        },
    },
]


# ---------------------------------------------------------------- tool handlers
def tool_search_operations(a):
    rows = KB.search_operations(a["query"], int(a.get("limit", 8)),
                                a.get("category"), bool(a.get("trigger_only")))
    if not rows:
        return text_result({"results": [],
                            "hint": "No operation matched. Try search_nodes, or a broader phrase."})
    return text_result({"count": len(rows), "results": rows})


def tool_search_nodes(a):
    rows = KB.search_nodes(a["query"], int(a.get("limit", 8)), a.get("category"))
    return text_result({"count": len(rows), "results": rows})


def tool_get_node(a):
    nid = KB.find_node_id(a["node"])
    if not nid:
        return text_result({"error": f"unknown node: {a['node']}",
                            "hint": "Use search_nodes to find the id."}, is_error=True)
    rec = KB.record(nid) or {}
    out = node_summary(rec)
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
            out["examples"] = [
                {"name": e.get("name"), "node_count": e.get("node_count"),
                 "source_url": e.get("source_url")}
                for e in (rec.get("examples") or [])
            ]
    out["enums"] = "call resolve_enum for internal resource/operation values"
    return text_result(out)


def tool_get_operation(a):
    nid = KB.find_node_id(a["node"])
    if not nid:
        return text_result({"error": f"unknown node: {a['node']}"}, is_error=True)
    rec = KB.record(nid) or {}
    want_op = a["operation"].strip().lower()
    want_res = (a.get("resource") or "").strip().lower()
    matches = []
    for o in rec.get("operations") or []:
        if o["operation"].strip().lower() != want_op:
            continue
        if want_res and o.get("resource", "").strip().lower() != want_res:
            continue
        matches.append(o)
    if not matches:
        for o in rec.get("operations") or []:
            if want_op in o["operation"].lower():
                matches.append(o)
    if not matches:
        return text_result({
            "error": f"no operation '{a['operation']}' on {rec.get('name')}",
            "available": sorted({o["operation"] for o in rec.get("operations") or []}),
        }, is_error=True)
    return text_result({
        "node": rec.get("workflow_type"),
        "matches": [{
            "resource": o.get("resource"),
            "operation": o.get("operation"),
            "resource_value": o.get("resource_value"),
            "operation_value": o.get("operation_value"),
            "description": o.get("description"),
            "parameters": o.get("parameters"),
            "options": o.get("options"),
            "doc": o.get("doc"),
        } for o in matches],
    })


def tool_list_triggers(a):
    rows = KB.list_triggers(a.get("query"), int(a.get("limit", 50)))
    return text_result({"count": len(rows), "triggers": rows})


def tool_resolve_enum(a):
    out = KB.resolve_enum(a["node"], a.get("label"))
    return text_result(out, is_error="error" in out)


def tool_validate_workflow(a):
    wf = a["workflow"]
    if isinstance(wf, str):
        try:
            wf = json.loads(wf)
        except Exception as e:
            return text_result({"valid": False, "errors": [f"not valid JSON: {e}"]},
                               is_error=True)
    try:
        from tools.validate_repo import load_known_types, validate_workflow
    except Exception as e:  # pragma: no cover - only if the repo is incomplete
        return text_result({"error": f"validator unavailable: {e}"}, is_error=True)

    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(wf, fh)
        errs, warns, info = validate_workflow(tmp, load_known_types())
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    return text_result({
        "valid": not errs,
        "errors": errs,
        "warnings": warns,
        "info": info,
    }, is_error=bool(errs))


HANDLERS = {
    "search_operations": tool_search_operations,
    "search_nodes": tool_search_nodes,
    "get_node": tool_get_node,
    "get_operation": tool_get_operation,
    "list_triggers": tool_list_triggers,
    "resolve_enum": tool_resolve_enum,
    "validate_workflow": tool_validate_workflow,
}


# ---------------------------------------------------------------- protocol
def handle(msg):
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        return ok(msg_id, {
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
            },
            "serverInfo": SERVER_INFO,
            "instructions": (
                "Knowledge base for n8n built-in nodes. Typical flow: search_operations to "
                "find the node for a step, get_operation for its parameters, resolve_enum "
                "for the internal values workflow JSON needs, then validate_workflow on the "
                "JSON you produced. Resource n8n://guide/agent explains the workflow format."
            ),
        })

    if method in ("notifications/initialized", "notifications/cancelled"):
        return None  # notifications get no reply

    if method == "ping":
        return ok(msg_id, {})

    if method == "tools/list":
        return ok(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if not fn:
            return err(msg_id, -32602, f"unknown tool: {name}",
                       {"available": list(HANDLERS)})
        try:
            return ok(msg_id, fn(args))
        except KeyError as e:
            return err(msg_id, -32602, f"missing argument: {e}")
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            return ok(msg_id, text_result({"error": f"{type(e).__name__}: {e}"}, is_error=True))

    if method == "resources/list":
        return ok(msg_id, {"resources": [
            {"uri": uri, "name": os.path.basename(p), "mimeType": "text/markdown",
             "description": desc}
            for uri, p, desc in [
                ("n8n://guide/agent", "AGENT-GUIDE.md",
                 "How to turn this knowledge base into a valid n8n workflow"),
                ("n8n://guide/knowledge-base", "README.md",
                 "Field-by-field reference for a node record"),
                ("n8n://guide/workflow-conventions", "workflow-conventions.md",
                 "Repository rules for workflow JSON"),
                ("n8n://guide/security", "SECURITY.md",
                 "Secret handling and import safety"),
            ]
        ]})

    if method == "resources/templates/list":
        return ok(msg_id, {"resourceTemplates": [
            {"uriTemplate": "n8n://node/{id}", "name": "Node reference",
             "mimeType": "text/markdown",
             "description": "The full Markdown reference for one node, e.g. n8n://node/n8n-nodes-base.gmail"},
        ]})

    if method == "resources/read":
        uri = params.get("uri") or ""
        if uri.startswith("n8n://node/"):
            body = KB.node_markdown(uri[len("n8n://node/"):])
            if body is None:
                return err(msg_id, -32602, f"unknown node in uri: {uri}")
            return ok(msg_id, {"contents": [
                {"uri": uri, "mimeType": "text/markdown", "text": body[:MAX_TEXT]}]})
        body = KB.read_guide(uri)
        if body is None:
            return err(msg_id, -32602, f"unknown resource: {uri}")
        return ok(msg_id, {"contents": [
            {"uri": uri, "mimeType": "text/markdown", "text": body[:MAX_TEXT]}]})

    if method in ("prompts/list",):
        return ok(msg_id, {"prompts": []})

    if method == "shutdown":
        return ok(msg_id, {})

    return err(msg_id, -32601, f"method not found: {method}")


def main():
    print(f"n8n-automation-hub MCP server ready (stdio) — {SERVER_INFO['version']}",
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
