"""Optional integration with a real n8n instance over the public REST API.

Design rules, in order of importance:

  1. **Off by default.** With no configuration every tool returns a clear "not configured"
     message instead of guessing or failing obscurely.
  2. **Never activate, never delete.** The client can create an *inactive* draft, read
     workflows and executions, and — only with an explicit second opt-in — run a workflow.
  3. **Never print the key.** It lives in memory, is sent in one header, and is redacted from
     every error message and log line.
  4. **No secrets travel.** Credentials are stripped from a workflow before it is uploaded:
     credential ids from another instance are meaningless and would leak names.

Endpoint reality check: the public API v1 exposes /workflows and /executions. Running a
workflow by id (`POST /workflows/{id}/execute`) is newer than most deployed versions, so the
client probes for it and explains the situation when it is absent.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

DEFAULT_TIMEOUT = 30


def _truthy(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


class N8nNotConfigured(RuntimeError):
    pass


class N8nError(RuntimeError):
    def __init__(self, message: str, status: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class N8nClient:
    """Thin, defensive client. `transport` is injectable so tests need no network."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 allow_execute: Optional[bool] = None, timeout: int = DEFAULT_TIMEOUT,
                 transport=None):
        self.base_url = (base_url or "").rstrip("/")
        self._api_key = api_key or ""
        self.allow_execute = _truthy(os.environ.get("N8N_ALLOW_EXECUTE")) if allow_execute is None \
            else bool(allow_execute)
        self.timeout = timeout
        self._transport = transport or self._urllib_transport

    # ------------------------------------------------------------------ config
    @classmethod
    def from_env(cls, **kwargs) -> "N8nClient":
        return cls(base_url=os.environ.get("N8N_BASE_URL"),
                   api_key=os.environ.get("N8N_API_KEY"), **kwargs)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self._api_key)

    def require(self) -> None:
        if not self.configured:
            raise N8nNotConfigured(
                "No n8n instance is configured. Set N8N_BASE_URL (for example "
                "https://n8n.example.com) and N8N_API_KEY (Settings → n8n API), then restart "
                "the server. Everything except the live-execution tools works without it.")

    def _redact(self, text: str) -> str:
        if not text:
            return ""
        out = str(text)
        if self._api_key:
            out = out.replace(self._api_key, "[redacted]")
        return out[:800]

    # ------------------------------------------------------------------ transport
    def _urllib_transport(self, method: str, url: str, headers: Dict[str, str],
                          body: Optional[bytes]) -> Tuple[int, Any]:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                return resp.status, (json.loads(raw) if raw.strip() else {})
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                payload = json.loads(raw) if raw.strip() else {}
            except Exception:
                payload = {"raw": raw[:400]}
            return e.code, payload
        except urllib.error.URLError as e:
            raise N8nError(self._redact(f"cannot reach {self.base_url}: {e.reason}"))

    def request(self, method: str, path: str, payload: Optional[dict] = None,
                query: Optional[dict] = None) -> Tuple[int, Any]:
        self.require()
        url = f"{self.base_url}/api/v1{path}"
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        headers = {"X-N8N-API-KEY": self._api_key, "Accept": "application/json"}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            return self._transport(method, url, headers, body)
        except N8nError:
            raise
        except Exception as e:  # transport blew up
            raise N8nError(self._redact(f"request failed: {type(e).__name__}: {e}"))

    # ------------------------------------------------------------------ reads
    def status(self) -> Dict[str, Any]:
        """Cheap capability probe: does the instance answer, and what does it expose?"""
        if not self.configured:
            return {"configured": False,
                    "reason": "set N8N_BASE_URL and N8N_API_KEY to enable live integration",
                    "allow_execute": self.allow_execute}
        code, data = self.request("GET", "/workflows", query={"limit": 1})
        out = {"configured": True, "base_url": self.base_url, "reachable": code < 400,
               "http_status": code, "allow_execute": self.allow_execute}
        if code >= 400:
            out["error"] = self._redact(json.dumps(data)[:300])
        # optional: capability map on newer builds
        dcode, _ddata = self.request("GET", "/discover")
        out["discover_endpoint"] = dcode < 400
        return out

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        code, data = self.request("GET", f"/workflows/{urllib.parse.quote(str(workflow_id))}")
        if code >= 400:
            raise N8nError(f"workflow {workflow_id} not readable", code, data)
        return data

    def list_executions(self, workflow_id: Optional[str] = None, limit: int = 20,
                        status: Optional[str] = None) -> Dict[str, Any]:
        code, data = self.request("GET", "/executions",
                                  query={"workflowId": workflow_id, "limit": limit,
                                         "status": status, "includeData": "false"})
        if code >= 400:
            raise N8nError("executions not readable", code, data)
        return data

    def get_execution(self, execution_id: str, include_data: bool = False) -> Dict[str, Any]:
        code, data = self.request(
            "GET", f"/executions/{urllib.parse.quote(str(execution_id))}",
            query={"includeData": "true" if include_data else "false"})
        if code >= 400:
            raise N8nError(f"execution {execution_id} not readable", code, data)
        return data

    # ------------------------------------------------------------------ writes
    @staticmethod
    def strip_credentials(workflow: dict) -> Tuple[dict, list]:
        """Remove credential references: ids are instance-local and names are sensitive."""
        import copy
        wf = copy.deepcopy(workflow)
        stripped = []
        for node in wf.get("nodes", []):
            if isinstance(node, dict) and node.get("credentials"):
                stripped.append({"node": node.get("name"),
                                 "types": sorted(node["credentials"].keys())})
                node.pop("credentials", None)
        return wf, stripped

    def create_draft(self, workflow: dict, name: Optional[str] = None) -> Dict[str, Any]:
        """Create an **inactive** workflow. Never activates anything."""
        wf, stripped = self.strip_credentials(workflow)
        payload = {
            "name": name or wf.get("name") or "Draft from n8n-automation-hub",
            "nodes": wf.get("nodes", []),
            "connections": wf.get("connections", {}),
            "settings": wf.get("settings", {}),
        }
        code, data = self.request("POST", "/workflows", payload)
        if code >= 400:
            raise N8nError("could not create the draft workflow", code, data)
        return {"workflow_id": data.get("id"), "active": data.get("active", False),
                "stripped_credentials": stripped,
                "note": "Created inactive. Attach credentials in the n8n UI before running."}

    def execute(self, workflow_id: str, confirm: bool = False) -> Dict[str, Any]:
        """Run a workflow by id. Requires N8N_ALLOW_EXECUTE=1 *and* confirm=True."""
        if not self.allow_execute:
            return {"executed": False, "reason": "execution is disabled",
                    "how_to_enable": ("set N8N_ALLOW_EXECUTE=1 and restart the server; prefer a "
                                      "staging instance")}
        if not confirm:
            return {"executed": False, "reason": "confirmation required",
                    "how_to_enable": "call again with confirm=true once the target is verified"}
        code, data = self.request(
            "POST", f"/workflows/{urllib.parse.quote(str(workflow_id))}/execute", {})
        if code == 404:
            return {"executed": False, "reason": "endpoint not available",
                    "detail": ("This n8n version's public API has no "
                               "POST /workflows/{id}/execute endpoint. Trigger the workflow "
                               "another way: add a Webhook trigger and call it, use a schedule, "
                               "or run `n8n execute --id <id>` on the host."),
                    "http_status": code}
        if code >= 400:
            raise N8nError("execution request failed", code, data)
        return {"executed": True, "execution_id": data.get("executionId"),
                "waiting_for_webhook": data.get("waitingForWebhook"),
                "note": "Poll get_execution_status with this execution id."}

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def summarise_execution(execution: dict) -> Dict[str, Any]:
        """Shape an execution record for an agent, without dumping item data."""
        data = execution.get("data") or {}
        result = data.get("resultData") or {}
        error = result.get("error") or {}
        run_data = result.get("runData") or {}
        nodes_run = []
        for name, runs in run_data.items():
            if not isinstance(runs, list):
                continue
            first = runs[0] if runs and isinstance(runs[0], dict) else {}
            nodes_run.append({
                "node": name,
                "status": "error" if first.get("error") else "ok",
                "execution_time_ms": first.get("executionTime"),
                "items_out": sum(len(((r or {}).get("data") or {}).get("main", [[]])[0])
                                 for r in runs if isinstance(r, dict)),
            })
        return {
            "id": execution.get("id"),
            "status": execution.get("status"),
            "mode": execution.get("mode"),
            "workflow_id": execution.get("workflowId"),
            "started_at": execution.get("startedAt"),
            "stopped_at": execution.get("stoppedAt"),
            "error": {
                "message": (error.get("message") or "")[:500] or None,
                "node": ((error.get("node") or {}) if isinstance(error.get("node"), dict)
                         else {}).get("name"),
                "description": (error.get("description") or "")[:500] or None,
            } if error else None,
            "nodes": nodes_run,
            "data_included": bool(data),
        }
