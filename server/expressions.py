"""n8n expression parsing.

n8n expressions live inside `{{ … }}` and are JavaScript-like, with a handful of globals
(`$json`, `$node`, `$now`, …). Evaluating them would mean running user code, which this
server must never do. Instead this module tokenises the expression properly — quote-aware and
brace-aware, not a regex sweep — and reports:

  * syntax problems: unbalanced braces, quotes or brackets
  * which nodes an expression references, so a renamed or deleted node is caught
  * which `$json` paths it reads, so data-flow analysis can check they exist upstream
  * unknown `$` globals, which are almost always a typo

Everything here is static analysis. A clean report means "syntactically sound and references
real nodes", not "will evaluate to a value at runtime".
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Globals n8n exposes inside expressions.
KNOWN_GLOBALS = {
    "$json", "$binary", "$node", "$items", "$item", "$input", "$parameter", "$now",
    "$today", "$vars", "$env", "$execution", "$workflow", "$runIndex", "$itemIndex",
    "$jmespath", "$evaluate", "$if", "$max", "$min", "$number", "$string", "$object",
    "$array", "$boolean", "$date", "$this", "$root", "$j", "$",
}

NODE_REF_PATTERNS = [
    re.compile(r"\$\(\s*['\"]([^'\"]+)['\"]\s*\)"),          # $('Node name')
    re.compile(r"\$node\[\s*['\"]([^'\"]+)['\"]\s*\]"),      # $node["Node name"]
    re.compile(r"\$items\(\s*['\"]([^'\"]+)['\"]"),          # $items('Node name')
    re.compile(r"\$item\(\s*\d+\s*,\s*\d+\s*,\s*['\"]([^'\"]+)['\"]"),  # $item(0,0,'Node')
]

JSON_PATH_RE = re.compile(
    r"\$json((?:\.[A-Za-z_$][\w$]*|\[\s*['\"][^'\"]+['\"]\s*\])+)")
GLOBAL_USE_RE = re.compile(r"(\$[A-Za-z_$][\w$]*)")
PATH_SEG_RE = re.compile(r"\.([A-Za-z_$][\w$]*)|\[\s*['\"]([^'\"]+)['\"]\s*\]")


class ExprIssue(dict):
    pass


def find_expressions(text: str) -> List[Tuple[str, int]]:
    """Return [(expression_inner, offset)] for every balanced `{{ … }}` in a string.

    Quote-aware: `{{ 'a }} b' }}` is one expression, not two.
    """
    out: List[Tuple[str, int]] = []
    i, n = 0, len(text)
    while i < n - 1:
        if text[i] == "{" and text[i + 1] == "{":
            start = i + 2
            j = start
            depth = 0
            quote: Optional[str] = None
            while j < n:
                ch = text[j]
                if quote:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == quote:
                        quote = None
                elif ch in "'\"`":
                    quote = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    if depth > 0:
                        depth -= 1
                    elif j + 1 < n and text[j + 1] == "}":
                        out.append((text[start:j], i))
                        i = j + 2
                        break
                j += 1
            else:
                # unterminated: record what we have so the caller can report it
                out.append((text[start:], i))
                return out
            continue
        i += 1
    return out


def has_unterminated(text: str) -> bool:
    """True when a string opens `{{` more often than it closes `}}`."""
    return isinstance(text, str) and text.count("{{") > text.count("}}")


def _balance_errors(expr: str) -> List[str]:
    errs: List[str] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack: List[str] = []
    quote: Optional[str] = None
    i = 0
    while i < len(expr):
        ch = expr[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch in pairs:
            stack.append(pairs[ch])
        elif ch in ")]}":
            if not stack or stack[-1] != ch:
                errs.append(f"unexpected '{ch}'")
                return errs
            stack.pop()
        i += 1
    if quote:
        errs.append(f"unterminated {quote} string")
    if stack:
        errs.append(f"unclosed {''.join(stack)}")
    return errs


def split_path(path: str) -> List[str]:
    """`$json.a.b[0]["c-d"]` → ['a','b','0','c-d']"""
    segs = []
    for m in PATH_SEG_RE.finditer(path):
        segs.append(m.group(1) or m.group(2))
    return segs


def analyse(expr: str) -> Dict[str, Any]:
    """Analyse one expression body (without the braces)."""
    issues: List[Dict[str, str]] = []
    refs: List[Dict[str, Any]] = []

    for e in _balance_errors(expr):
        issues.append({"code": "expression_syntax", "message": e})

    if not expr.strip():
        issues.append({"code": "expression_empty", "message": "expression is empty"})

    for rx in NODE_REF_PATTERNS:
        for m in rx.finditer(expr):
            refs.append({"kind": "node", "node": m.group(1), "raw": m.group(0)})

    for m in JSON_PATH_RE.finditer(expr):
        refs.append({"kind": "json_path", "path": split_path(m.group(1)), "raw": m.group(0)})

    for m in GLOBAL_USE_RE.finditer(expr):
        name = m.group(1)
        if name == "$" or name.startswith("$$"):
            continue
        if name not in KNOWN_GLOBALS:
            # a property access like obj.$foo is not a global; only flag standalone uses
            before = expr[max(0, m.start() - 1):m.start()]
            if before == ".":
                continue
            issues.append({
                "code": "unknown_global",
                "message": f"'{name}' is not an n8n expression variable",
            })

    return {"expression": expr, "refs": refs, "issues": issues}


def analyse_value(value: Any) -> List[Dict[str, Any]]:
    """Analyse every expression inside one parameter value."""
    if not isinstance(value, str) or "{{" not in value:
        return []
    out = []
    if has_unterminated(value):
        out.append({"expression": value[:120], "refs": [],
                    "issues": [{"code": "expression_syntax",
                                "message": "unterminated expression: '{{' without a closing '}}'"}]})
    for inner, offset in find_expressions(value):
        result = analyse(inner)
        result["offset"] = offset
        out.append(result)
    return out


def iter_node_expressions(parameters: Any, path: str = "parameters") -> Iterable[Tuple[str, str, str]]:
    """Yield (parameter_path, raw_expression, inner) for every expression in a node."""
    if isinstance(parameters, dict):
        for k, v in parameters.items():
            yield from iter_node_expressions(v, f"{path}.{k}")
    elif isinstance(parameters, list):
        for i, v in enumerate(parameters):
            yield from iter_node_expressions(v, f"{path}[{i}]")
    elif isinstance(parameters, str) and "{{" in parameters:
        for inner, _ in find_expressions(parameters):
            yield path, parameters, inner


def referenced_nodes(workflow: dict) -> List[str]:
    """Every node name referenced by any expression in the workflow."""
    names = set()
    for node in workflow.get("nodes", []):
        for _path, _raw, inner in iter_node_expressions(node.get("parameters") or {}):
            for ref in analyse(inner)["refs"]:
                if ref["kind"] == "node":
                    names.add(ref["node"])
    return sorted(names)


def looks_hardcoded(value: str) -> bool:
    """A plain string that reads like it wanted to be an expression."""
    if not isinstance(value, str) or value.startswith("="):
        return False
    return bool(re.search(r"\b(previous|output|response|result|payload)\.\w+", value, re.I))
