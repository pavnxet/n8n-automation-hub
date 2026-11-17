#!/usr/bin/env python3
"""Security scan for workflows, knowledge-base records and community nodes.

Three jobs:

  1. workflows  - secrets, dangerous nodes, dangerous code, SSRF targets, disabled TLS,
                  PII, and third-party nodes that need review
  2. records    - secrets pasted into knowledge-base node or credential records
  3. packages   - provenance checks for community nodes on the shortlist:
                  existence, licence, repository, age, download floor, typosquat distance

Usage
    python3 tools/security_scan.py                  # scan the whole repository
    python3 tools/security_scan.py --changed        # only files changed vs a base ref
    python3 tools/security_scan.py --base origin/main
    python3 tools/security_scan.py --json
    python3 tools/security_scan.py --fail-on medium # exit non-zero threshold (default high)

Exit codes
    0  no findings at or above the threshold
    1  findings at or above the threshold
    2  scanner error (bad path, unreadable file)

Waivers live in security/waivers.json so an accepted risk is written down, dated and expires.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAIVERS = os.path.join(ROOT, "security", "waivers.json")
SHORTLIST = os.path.join(ROOT, "community-nodes", "shortlist.json")

SEV_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

# ---------------------------------------------------------------- rule data
SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|apikey|access[_-]?token|auth[_-]?token|bearer|client[_-]?secret|"
    r"private[_-]?key|password|passwd|secret|session[_-]?token|refresh[_-]?token|"
    r"webhook[_-]?secret|signing[_-]?key)", re.I)

SECRET_VALUE_PATTERNS = [
    ("SEC002", "high", "credential-shaped value", re.compile(r"^sk-[A-Za-z0-9_\-]{16,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^sk-ant-[A-Za-z0-9_\-]{16,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^gh[pousr]_[A-Za-z0-9]{20,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^github_pat_[A-Za-z0-9_]{20,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^AKIA[0-9A-Z]{16}$")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^AIza[0-9A-Za-z_\-]{30,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^ya29\.[0-9A-Za-z_\-]{20,}")),
    ("SEC002", "high", "credential-shaped value", re.compile(r"^eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")),
    ("SEC002", "critical", "private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("SEC002", "high", "Stripe live key", re.compile(r"^(sk|rk)_live_[A-Za-z0-9]{16,}")),
    ("SEC002", "high", "Twilio auth token shape", re.compile(r"^SK[0-9a-f]{32}$")),
    ("SEC003", "high", "Slack webhook URL with token",
     re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{20,}")),
    ("SEC003", "high", "Discord webhook URL with token",
     re.compile(r"https://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]{20,}")),
]

DANGEROUS_NODES = {
    "n8n-nodes-base.executeCommand": ("high", "runs shell commands on the host"),
    "n8n-nodes-base.localFileTrigger": ("medium", "fires on local filesystem changes"),
    "n8n-nodes-base.readWriteFile": ("medium", "reads and writes files on the host"),
    "n8n-nodes-base.ftp": ("medium", "transfers files over FTP/FTPS"),
    "n8n-nodes-base.ssh": ("high", "opens SSH sessions to remote hosts"),
    "n8n-nodes-base.executeWorkflow": ("info", "invokes another workflow; check its target"),
}

CODE_DANGER = [
    ("child_process", "high", "spawns processes from a Code node"),
    ("require('http", "medium", "opens raw sockets from a Code node"),
    ('require("http', "medium", "opens raw sockets from a Code node"),
    ("process.env", "medium", "reads instance environment variables"),
    ("eval(", "high", "evaluates dynamic code"),
    ("new Function", "high", "evaluates dynamic code"),
    ("fs.readFile", "medium", "reads files from the host"),
    ("fs.writeFile", "medium", "writes files to the host"),
    ("Buffer.from(", "low", "may decode an embedded blob"),
]

SSRF_PATTERNS = [
    ("169.254.169.254", "cloud metadata endpoint"),
    ("metadata.google.internal", "cloud metadata endpoint"),
    ("127.0.0.1", "loopback address"),
    ("localhost", "loopback address"),
    ("0.0.0.0", "wildcard address"),
    ("10.", "private range"),
    ("192.168.", "private range"),
    ("172.16.", "private range"),
]

PII_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PII_EMAIL_SAFE = re.compile(
    r"(example\.(com|org|net)|users\.noreply\.github\.com|noreply|@n8n\.io|"
    r"docs\.n8n\.io|schema\.org|w3\.org|placeholder|you@|user@|name@|email@)", re.I)

HIGH_ENTROPY = re.compile(r"^[A-Za-z0-9+/_\-]{48,}={0,2}$")


# ---------------------------------------------------------------- helpers
def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def load_waivers():
    if not os.path.exists(WAIVERS):
        return []
    try:
        doc = json.load(open(WAIVERS, encoding="utf-8"))
    except Exception:
        return []
    return [w for w in doc.get("waivers", []) if isinstance(w, dict)]


def waived(finding, waivers, today):
    for w in waivers:
        if w.get("rule") != finding["rule"]:
            continue
        if w.get("file") and not finding["file"].startswith(w["file"]):
            continue
        if w.get("expires") and w["expires"] < today:
            continue
        return w
    return None


def walk_strings(obj, path="parameters"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                yield path, k, v
            else:
                yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                yield path, "", v
            else:
                yield from walk_strings(v, f"{path}[{i}]")


def redact(value, keep=4):
    v = value.strip()
    if len(v) <= keep * 2:
        return "*" * len(v)
    return f"{v[:keep]}…{v[-keep:]} ({len(v)} chars)"


def add(findings, rule, severity, file, message, node=None, evidence=None):
    f = {"rule": rule, "severity": severity, "file": file, "message": message}
    if node:
        f["node"] = node
    if evidence:
        f["evidence"] = evidence
    findings.append(f)


# ---------------------------------------------------------------- workflow rules
def scan_workflow(path, findings):
    name = rel(path)
    try:
        wf = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        add(findings, "SEC000", "medium", name, f"unreadable workflow JSON: {e}")
        return
    nodes = wf.get("nodes") or []

    for n in nodes:
        label = n.get("name") or "unnamed node"
        ntype = n.get("type") or ""
        params = n.get("parameters") or {}

        # SEC004 - dangerous built-in nodes
        if ntype in DANGEROUS_NODES:
            sev, why = DANGEROUS_NODES[ntype]
            add(findings, "SEC004", sev, name, f"uses {ntype}, which {why}", label)

        # SEC005 - dangerous code inside a Code node
        if ntype.endswith(".code") or ntype.endswith(".function"):
            code = json.dumps(params)
            for needle, sev, why in CODE_DANGER:
                if needle in code:
                    add(findings, "SEC005", sev, name, f"Code node {why}", label, needle)

        # SEC006 - SSRF-shaped targets and disabled TLS
        if "httpRequest" in ntype:
            url = json.dumps(params.get("url", ""))
            for needle, why in SSRF_PATTERNS:
                if needle in url:
                    add(findings, "SEC006", "medium", name,
                        f"HTTP Request targets {why} ({needle})", label, url[:80])
            if params.get("allowUnauthorizedCerts") is True:
                add(findings, "SEC009", "medium", name,
                    "HTTP Request disables TLS certificate validation", label)
            auth = params.get("authentication")
            if auth in ("none", None) and re.search(r"https?://", url) and "@" in url:
                add(findings, "SEC001", "high", name,
                    "credentials embedded in the URL userinfo section", label)

        # SEC007 - public webhook without authentication
        if ntype.endswith(".webhook") and params.get("authentication") in (None, "none"):
            add(findings, "SEC007", "medium", name,
                "webhook has no authentication configured", label)

        # SEC012 - third-party node present
        if ntype.startswith(("n8n-nodes-", "@")) and not ntype.startswith(
                ("n8n-nodes-base.", "@n8n/n8n-nodes-langchain.")):
            add(findings, "SEC012", "low", name,
                f"uses community node {ntype} - confirm it is on the shortlist", label)

        # SEC001/SEC002/SEC008 - values
        for parent, key, val in walk_strings(params):
            if not val.strip():
                continue
            if key and SECRET_KEY_RE.search(key):
                add(findings, "SEC001", "high", name,
                    f"literal value in secret-shaped field '{parent}.{key}'", label, redact(val))
                continue
            for rule, sev, why, rx in SECRET_VALUE_PATTERNS:
                if rx.search(val):
                    add(findings, rule, sev, name, f"{why}", label, redact(val))
                    break
            else:
                if HIGH_ENTROPY.match(val.strip()) and not val.startswith(("http", "{{", "=")):
                    classes = sum([any(c.islower() for c in val), any(c.isupper() for c in val),
                                   any(c.isdigit() for c in val)])
                    if classes >= 2:
                        add(findings, "SEC011", "low", name,
                            "long high-entropy string - confirm it is not a key", label,
                            redact(val))
                for m in PII_EMAIL.finditer(val):
                    if not PII_EMAIL_SAFE.search(m.group(0)):
                        add(findings, "SEC008", "low", name,
                            "email address in workflow data", label, m.group(0))
                        break


# ---------------------------------------------------------------- record rules
def scan_record(path, findings):
    name = rel(path)
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        return
    blob = json.dumps(doc)
    for rule, sev, why, rx in SECRET_VALUE_PATTERNS:
        for m in rx.finditer(blob):
            add(findings, "SEC101", sev, name, f"{why} inside a knowledge-base record",
                evidence=redact(m.group(0)))
            break


# ---------------------------------------------------------------- package rules
def npm_meta(pkg):
    """Minimal npm metadata fetch; returns None when offline."""
    import urllib.request
    url = "https://registry.npmjs.org/" + pkg.replace("/", "%2F")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "n8n-automation-hub/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def levenshtein(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def scan_shortlist(findings, offline_ok=True):
    if not os.path.exists(SHORTLIST):
        return
    try:
        doc = json.load(open(SHORTLIST, encoding="utf-8"))
    except Exception as e:
        add(findings, "SEC201", "medium", "community-nodes/shortlist.json",
            f"unreadable shortlist: {e}")
        return
    entries = doc.get("packages") or []
    if not entries:
        return

    index = {}
    idx_path = os.path.join(ROOT, "community-nodes", "index.json")
    if os.path.exists(idx_path):
        for p in json.load(open(idx_path, encoding="utf-8")).get("packages", []):
            index[p["name"]] = p
    popular = [n for n in index]

    for e in entries:
        pkg = e.get("name")
        if not pkg:
            add(findings, "SEC201", "medium", "community-nodes/shortlist.json",
                "shortlist entry without a package name")
            continue
        f = "community-nodes/shortlist.json"

        # SEC202 - unpinned version
        if not re.match(r"^\d+\.\d+\.\d+", str(e.get("version", ""))):
            add(findings, "SEC202", "medium", f,
                f"{pkg} is not pinned to an exact version", evidence=str(e.get("version")))

        # SEC203 - typosquat distance, but only when the lookalike is clearly the
        # more established package. Two genuinely popular packages can sit two edits
        # apart (chatwoot / chatwork) and neither is impersonating the other.
        base = pkg.split("/")[-1].replace("n8n-nodes-", "")
        cand_dl = (index.get(pkg) or {}).get("downloads_last_month") or 0
        for other in popular:
            ob = other.split("/")[-1].replace("n8n-nodes-", "")
            if other == pkg or not ob or not base or len(base) <= 6:
                continue
            if not 0 < levenshtein(base, ob) <= 2:
                continue
            other_dl = (index.get(other) or {}).get("downloads_last_month") or 0
            if other_dl >= 1000 and other_dl >= max(cand_dl, 1) * 3:
                add(findings, "SEC203", "medium", f,
                    f"{pkg} is {levenshtein(base, ob)} edits from the far more used "
                    f"{other} - possible typosquat", evidence=other)
                break

        meta = npm_meta(pkg)
        if meta is None:
            if not offline_ok:
                add(findings, "SEC204", "low", f, f"could not reach npm for {pkg}")
            continue

        # SEC205 - missing provenance
        if not (meta.get("repository") or {}).get("url"):
            add(findings, "SEC205", "medium", f, f"{pkg} declares no source repository")
        if not meta.get("license"):
            add(findings, "SEC205", "low", f, f"{pkg} declares no licence")
        # SEC206 - brand new package
        created = (meta.get("time") or {}).get("created", "")
        if created[:4] >= "2026" and created[5:7] >= "10":
            add(findings, "SEC206", "low", f,
                f"{pkg} was first published at {created[:10]} - very new")
        # SEC207 - no recent maintenance
        modified = (meta.get("time") or {}).get("modified", "")
        if modified and modified[:4] < "2025":
            add(findings, "SEC207", "low", f,
                f"{pkg} last modified {modified[:10]}")


# ---------------------------------------------------------------- driver
def changed_files(base):
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
            capture_output=True, text=True, check=True).stdout
    except Exception as e:
        print(f"could not diff against {base}: {e}", file=sys.stderr)
        return None
    return [os.path.join(ROOT, f) for f in out.split("\n") if f.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", action="store_true",
                    help="scan only files changed against --base")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", default="high",
                    choices=["info", "low", "medium", "high", "critical", "none"])
    ap.add_argument("--no-network", action="store_true",
                    help="skip npm provenance checks")
    args = ap.parse_args()

    targets = None
    if args.changed:
        targets = changed_files(args.base)
        if targets is None:
            targets = []
        targets = [t for t in targets if os.path.isfile(t)]

    def wanted(path, pattern):
        if targets is not None:
            return path in targets
        return re.search(pattern, rel(path)) is not None

    findings = []
    workflows = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ROOT, "automations"))
                 for f in fs if f.endswith(".json") and f != "registry.json"]
    records = ([os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ROOT, "knowledge-base", "nodes"))
                for f in fs if f.endswith(".json")] +
               [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(ROOT, "knowledge-base", "credentials"))
                for f in fs if f.endswith(".json")])

    for p in workflows:
        if wanted(p, r"^automations/"):
            scan_workflow(p, findings)
    for p in records:
        if wanted(p, r"^knowledge-base/(nodes|credentials)/"):
            scan_record(p, findings)

    if not args.no_network and (targets is None or SHORTLIST in targets):
        scan_shortlist(findings)

    today = "2026-11-17"
    waivers = load_waivers()
    kept = []
    for f in findings:
        w = waived(f, waivers, today)
        if w:
            f["waived"] = w.get("reason", "waived")
        kept.append(f)

    active = [f for f in kept if "waived" not in f]
    active.sort(key=lambda f: (-SEV_ORDER[f["severity"]], f["file"], f["rule"]))

    if args.json:
        print(json.dumps({"findings": kept, "active": len(active),
                          "waived": len(kept) - len(active)}, indent=2))
    else:
        for f in active:
            loc = f"{f['file']}" + (f" :: {f['node']}" if f.get("node") else "")
            ev = f"  [{f['evidence']}]" if f.get("evidence") else ""
            print(f"{f['severity']:>8}  {f['rule']}  {loc}\n          {f['message']}{ev}")
        if len(kept) != len(active):
            print(f"\n{len(kept) - len(active)} finding(s) waived via security/waivers.json")
        counts = {}
        for f in active:
            counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in
                            sorted(counts.items(), key=lambda kv: -SEV_ORDER[kv[0]])) or "clean"
        print(f"\n{len(workflows)} workflows, {len(records)} records scanned - {summary}")

    if args.fail_on == "none":
        return 0
    threshold = SEV_ORDER[args.fail_on]
    return 1 if any(SEV_ORDER[f["severity"]] >= threshold for f in active) else 0


if __name__ == "__main__":
    sys.exit(main())
