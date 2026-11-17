"""Hybrid node search.

The first version of this server ranked operations with plain BM25 over
"name resource operation description". That fails in a specific, repeatable way: a query like
`HTTP Request GET JSON API` matched a Facebook node whose *operation* is literally called
"HTTP Request Method / GET", while the HTTP Request node itself has no operations at all and
was invisible to the index. The same gap hid Filter, Schedule Trigger and every other core
node: no operations, no row, no result.

This module fixes the cause rather than the symptom:

  1. **Every node is a candidate.** Node identity (name, alias, tokens) is scored directly,
     independently of whether the node exposes operations.
  2. **Operations are a second signal, not the index.** An operation can lift its node, but it
     can never outrank a node whose name the user actually typed.
  3. **A lexicon adds the words people use.** "rest api" → HTTP Request, "every morning" →
     Schedule Trigger, "loop over items" → Split In Batches.
  4. **Intent decides the tie-break.** Trigger-shaped queries favour trigger nodes; verb-shaped
     queries favour operations.
  5. **Weak results are dropped, not padded.** A confidence floor is applied before the limit.

Scoring is deliberately explainable: every result carries the reasons it was selected, so a
wrong ranking can be diagnosed instead of guessed at.
"""
from __future__ import annotations

import json
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEXICON = os.path.join(HERE, "aliases.json")

STOP = set("""a an and are as at be by for from has have how in into is it its of on or that the
this to use used using with you your do does i we my can will not what which who node nodes
me some any all please want need""".split())

TOKEN_RE = re.compile(r"[a-z0-9+#]+")

# Confidence bands, used for the `confidence` label and the default floor.
BANDS = ((0.72, "high"), (0.45, "medium"), (0.0, "low"))
DEFAULT_FLOOR = 0.28


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def tokens(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOP and len(t) > 1]


from functools import lru_cache


@lru_cache(maxsize=65536)
def levenshtein(a: str, b: str, cap: int = 3) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fuzzy_contains(needle: str, hay) -> int:
    """Count haystack tokens that equal needle, or are one edit away when long enough.

    Accepts a set for the common case: an exact hit is O(1) and the fuzzy fallback only runs
    for tokens that are not present, against candidates of a similar length.
    """
    if isinstance(hay, (set, frozenset, dict)):
        if needle in hay:
            return 1
        if len(needle) < 5:
            return 0
        for h in hay:
            if len(h) >= 5 and abs(len(h) - len(needle)) <= 1 and levenshtein(needle, h, 1) <= 1:
                return 1
        return 0
    hits = 0
    for h in hay:
        if h == needle:
            hits += 1
        elif len(needle) >= 5 and len(h) >= 5 and levenshtein(needle, h, 1) <= 1:
            hits += 1
    return hits


def band(conf: float) -> str:
    for threshold, label in BANDS:
        if conf >= threshold:
            return label
    return "low"


class SearchEngine:
    """Ranked search over nodes and operations, with intent routing and a fallback path."""

    def __init__(self, kb):
        self.kb = kb
        self._nodes: Optional[List[dict]] = None
        self._ops_by_node: Optional[Dict[str, List[dict]]] = None
        self._lex: Optional[dict] = None
        self._alias_cache: Optional[Dict[str, List[str]]] = None

    # ------------------------------------------------------------------ data
    @property
    def nodes(self) -> List[dict]:
        if self._nodes is None:
            prepared = []
            for row in self.kb.nodes:
                ntype = row.get("type") or row["id"]
                alias_tokens = set()
                for alias in self.aliases.get(ntype, []):
                    alias_tokens.update(tokens(alias))
                name_tokens = set(tokens(row.get("name")))
                desc_tokens = set(tokens(row.get("desc") or "")) | set(
                    tokens(" ".join(row.get("ops") or [])))
                prepared.append({
                    **row,
                    "_name": norm(row.get("name")),
                    "_name_tokens": name_tokens,
                    "_alias_tokens": alias_tokens,
                    "_desc_tokens": desc_tokens,
                    "_strong_tokens": name_tokens | alias_tokens,
                })
            self._nodes = prepared
        return self._nodes

    @property
    def ops_by_node(self) -> Dict[str, List[dict]]:
        """Operations per node, with their token sets precomputed."""
        if self._ops_by_node is None:
            table: Dict[str, List[dict]] = {}
            for op in self.kb.operations:
                entry = dict(op)
                entry["_tokens"] = set(tokens(f"{op.get('operation','')} {op.get('resource','')}"))
                entry["_name_tokens"] = set(tokens(op.get("operation", "")))
                table.setdefault(op["node"], []).append(entry)
            self._ops_by_node = table
        return self._ops_by_node

    @property
    def lexicon(self) -> dict:
        if self._lex is None:
            self._lex = json.load(open(LEXICON, encoding="utf-8")) if os.path.exists(LEXICON) else {}
        return self._lex

    @property
    def aliases(self) -> Dict[str, List[str]]:
        """Lexicon aliases, plus aliases derived for trigger nodes.

        Every `…Trigger` node inherits its app's phrases and gains a "trigger" variant, so
        "when a new row appears in Google Sheets" finds Google Sheets Trigger without a
        hand-maintained entry for every trigger in the library.
        """
        if self._alias_cache is not None:
            return self._alias_cache
        base = {k: list(v) for k, v in (self.lexicon.get("nodes") or {}).items()}
        by_lower = {k.lower(): k for k in base}
        for node in self.kb.nodes:  # raw rows: self.nodes depends on this property
            ntype = node.get("type") or ""
            if not ntype.lower().endswith("trigger"):
                continue
            stem = ntype[:-len("trigger")].lower()
            src = by_lower.get(stem) or by_lower.get(stem.rstrip("_s"))
            if not src:
                continue
            extra = [f"{a} trigger" for a in base[src]] + base[src][:4]
            base[ntype] = list(dict.fromkeys(base.get(ntype, []) + extra))
        self._alias_cache = base
        return base

    # ------------------------------------------------------------------ intent
    def classify(self, query: str) -> Dict[str, Any]:
        q = (query or "").lower()
        q_tokens = tokens(q)
        intents = self.lexicon.get("intents") or {}

        def hits(words):
            return sum(1 for w in words if w in q)

        scores = {
            "trigger": hits(intents.get("trigger", [])),
            "operation": hits(intents.get("operation", [])),
            "pattern": hits(intents.get("pattern", [])),
            "node": hits(intents.get("node", [])),
        }
        # a query that is (almost) exactly a node name is a node lookup
        exact_node = any(n["_name"] and n["_name"] == norm(q) for n in self.nodes)
        if exact_node:
            scores["node"] += 3

        # several clauses and sequencing words mean "describe a workflow", not "find a node"
        clauses = len(re.split(r"\b(?:then|after that|followed by|and then)\b|;", q))
        if clauses > 1:
            scores["pattern"] += 2

        primary = max(scores, key=lambda k: (scores[k], k == "node"))
        if scores[primary] == 0:
            primary = "capability"
        total = sum(scores.values()) or 1
        return {
            "intent": primary,
            "scores": scores,
            "confidence": round(scores[primary] / total, 3) if sum(scores.values()) else 0.0,
            "is_trigger_query": scores["trigger"] > 0,
            "is_pattern_query": scores["pattern"] >= 2 or clauses > 1,
            "token_count": len(q_tokens),
        }

    # ------------------------------------------------------------------ scoring
    def _alias_score(self, node_type: str, query_norm: str, q_tokens: List[str]) -> Tuple[float, Optional[str]]:
        best, which = 0.0, None
        for alias in self.aliases.get(node_type, []):
            a_norm = norm(alias)
            a_tokens = tokens(alias)
            if not a_norm:
                continue
            if query_norm == a_norm:
                return 1.0, alias
            if len(a_norm) >= 4 and (a_norm in query_norm or query_norm in a_norm):
                score = 0.9 if len(a_norm) >= 6 else 0.75
            else:
                q_set = set(q_tokens)
                overlap = sum(1 for t in a_tokens if t in q_set)
                if not overlap:
                    overlap = sum(fuzzy_contains(t, a_tokens) for t in q_tokens)
                score = 0.45 * (overlap / max(1, len(a_tokens))) if overlap else 0.0
            if score > best:
                best, which = score, alias
        return best, which

    def _node_score(self, node: dict, query_norm: str, q_tokens: List[str]) -> Tuple[float, List[str], Dict[str, float]]:
        name = node["_name"]
        name_tokens = node["_name_tokens"]

        exact = 1.0 if name and query_norm == name else 0.0
        substring = 0.0
        if name and not exact and len(name) >= 4:
            if name in query_norm:
                substring = min(1.0, len(name) / max(4, len(query_norm)))
            elif query_norm in name:
                substring = 0.6 * (len(query_norm) / max(4, len(name)))

        covered = sum(fuzzy_contains(t, name_tokens) for t in q_tokens)
        coverage = covered / len(q_tokens) if q_tokens else 0.0

        alias, alias_hit = self._alias_score(node.get("type") or node["id"], query_norm, q_tokens)

        desc_overlap = 0.0
        if q_tokens:
            # exact overlap only: descriptions are long, and fuzzy matching them dominated
            # the runtime without changing the ranking
            desc_hits = sum(1 for t in q_tokens if t in node["_desc_tokens"])
            desc_overlap = desc_hits / len(q_tokens)

        raw = (0.50 * exact + 0.45 * alias + 0.30 * coverage +
               0.15 * substring + 0.10 * min(1.0, desc_overlap))
        score = raw / 1.5

        why = []
        if exact:
            why.append(f"node name matches the query exactly ({node['name']})")
        if alias_hit and alias:
            why.append(f"matches the phrase '{alias}'")
        if coverage >= 0.5:
            why.append(f"name covers {int(round(coverage * 100))}% of the query terms")
        if substring and not exact:
            why.append("node name appears in the query")
        if desc_overlap >= 0.5 and not why:
            why.append("description and operations overlap with the query")

        return score, why, {"exact": exact, "alias": alias, "coverage": coverage,
                            "substring": substring, "desc": desc_overlap}

    def _op_score(self, op: dict, node: dict, q_tokens: List[str], query_norm: str,
                  node_name_hit: bool) -> Tuple[float, List[str], Dict[str, float]]:
        op_tokens = op.get("_tokens") or set(tokens(f"{op.get('operation','')} {op.get('resource','')}"))
        if not op_tokens or not q_tokens:
            return 0.0, [], {}

        exact = 1.0 if norm(op.get("operation", "")) == query_norm else 0.0
        covered = sum(fuzzy_contains(t, op_tokens) for t in q_tokens)
        coverage = covered / len(q_tokens)
        name_hit = 1.0 if node_name_hit else 0.0
        if exact == 0.0 and coverage == 0.0:
            # the node was named but this operation has nothing to do with the clause
            return 0.0, [], {}

        # precision: an operation whose own words are all in the query is a closer fit than a
        # longer operation that merely overlaps ("Append Row" beats "Append or Update Row")
        name_tokens = op.get("_name_tokens") or set(tokens(op.get("operation", "")))
        q_set = set(q_tokens)
        precision = (sum(1 for t in name_tokens if t in q_set) / len(name_tokens)) if name_tokens else 0.0

        raw = (0.40 * exact + 0.30 * coverage + 0.15 * name_hit + 0.10 * precision)
        score = raw / 1.5

        why = []
        if exact:
            why.append(f"operation '{op['operation']}' matches the query exactly")
        if coverage >= 0.4:
            label = f"{op['resource']} / {op['operation']}" if op.get("resource") else op["operation"]
            why.append(f"operation '{label}' covers {int(round(coverage * 100))}% of the terms")
        if name_hit:
            why.append(f"belongs to {node['name']}, which the query names")
        return score, why, {"exact": exact, "coverage": coverage, "name_hit": name_hit,
                            "precision": precision}

    # ------------------------------------------------------------------ search
    def search(self, query: str, limit: int = 8, category: Optional[str] = None,
               trigger_only: bool = False, min_confidence: float = DEFAULT_FLOOR,
               explain: bool = True, force_intent: Optional[str] = None) -> Dict[str, Any]:
        query = (query or "").strip()
        if not query:
            return {"query": query, "results": [], "intent": None,
                    "note": "empty query", "count": 0}

        query_norm = norm(query)
        q_tokens = tokens(query)
        intent = self.classify(query)
        if force_intent:
            intent["intent"] = force_intent

        candidates: List[Dict[str, Any]] = []
        for node in self.nodes:
            if category and node.get("category") != category:
                continue
            if trigger_only and not node.get("trigger"):
                continue

            n_score, n_why, n_parts = self._node_score(node, query_norm, q_tokens)
            # the query names this node, either by name or by a known phrase for it
            node_name_hit = (n_parts.get("exact", 0) > 0
                             or n_parts.get("coverage", 0) >= 0.5
                             or n_parts.get("alias", 0) >= 0.6)

            best_op, best_op_score, best_op_why, best_op_parts = None, 0.0, [], {}
            # only look at operations when they could matter: an exact node-name hit or a
            # node with no operation tokens in common is not worth scanning
            if n_parts.get("exact", 0) < 1.0:
                ops = self.ops_by_node.get(node["id"]) or []
                if ops and (node_name_hit or any(t in node["_strong_tokens"] | node["_desc_tokens"]
                                                 for t in q_tokens)):
                    for op in ops:
                        s, why, parts = self._op_score(op, node, q_tokens, query_norm,
                                                       node_name_hit)
                        if s > best_op_score:
                            best_op, best_op_score, best_op_why = op, s, why
                            best_op_parts = parts

            op_contribution = 0.9 * best_op_score
            if intent["intent"] == "operation":
                op_contribution *= 1.15
            if intent["is_trigger_query"] and node.get("trigger"):
                n_score *= 1.2

            score = max(n_score, op_contribution)
            if score <= 0:
                continue

            # An operation is surfaced when it stands on its own, or when it explains a
            # node-level hit (Telegram + "send message").
            # Surface the operation when it explains the hit: an exact operation name, or a
            # strong term overlap on a node the query already names.
            strong_op = bool(best_op) and (
                best_op_parts.get("exact", 0) >= 1.0
                or (best_op_parts.get("coverage", 0) >= 0.5 and best_op_parts.get("name_hit")))
            show_op = strong_op and best_op_score >= 0.20 and (
                best_op_score >= 0.6 * max(n_score, 1e-6) or intent["intent"] == "operation")

            conf = round(min(1.0, score), 3)
            if conf < min_confidence:
                continue

            result = {
                "node": node["id"],
                "node_id": node["id"],
                "workflow_type": node.get("type") or node["id"],
                "name": node.get("name"),
                "category": node.get("category"),
                "type_version": node.get("tv"),
                "is_trigger": bool(node.get("trigger")),
                "is_ai_tool": bool(node.get("ai_tool")),
                "match": "operation" if show_op else "node",
                "confidence": conf,
                "confidence_band": band(conf),
                "score": round(score * 100, 2),
            }
            if show_op and best_op:
                result["operation"] = {
                    "resource": best_op.get("resource"),
                    "operation": best_op.get("operation"),
                    "resource_value": best_op.get("resource_value"),
                    "operation_value": best_op.get("operation_value"),
                    "description": best_op.get("description"),
                    "doc": best_op.get("doc"),
                }
            if explain:
                result["why"] = (best_op_why if show_op else []) + n_why
                if not result["why"]:
                    result["why"] = ["partial term overlap"]
            candidates.append(result)

        candidates.sort(key=lambda r: (-r["confidence"], r["name"] or ""))

        # Deduplicate by node: keep the best row per node.
        seen, results = set(), []
        for r in candidates:
            if r["node"] in seen:
                continue
            seen.add(r["node"])
            results.append(r)
            if len(results) >= limit:
                break

        out: Dict[str, Any] = {
            "query": query,
            "intent": intent,
            "count": len(results),
            "results": results,
        }

        # ---- fallback: nothing convincing? try the node, then its operations.
        if not results or results[0]["confidence"] < 0.35:
            fb = self._fallback(query, q_tokens, query_norm, category, trigger_only)
            if fb:
                out["fallback"] = fb
                if not results:
                    out["results"] = [fb["node_result"]]
                    out["count"] = 1

        if not results and "fallback" not in out:
            out["note"] = ("No node or operation matched with enough confidence. "
                           "Try a node name, an app name, or a shorter phrase.")
        if intent["is_pattern_query"]:
            out["hint"] = ("This reads like a multi-step automation. "
                           "Use plan_workflow to turn it into a node sequence.")
        return out

    def _fallback(self, query: str, q_tokens: List[str], query_norm: str,
                  category: Optional[str], trigger_only: bool) -> Optional[Dict[str, Any]]:
        """Pick the least-bad node, then rank its operations against the query."""
        best, best_score = None, 0.0
        for node in self.nodes:
            if category and node.get("category") != category:
                continue
            if trigger_only and not node.get("trigger"):
                continue
            score, why, parts = self._node_score(node, query_norm, q_tokens)
            if score > best_score:
                best, best_score = (node, why), score
        if not best or best_score < 0.18:
            return None

        node, why = best
        ops = []
        for op in self.ops_by_node.get(node["id"], []):
            s, _w, _p = self._op_score(op, node, q_tokens, query_norm, True)
            if s > 0:
                ops.append({
                    "resource": op.get("resource"),
                    "operation": op.get("operation"),
                    "resource_value": op.get("resource_value"),
                    "operation_value": op.get("operation_value"),
                    "confidence": round(min(1.0, s), 3),
                })
        ops.sort(key=lambda o: -o["confidence"])
        return {
            "strategy": "closest_node_then_operations",
            "reason": "no result cleared the confidence floor; offering the nearest node",
            "node_result": {
                "node": node["id"],
                "node_id": node["id"],
                "workflow_type": node.get("type") or node["id"],
                "name": node.get("name"),
                "category": node.get("category"),
                "type_version": node.get("tv"),
                "is_trigger": bool(node.get("trigger")),
                "is_ai_tool": bool(node.get("ai_tool")),
                "match": "node",
                "confidence": round(best_score, 3),
                "confidence_band": band(best_score),
                "score": round(best_score * 100, 2),
                "why": why or ["closest partial match"],
            },
            "operations": ops[:10],
        }

    # ------------------------------------------------------------------ variants
    def search_nodes(self, query: str, limit: int = 8, category: Optional[str] = None,
                     min_confidence: float = DEFAULT_FLOOR) -> Dict[str, Any]:
        res = self.search(query, limit=limit, category=category,
                          min_confidence=min_confidence, force_intent="node")
        rows = [r for r in res["results"]]
        return {"query": query, "count": len(rows), "results": rows,
                **({"note": res["note"]} if res.get("note") else {})}

    def search_operations(self, query: str, limit: int = 8, category: Optional[str] = None,
                          trigger_only: bool = False,
                          min_confidence: float = DEFAULT_FLOOR) -> Dict[str, Any]:
        res = self.search(query, limit=max(limit * 2, limit), category=category,
                          trigger_only=trigger_only, min_confidence=min_confidence,
                          force_intent="operation")
        rows = [r for r in res["results"] if r.get("operation")]
        if len(rows) < limit:
            # nodes whose own name matched still deserve a row, flagged as node-level
            extra = [r for r in res["results"] if not r.get("operation")]
            rows.extend(extra[:limit - len(rows)])
        return {"query": query, "count": len(rows[:limit]), "results": rows[:limit],
                "intent": res.get("intent"),
                **({"fallback": res["fallback"]} if res.get("fallback") else {}),
                **({"note": res["note"]} if res.get("note") else {})}

    # ------------------------------------------------------------------ helpers
    def operations_of(self, node_id: str) -> List[dict]:
        return self.ops_by_node.get(node_id, [])

    def best_operation(self, node_id: str, query: str) -> Optional[dict]:
        """Rank one node's operations against a query — used by the planner."""
        node = next((n for n in self.nodes if n["id"] == node_id), None)
        if not node:
            return None
        q_tokens = tokens(query)
        query_norm = norm(query)
        scored = []
        for op in self.ops_by_node.get(node_id, []):
            s, _w, _p = self._op_score(op, node, q_tokens, query_norm, True)
            scored.append((s, op))
        scored.sort(key=lambda t: -t[0])
        return scored[0][1] if scored and scored[0][0] > 0 else None
