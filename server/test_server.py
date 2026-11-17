#!/usr/bin/env python3
"""Protocol and tool tests: drives the MCP server over stdio exactly as a client would.

    python3 server/test_server.py

Exits non-zero on the first failed assertion, so CI can run it directly.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "mcp_server.py")

EXPECTED_TOOLS = {
    # discovery
    "search_operations", "search_nodes", "get_node", "get_operation", "list_triggers",
    "resolve_enum", "search_community_nodes", "search_mcp_servers", "get_mcp_server",
    "search_reference", "get_reference",
    "search_templates", "get_template",
    # validation
    "validate_workflow", "audit_workflow", "analyze_data_flow", "debug_workflow",
    # authoring
    "plan_workflow", "generate_workflow",
    # live n8n
    "test_workflow", "execute_workflow", "get_execution_status", "get_execution_data",
    "get_execution_error",
}


class Client:
    def __init__(self):
        self.proc = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, bufsize=1)
        self.next_id = 0

    def rpc(self, method, params=None):
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise SystemExit(f"server closed the stream during {method}")
        return json.loads(line)

    def call(self, name, args):
        reply = self.rpc("tools/call", {"name": name, "arguments": args})
        if "error" in reply:
            return None, reply["error"], True
        res = reply["result"]
        body = json.loads(res["content"][0]["text"]) if res["content"][0]["text"].strip() \
            .startswith(("{", "[")) else res["content"][0]["text"]
        return body, res, res.get("isError", False)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


def main():
    c = Client()
    checks = []

    def check(name, condition):
        checks.append((name, bool(condition)))

    init = c.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "test", "version": "0"}})
    check("initialize returns serverInfo", "serverInfo" in init.get("result", {}))
    check("initialize advertises tools", "tools" in init["result"]["capabilities"])
    c.proc.stdin.write(json.dumps({"jsonrpc": "2.0",
                                   "method": "notifications/initialized"}) + "\n")
    c.proc.stdin.flush()

    tools = c.rpc("tools/list")
    names = {t["name"] for t in tools["result"]["tools"]}
    check("twenty-four tools listed", len(names) == 24)
    check("every expected tool is registered", EXPECTED_TOOLS <= names)
    check("no duplicate tool names", len(names) == len(tools["result"]["tools"]))
    check("all tools declare an input schema",
          all("inputSchema" in t for t in tools["result"]["tools"]))

    # ---------------- discovery
    body, res, err = c.call("search_operations", {"query": "append row to a spreadsheet",
                                                  "limit": 3})
    check("search returns rows", body["count"] > 0 and not err)
    top = body["results"][0]
    check("search results carry internal values",
          any(r.get("operation") for r in body["results"]))
    check("search result explains itself", bool(top.get("why")))
    check("search result carries a doc link", bool(top.get("doc")))
    check("structuredContent is present", "structuredContent" in res)

    body, _, err = c.call("search_operations", {"query": "HTTP Request GET JSON API", "limit": 3})
    check("http request query resolves to HTTP Request",
          body["results"][0]["workflow_type"] == "n8n-nodes-base.httpRequest")

    body, _, _ = c.call("search_nodes", {"query": "Schedule Trigger", "limit": 2})
    check("node search resolves Schedule Trigger",
          body["results"][0]["workflow_type"] == "n8n-nodes-base.scheduleTrigger")

    body, _, _ = c.call("get_node", {"node": "Gmail"})
    check("get_node resolves a display name", body["workflow_type"] == "n8n-nodes-base.gmail")
    check("get_node carries typeVersion", body["type_version"] is not None)

    body, _, _ = c.call("get_operation", {"node": "n8n-nodes-base.gmail", "operation": "Send"})
    check("get_operation returns parameters", bool(body["matches"][0]["parameters"]))

    body, _, _ = c.call("resolve_enum", {"node": "n8n-nodes-base.googleSheets",
                                         "label": "Append Row"})
    check("resolve_enum maps a label",
          any(m.get("operation_value") == "append" for m in body.get("matched", [])))

    body, _, _ = c.call("list_triggers", {"query": "slack", "limit": 5})
    check("list_triggers filters", body["count"] >= 1)

    body, _, _ = c.call("search_community_nodes", {"query": "whatsapp", "limit": 3})
    check("community search returns packages", body["count"] > 0)
    check("community search warns about trust", "unverified" in body["warning"].lower())

    body, _, _ = c.call("search_mcp_servers", {"query": "postgres", "limit": 3})
    check("mcp catalogue returns servers", body["count"] >= 1)
    check("mcp catalogue reports totals", body["counts"]["servers"] > 1000)
    check("mcp catalogue exposes categories", bool(body["categories"]))

    body, _, _ = c.call("search_mcp_servers", {"query": "fetch", "limit": 5})
    check("official reference servers are findable",
          any(r["trust"] == "official" for r in body["results"]))

    body, _, _ = c.call("get_mcp_server", {"name": "modelcontextprotocol/servers/fetch"})
    check("get_mcp_server returns an entry", body.get("name") == "fetch")

    body, _, err = c.call("get_mcp_server", {"name": "no-such-server-xyz"})
    check("unknown mcp server is a tool error", err)

    body, _, _ = c.call("search_reference", {"query": "$fromAI"})
    check("reference search finds an expression",
          body["count"] >= 1 and any("fromAI" in (r.get("name") or "") for r in body["results"]))
    check("reference search reports layer counts", body["counts"]["expressions"] > 100)

    body, _, _ = c.call("search_reference", {"query": "N8N_ENFORCE_SETTINGS",
                                             "kind": "env-vars"})
    check("reference search filters by kind", body["count"] >= 1)

    body, _, _ = c.call("get_reference", {"kind": "expressions", "name": "$jmespath()"})
    check("get_reference returns an entry", body.get("name") == "$jmespath()")

    body, _, err = c.call("get_reference", {"kind": "expressions", "name": "$nope()"})
    check("unknown reference entry is a tool error", err)

    body, _, _ = c.call("search_templates", {"query": "pagination", "limit": 3})
    check("template search returns entries", body["count"] >= 1)
    tpl_id = body["templates"][0]["id"]
    body, _, _ = c.call("get_template", {"id": tpl_id})
    check("get_template returns a workflow", "workflow" in body)

    # ---------------- validation
    good = {"name": "t", "nodes": [
        {"parameters": {}, "id": "1", "name": "Start", "type": "n8n-nodes-base.manualTrigger",
         "typeVersion": 1, "position": [0, 0]}], "connections": {}}
    body, _, err = c.call("validate_workflow", {"workflow": good})
    check("validator accepts a clean workflow", body["valid"] and not err)
    check("validator reports which checks ran", bool(body["checked"]))

    missing_url = {"name": "t", "nodes": [
        {"parameters": {}, "id": "1", "name": "HTTP Request",
         "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.4, "position": [0, 0]}],
        "connections": {}}
    body, _, err = c.call("validate_workflow", {"workflow": missing_url})
    check("validator rejects a missing required parameter", not body["valid"] and err)
    check("validator names the missing parameter",
          any(e.get("parameter") == "url" for e in body["errors"]))
    check("validator offers a suggestion",
          all("suggestion" in e for e in body["errors"] if e["code"] == "missing_required_parameter"))

    secret_wf = json.loads(json.dumps(good))
    secret_wf["nodes"][0]["parameters"] = {"apiKey": "sk-test-0000000000000000"}
    body, _, err = c.call("validate_workflow", {"workflow": secret_wf})
    check("validator rejects a literal secret",
          any(e["code"] == "secret_in_parameters" for e in body["errors"]) and err)

    dup = json.loads(json.dumps(good))
    dup["nodes"].append(dict(dup["nodes"][0], position=[220, 0]))
    body, _, _ = c.call("validate_workflow", {"workflow": dup})
    check("validator rejects duplicate node names",
          any(e["code"] == "duplicate_node_name" for e in body["errors"]))

    body, _, _ = c.call("audit_workflow", {"workflow": {
        "name": "t", "nodes": [
            {"parameters": {"command": "ls"}, "id": "1", "name": "Run",
             "type": "n8n-nodes-base.executeCommand", "typeVersion": 1,
             "position": [0, 0]}], "connections": {}}})
    check("audit flags a dangerous node",
          any(f["rule"] == "SEC004" for f in body["findings"]))
    check("audit reports a risk level", body["risk"] in
          ("critical", "high", "medium", "low", "clean"))

    body, _, _ = c.call("analyze_data_flow", {"workflow": {
        "name": "t", "nodes": [
            {"parameters": {"assignments": {"assignments": [
                {"name": "title", "value": "x", "type": "string"}]}},
             "id": "1", "name": "Set", "type": "n8n-nodes-base.set",
             "typeVersion": 3.4, "position": [0, 0]},
            {"parameters": {"resource": "message", "operation": "sendMessage",
                            "chatId": "1", "text": "={{ $json.headline }}"},
             "id": "2", "name": "Post", "type": "n8n-nodes-base.telegram",
             "typeVersion": 1, "position": [220, 0]}],
        "connections": {"Set": {"main": [[{"node": "Post", "index": 0}]]}}}})
    check("data-flow analysis finds a missing field",
          any(f["code"] == "field_not_upstream" for f in body["findings"]))
    check("data-flow analysis declares itself a simulation", body["simulated"])

    body, _, _ = c.call("debug_workflow", {
        "workflow": good, "error_text": "401 Unauthorized"})
    check("debugger classifies an auth error",
          any(f["category"] == "authentication" for f in body["findings"]))
    check("debugger requires approval for fixes", body["requires_approval"])

    # ---------------- authoring
    body, _, err = c.call("plan_workflow", {"request": "When a new row appears in Google "
                                                       "Sheets, send it to Telegram"})
    check("planner picks the app trigger",
          body["trigger"]["node_type"] == "n8n-nodes-base.googleSheetsTrigger")
    check("planner returns steps", len(body["steps"]) >= 1)

    body, _, err = c.call("generate_workflow", {"request": "Every morning at 8 fetch the "
                                                           "weather from an API and post it "
                                                           "to Slack"})
    check("generator returns importable JSON", body.get("importable") is True)
    check("generator marks placeholders", bool(body["placeholders"]))
    check("generator does not claim execution", body["executed"] is False)
    check("generator emits a sticky note",
          any(n["type"] == "n8n-nodes-base.stickyNote" for n in body["workflow"]["nodes"]))

    # ---------------- live n8n (not configured in CI)
    body, _, _ = c.call("test_workflow", {"workflow": good})
    check("test_workflow validates without an instance", body["validation"]["valid"])
    check("test_workflow says what it could not do", "configured" in body)

    body, _, _ = c.call("execute_workflow", {"workflow_id": "1", "confirm": True})
    check("execute_workflow refuses without configuration", body.get("executed") is False)

    body, _, _ = c.call("get_execution_status", {"execution_id": "1"})
    check("get_execution_status explains configuration", "how_to_configure" in body)

    # ---------------- protocol edge cases
    reply = c.rpc("tools/call", {"name": "nope", "arguments": {}})
    check("unknown tool is a protocol error", "error" in reply)

    body, _, err = c.call("get_node", {"node": "definitely-not-a-node"})
    check("unknown node is a tool error", err)

    reply = c.rpc("resources/read", {"uri": "n8n://guide/agent"})
    check("guide resource is readable",
          "workflow" in reply["result"]["contents"][0]["text"].lower())
    reply = c.rpc("resources/read", {"uri": "n8n://node/n8n-nodes-base.gmail"})
    check("node resource template works", "Gmail" in reply["result"]["contents"][0]["text"])
    reply = c.rpc("resources/read", {"uri": "n8n://guide/mcp-tools"})
    check("tool documentation resource exists",
          "search_operations" in reply["result"]["contents"][0]["text"])

    reply = c.rpc("ping")
    check("ping replies", reply.get("result") == {})
    reply = c.rpc("no/such/method")
    check("unknown method is an error", reply.get("error", {}).get("code") == -32601)

    c.close()
    failed = [n for n, ok_ in checks if not ok_]
    for name, ok_ in checks:
        print(f"{'PASS' if ok_ else 'FAIL'}  {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
