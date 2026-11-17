#!/usr/bin/env python3
"""Smoke test: drives the MCP server over stdio and asserts the protocol behaves.

    python3 server/test_server.py

Exits non-zero on the first failed assertion, so CI can run it directly.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "mcp_server.py")


def rpc(proc, msg):
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        raise SystemExit(f"server closed the stream after {msg.get('method')}")
    return json.loads(line)


def main():
    proc = subprocess.Popen([sys.executable, SERVER], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True, bufsize=1)
    checks = []

    init = rpc(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "test", "version": "0"}}})
    checks.append(("initialize returns serverInfo", "serverInfo" in init.get("result", {})))
    checks.append(("initialize advertises tools", "tools" in init["result"]["capabilities"]))

    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    tools = rpc(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    checks.append(("eight tools listed", len(names) == 8))
    checks.append(("validate_workflow exposed", "validate_workflow" in names))
    checks.append(("search_operations exposed", "search_operations" in names))
    checks.append(("search_community_nodes exposed", "search_community_nodes" in names))

    def call(i, name, args):
        r = rpc(proc, {"jsonrpc": "2.0", "id": i, "method": "tools/call",
                       "params": {"name": name, "arguments": args}})
        return r["result"]["content"][0]["text"], r["result"].get("isError", False)

    body, is_err = call(3, "search_operations", {"query": "append row to spreadsheet", "limit": 3})
    data = json.loads(body)
    checks.append(("operation search returns rows", data["count"] > 0 and not is_err))
    top = data["results"][0]
    checks.append(("operation carries internal values",
                   bool(top.get("operation_value")) and bool(top.get("resource_value"))))

    body, is_err = call(4, "get_node", {"node": "Gmail"})
    rec = json.loads(body)
    checks.append(("get_node resolves a display name", rec.get("workflow_type") == "n8n-nodes-base.gmail"))
    checks.append(("get_node carries typeVersion", rec.get("type_version") is not None))
    checks.append(("get_node summary stays compact", len(body) < 20000))

    body, is_err = call(5, "get_operation", {"node": "n8n-nodes-base.gmail", "operation": "Send"})
    op = json.loads(body)
    checks.append(("get_operation finds parameters",
                   bool(op["matches"][0]["parameters"]) and not is_err))

    body, is_err = call(6, "resolve_enum", {"node": "n8n-nodes-base.googleSheets",
                                            "label": "Append Row"})
    en = json.loads(body)
    checks.append(("resolve_enum maps a label to a value",
                   any(m.get("operation_value") == "append" for m in en.get("matched", []))))

    body, is_err = call(7, "list_triggers", {"query": "slack", "limit": 5})
    tr = json.loads(body)
    checks.append(("list_triggers filters", tr["count"] >= 1 and not is_err))

    body, is_err = call(15, "search_community_nodes", {"query": "whatsapp", "limit": 3})
    comm = json.loads(body)
    checks.append(("community search returns packages", comm["count"] > 0 and not is_err))
    checks.append(("community search carries download counts",
                   any(r.get("downloads_last_month") for r in comm["results"])))
    checks.append(("community search warns about trust", "unverified" in comm["warning"].lower()))

    good = {"name": "t", "nodes": [
        {"parameters": {}, "id": "11111111-1111-4111-8111-111111111111",
         "name": "Start", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1,
         "position": [0, 0]}],
        "connections": {}}
    body, is_err = call(8, "validate_workflow", {"workflow": good})
    checks.append(("validator passes a clean workflow", json.loads(body)["valid"] and not is_err))

    bad = json.loads(json.dumps(good))
    bad["nodes"][0]["parameters"] = {"apiKey": "sk-test-0000000000000000"}
    body, is_err = call(9, "validate_workflow", {"workflow": bad})
    errs = json.loads(body)["errors"]
    checks.append(("validator rejects a literal secret",
                   any("secret-shaped" in e for e in errs) and is_err))

    dup = json.loads(json.dumps(good))
    dup["nodes"].append(dict(dup["nodes"][0], position=[220, 0]))
    body, _ = call(10, "validate_workflow", {"workflow": dup})
    checks.append(("validator rejects duplicate node names",
                   any("duplicate node name" in e for e in json.loads(body)["errors"])))

    unknown = rpc(proc, {"jsonrpc": "2.0", "id": 11, "method": "tools/call",
                         "params": {"name": "nope", "arguments": {}}})
    checks.append(("unknown tool is an error", "error" in unknown))

    res = rpc(proc, {"jsonrpc": "2.0", "id": 12, "method": "resources/read",
                     "params": {"uri": "n8n://guide/agent"}})
    checks.append(("guide resource is readable",
                   "workflow" in res["result"]["contents"][0]["text"].lower()))

    node_res = rpc(proc, {"jsonrpc": "2.0", "id": 13, "method": "resources/read",
                          "params": {"uri": "n8n://node/n8n-nodes-base.gmail"}})
    checks.append(("node resource template works",
                   "Gmail" in node_res["result"]["contents"][0]["text"]))

    ping = rpc(proc, {"jsonrpc": "2.0", "id": 14, "method": "ping"})
    checks.append(("ping replies", ping.get("result") == {}))

    proc.stdin.close()
    proc.wait(timeout=10)

    failed = [name for name, ok_ in checks if not ok_]
    for name, ok_ in checks:
        print(f"{'PASS' if ok_ else 'FAIL'}  {name}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
