"""Schema evaluation helpers.

The knowledge base stores each node's parameter schema exactly as n8n ships it
(`node_schema.parameters`). This module turns that schema into answers the validator and
generator need:

  * which parameters are visible for the values a workflow actually sets
  * which visible parameters are required and still empty
  * whether a value matches the declared type
  * which internal enum values are legal

`displayOptions` is the important part. A node like HTTP Request declares dozens of
parameters that only exist for one body type or one authentication method. Flagging those as
"missing" would be worse than not validating at all, so visibility is evaluated first and
only visible parameters are judged.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Parameter types that never carry user input and must not be judged.
NON_INPUT_TYPES = {"notice", "hidden", "button", "color", "callout", "credentialsSelect"}

# Types where an expression ("={{ ... }}") makes static type checking meaningless.
EXPRESSION_TYPES = {"string", "number", "boolean", "json", "dateTime", "options", "multiOptions"}


def is_expression(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("=")


def params_of(record: Optional[dict]) -> List[dict]:
    """Parameter list from a knowledge-base record, or [] when there is no schema."""
    if not record:
        return []
    schema = record.get("node_schema") or {}
    return schema.get("parameters") or []


def param_map(record: Optional[dict]) -> Dict[str, dict]:
    return {p["name"]: p for p in params_of(record) if p.get("name")}


def defaults_of(record: Optional[dict]) -> Dict[str, Any]:
    """Defaults declared by the schema, excluding empty ones.

    n8n pre-fills these when a node is dropped on the canvas, so a required parameter with a
    usable default is not "missing" in a real workflow.
    """
    out: Dict[str, Any] = {}
    for name, p in param_map(record).items():
        if "default" in p and p["default"] not in ("", None, {}, []):
            out[name] = p["default"]
    return out


def effective_values(node_params: Optional[dict], record: Optional[dict]) -> Dict[str, Any]:
    """Workflow parameters merged over schema defaults — what n8n would actually show."""
    values = dict(defaults_of(record))
    for k, v in (node_params or {}).items():
        if v not in ("", None):
            values[k] = v
    return values


def _matches(expected: Any, actual: Any) -> bool:
    """Compare one displayOptions expectation with the value actually set."""
    if isinstance(actual, str) and actual.startswith("="):
        return True  # an expression could be anything; keep the parameter visible
    if isinstance(expected, list):
        if isinstance(actual, list):
            return any(a in expected for a in actual)
        return actual in expected
    if isinstance(actual, list):
        return expected in actual
    return expected == actual


def is_visible(param: dict, values: Dict[str, Any]) -> bool:
    """Evaluate a parameter's displayOptions against the values in play."""
    opts = param.get("displayOptions") or {}
    show = opts.get("show") or {}
    hide = opts.get("hide") or {}

    for key, expected in show.items():
        if not _matches(expected, values.get(key)):
            return False
    for key, expected in hide.items():
        if _matches(expected, values.get(key)):
            return False
    return True


def visible_params(record: Optional[dict], values: Dict[str, Any]) -> List[dict]:
    return [p for p in params_of(record)
            if p.get("name") and p.get("type") not in NON_INPUT_TYPES and is_visible(p, values)]


def _empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def missing_required(record: Optional[dict], node_params: Optional[dict]) -> List[dict]:
    """Visible, required, and still empty after defaults are applied."""
    values = effective_values(node_params, record)
    out = []
    for p in visible_params(record, values):
        if not p.get("required"):
            continue
        if _empty(values.get(p["name"])):
            out.append(p)
    return out


def enum_values(param: dict) -> List[Any]:
    vals = []
    for o in param.get("options") or []:
        if isinstance(o, dict) and "value" in o:
            vals.append(o["value"])
    return vals


def _type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def check_value(param: dict, value: Any) -> List[Tuple[str, str]]:
    """Return [(code, message)] problems for one parameter value.

    Codes: wrong_type, invalid_enum, invalid_option, invalid_resource_locator,
    invalid_json, invalid_date, empty_required.
    """
    problems: List[Tuple[str, str]] = []
    ptype = param.get("type") or "string"
    name = param.get("name")
    display = param.get("displayName") or name

    if ptype in NON_INPUT_TYPES:
        return problems
    if is_expression(value):
        return problems  # resolved at runtime; the expression parser handles syntax

    if ptype == "string":
        if not isinstance(value, str):
            problems.append(("wrong_type", f"{display} expects text, got {_type_name(value)}"))
    elif ptype == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            try:
                float(str(value))
            except (TypeError, ValueError):
                problems.append(("wrong_type",
                                 f"{display} expects a number, got {_type_name(value)}"))
    elif ptype == "boolean":
        if not isinstance(value, bool):
            if str(value).lower() not in ("true", "false"):
                problems.append(("wrong_type",
                                 f"{display} expects true/false, got {_type_name(value)}"))
    elif ptype == "options":
        allowed = enum_values(param)
        if allowed and value not in allowed:
            problems.append(("invalid_enum",
                             f"{display} does not accept {value!r}; allowed: "
                             f"{', '.join(str(a) for a in allowed[:8])}"
                             + (" …" if len(allowed) > 8 else "")))
    elif ptype == "multiOptions":
        if not isinstance(value, list):
            problems.append(("wrong_type", f"{display} expects a list of options"))
        else:
            allowed = enum_values(param)
            bad = [v for v in value if allowed and v not in allowed]
            if bad:
                problems.append(("invalid_enum",
                                 f"{display} does not accept {', '.join(map(str, bad))}"))
    elif ptype == "collection":
        if not isinstance(value, dict):
            problems.append(("wrong_type", f"{display} expects an object of sub-options"))
    elif ptype == "fixedCollection":
        if not isinstance(value, dict):
            problems.append(("wrong_type", f"{display} expects an object keyed by group name"))
        else:
            allowed = {o.get("name") for o in param.get("options") or [] if isinstance(o, dict)}
            unknown = [k for k in value if allowed and k not in allowed]
            if unknown:
                problems.append(("invalid_option",
                                 f"{display} has no group {', '.join(map(str, unknown))}; "
                                 f"allowed: {', '.join(sorted(map(str, allowed)))}"))
    elif ptype == "resourceLocator":
        if not isinstance(value, dict):
            problems.append(("invalid_resource_locator",
                             f"{display} expects a resource locator object "
                             f"({{__rl: true, value: …}}), got {_type_name(value)}"))
        elif value.get("__rl") is not True:
            problems.append(("invalid_resource_locator",
                             f"{display} is a resource locator but __rl is not true"))
        elif _empty(value.get("value")):
            # structurally fine, but nothing is selected yet: importable, not runnable
            problems.append(("empty_resource_locator",
                             f"{display} has no resource selected"))
    elif ptype == "json":
        if isinstance(value, str):
            import json as _json
            try:
                _json.loads(value)
            except Exception as e:
                problems.append(("invalid_json", f"{display} is not valid JSON: {e}"))
        elif not isinstance(value, (dict, list)):
            problems.append(("wrong_type", f"{display} expects JSON, got {_type_name(value)}"))
    elif ptype == "dateTime":
        if not isinstance(value, str):
            problems.append(("wrong_type", f"{display} expects a date string"))
    elif ptype in ("string", "color"):
        pass
    return problems


def visible_names(record: Optional[dict], node_params: Optional[dict]) -> Iterable[str]:
    values = effective_values(node_params, record)
    return [p["name"] for p in visible_params(record, values)]


def normalise_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (label or "").lower())
