#!/usr/bin/env python3
"""Build a machine-readable knowledge base of n8n built-in nodes from the
n8n-docs repository (docs/integrations/builtin).

Output: /scratch/work/n8n-node-kb/
"""
import os, re, json, shutil, datetime, unicodedata, urllib.parse

SRC = "/scratch/work/n8n-docs/docs/integrations/builtin"
REPO = "/scratch/work/n8n-docs"
OUT = "/scratch/work/n8n-node-kb"
DOCS_BASE = "https://docs.n8n.io"
TODAY = "2026-11-17"

CATS = {
    "app-nodes": ("app-node", "App node - connects to an external service API"),
    "trigger-nodes": ("trigger-node", "Trigger node - starts a workflow when an event happens"),
    "core-nodes": ("core-node", "Core node - built-in logic, data or generic API functionality"),
    "cluster-nodes/root-nodes": ("cluster-root-node", "AI cluster root node (agent, chain, vector store)"),
    "cluster-nodes/sub-nodes": ("cluster-sub-node", "AI cluster sub-node (model, memory, tool, parser)"),
    "credentials": ("credential", "Credential type - authentication definition"),
}

# ---------------------------------------------------------------- reusable blocks
REUSABLE_TEXT = {
    "6vuTxJwns2nA8U7V56ij": "> **AI tool:** This node can be used as an AI tool. Connect it to the Tools input of an AI Agent node so the agent can call it.",
    "7QbEnpnpOks3Rq0SiMFb": "> **Credential-only node:** This node exists only to supply credentials to other nodes.",
    "HoGXnGIfupVt81dGox48": "> **n8n Cloud:** Cloud users can connect with the one-click sign-in button instead of entering keys manually.",
    "UqTgO2VbAzax4T8z4Fyh": "> **Note:** This node requires git to be configured on the n8n instance.",
    "fjWxEWe1g0CDvsx1igf6": "> **Header auth:** Send an `Authorization` header (or a custom header) with the credential value.",
    "vIyn1XsEkjlolZzHTfTG": "> **Basic auth:** Uses username and password.",
    "JeIbggto5Oi1mPf9SOYv": "> **Bearer auth:** Uses a bearer token sent in the `Authorization` header.",
    "tq6Yob45CR8oPKrT6Ggr": "> **Digest auth:** Uses username and password with HTTP digest authentication.",
    "2T2SmMUgiLyck7FDDwRD": "> **Feature availability:** Some features differ between n8n Cloud and self-hosted, or require a minimum n8n version.",
    "YSs9Y6clfLTwlXMx69w6E": "> **Note:** This is a prompt-based node: the behaviour is driven by the prompt text you supply.",
}


def reusable_index():
    """id -> name from REUSABLE_CONTENT_INDEX.md"""
    path = os.path.join(REPO, "REUSABLE_CONTENT_INDEX.md")
    m = {}
    if not os.path.exists(path):
        return m
    for line in open(path, encoding="utf-8"):
        if line.startswith("| `"):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) > 2:
                m[cells[1].strip("`")] = cells[2]
    return m


REUSABLE_NAMES = reusable_index()

# ---------------------------------------------------------------- helpers
ANCHOR_RE = re.compile(r'\s*<a href="#[^"]*" id="[^"]*"></a>')
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')


def strip_anchors(s):
    return ANCHOR_RE.sub("", s)


def clean_inline(s):
    """Remove gitbook noise from a single line, keep markdown."""
    s = strip_anchors(s)
    s = s.replace("{ data-preview }", "").replace("{ .data-preview }", "")
    s = re.sub(r"\{#?[a-z0-9-]+\}\s*$", "", s)  # trailing {#anchor}
    return s.rstrip()


def parse_frontmatter(text):
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = text[3:end].strip("\n")
            body = text[end + 4:]
            key, buf = None, []
            for line in raw.split("\n"):
                if re.match(r"^[A-Za-z_]+:", line):
                    if key:
                        fm[key] = " ".join(buf).strip()
                    key = line.split(":")[0].strip()
                    buf = [line.split(":", 1)[1].strip()]
                elif key:
                    buf.append(line.strip())
            if key:
                fm[key] = " ".join(buf).strip()
            for k, v in list(fm.items()):
                v = re.sub(r"^(>-|>|\||\|-)\s*", "", v)
                fm[k] = v.strip("'\"").strip()
    return fm, body


def doc_url_from_relpath(relpath):
    p = relpath.replace("\\", "/")
    p = re.sub(r"\.md$", "", p)
    p = re.sub(r"/(README|index)$", "", p)
    return f"{DOCS_BASE}/{p}"


def fix_links(text, page_origpath):
    """Resolve relative .md links to absolute docs.n8n.io URLs."""
    base_dir = os.path.dirname(page_origpath or "")

    def repl(m):
        label, target = m.group(1), m.group(2)
        if re.match(r"^[a-z]+://", target) or target.startswith("#") or target.startswith("mailto:"):
            return f"[{label}]({target})"
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if not target:
            return f"[{label}]({doc_url_from_relpath(page_origpath)}{anchor})"
        joined = os.path.normpath(os.path.join(base_dir, target)).replace("\\", "/")
        return f"[{label}]({doc_url_from_relpath(joined)}{anchor})"

    return LINK_RE.sub(repl, text)




DEMO_RE = re.compile(r'\{%\s*@n8n-blocks/n8n-workflow-demo\s+content="([^"]*)"\s+url="([^"]*)"\s*%\}')


def convert_demos(text, examples):
    """{% @n8n-blocks/n8n-workflow-demo content="<url-encoded json>" url="..." %}
    -> readable fenced JSON example, and collect the workflow for the record."""
    def repl(m):
        raw, url = m.group(1), m.group(2)
        try:
            wf = json.loads(urllib.parse.unquote(raw))
        except Exception:
            return f"\n> Example workflow: {url}\n"
        name = wf.get("name") or ""
        if name.strip().lower() in ("", "example workflow", "my workflow"):
            name = os.path.basename(url).replace(".json", "").replace("_", " ").strip().title()
        examples.append({"name": name, "source_url": url,
                         "node_count": len(wf.get("nodes", [])), "workflow": wf})
        body = json.dumps(wf, indent=2, ensure_ascii=False)
        return f"\n### Example workflow: {name}\n\nSource: {url}\n\n```json\n{body}\n```\n"

    return DEMO_RE.sub(repl, text)


def convert_html(text):
    """GitBook sometimes renders hints/components as raw HTML - normalise it."""
    def repl(m):
        style, inner = m.group(1), m.group(2)
        inner = re.sub(r"<[^>]+>", " ", inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        label = {"warning": "Warning", "info": "Note", "danger": "Important"}.get(style, "Note")
        return f"\n> **{label}:** {inner}\n"

    text = re.sub(r'<div data-gb-custom-block[^>]*data-style="([a-z]+)"[^>]*>(.*?)</div>',
                  repl, text, flags=re.S)
    text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.S)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.S)
    text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.S)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?(?:div|p|span|ul|ol|li|table|tr|td|th|thead|tbody|img|a)[^>]*>", "", text)
    return text


def convert_hints(text):
    """{% hint style="x" %} ... {% endhint %} -> blockquote"""
    def repl(m):
        style, inner = m.group(1), m.group(2)
        label = {"info": "Note", "warning": "Warning", "danger": "Important"}.get(style, "Note")
        inner = inner.strip()
        lines = [l for l in inner.split("\n") if l.strip()]
        if not lines:
            return ""
        first = lines[0].strip()
        m = re.match(r"^\*\*(.+?)\*\*:?\s*(.*)$", first)
        if m and not m.group(2):
            head = f"> **{m.group(1).strip()}:**"
        elif m:
            head = f"> **{m.group(1).strip()}:** {m.group(2).strip()}"
        else:
            head = f"> **{label}:** {first}"
        out = [head]
        for l in lines[1:]:
            out.append("> " + l.strip())
        return "\n".join(out)

    return re.sub(r'\{%\s*hint style="([a-z]+)"\s*%\}(.*?)\{%\s*endhint\s*%\}', repl, text, flags=re.S)


def convert_includes(text, blocks):
    """Replace {% include %} with readable text when known; record ids."""
    def repl(m):
        url = m.group(1)
        bid = url.rstrip("/").split("/")[-1]
        blocks.append({"id": bid, "name": REUSABLE_NAMES.get(bid, "unknown")})
        return REUSABLE_TEXT.get(bid, "")

    text = re.sub(r'\{%\s*include\s+"([^"]+)"\s*%\}', repl, text)
    return text


def convert_tabs(text):
    text = re.sub(r'\{%\s*tabs\s*%\}', "", text)
    text = re.sub(r'\{%\s*endtabs\s*%\}', "", text)
    text = re.sub(r'\{%\s*tab title="([^"]+)"\s*%\}', r"\n**\1**\n", text)
    text = re.sub(r"\{%\s*endtab\s*%\}", "", text)
    text = re.sub(r"\{%\s*endcontent-ref\s*%\}", "", text)
    text = re.sub(r'\{%\s*content-ref url="[^"]*"\s*%\}\s*\n?(.*?)\n?\{%\s*endcontent-ref\s*%\}', r"- \1", text, flags=re.S)
    text = re.sub(r'\{%\s*embed url="([^"]+)"[^%]*%\}', r"\n[Embedded content](\1)\n", text)
    text = re.sub(r"\{%\s*(end)?code[^%]*%\}", "", text)
    text = re.sub(r"\{%\s*[^\s%]+[^%]*%\}", "", text)
    return text


def split_sections(body):
    """Return list of (level, heading, text). Preamble = level 0, heading ''."""
    lines = body.split("\n")
    sections, cur = [], {"level": 0, "heading": "", "lines": []}
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            sections.append(cur)
            cur = {"level": len(m.group(1)), "heading": clean_inline(m.group(2)).strip(), "lines": []}
        else:
            cur["lines"].append(line)
    sections.append(cur)
    return [(s["level"], s["heading"], "\n".join(s["lines"]).strip()) for s in sections]


def plain(s):
    """Markdown inline -> plain text."""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("__", "").replace("`", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .*")


def first_para(text):
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if not p or p.startswith(">") or p.startswith("|") or p.startswith("*") or p.startswith("-"):
            continue
        return plain(p)
    return ""


BULLET_RE = re.compile(r"^([ \t]*)[*+-]\s+(.*)$")


def indent_of(ws):
    return len(ws.replace("\t", "    "))


def parse_operations(section_text):
    """Parse the Operations section into [{resource, operation, description, doc}]."""
    ops = []
    # table form
    tbl = [l for l in section_text.split("\n") if l.strip().startswith("|")]
    if tbl and not any(BULLET_RE.match(l) for l in section_text.split("\n")):
        header = None
        for l in tbl:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if header is None:
                header = [plain(c).lower() for c in cells]
                continue
            row = dict(zip(header, cells))
            res = plain(row.get("resource", "") or row.get("service", "") or "")
            op = plain(row.get("operation", "") or row.get("action", "") or "")
            desc = plain(row.get("description", "") or "")
            if op:
                ops.append({"resource": res, "operation": op, "description": desc, "doc": ""})
        return ops

    items = []  # (indent, text)
    for line in section_text.split("\n"):
        m = BULLET_RE.match(line)
        if m:
            items.append((indent_of(m.group(1)), m.group(2).strip()))
    if not items:
        return ops

    def split_name_desc(txt):
        """**Name** rest / [**Name**](url) rest / Name: desc"""
        doc = ""
        m = re.match(r"\[([^\]]*)\]\(([^)]*)\)\s*(.*)$", txt)
        if m:
            return plain(m.group(1)), plain(m.group(3)), m.group(2)
        m = re.match(r"\*\*(.+?)\*\*\s*[:\-\u2013]?\s*(.*)$", txt)
        if m:
            return plain(m.group(1)), plain(m.group(2)), doc
        if ":" in txt:
            a, b = txt.split(":", 1)
            return plain(a), plain(b), doc
        return plain(txt), "", doc

    # build a tree of bullets by indentation
    roots, stack = [], []
    for ind, txt in items:
        node = {"indent": ind, "text": txt, "children": []}
        while stack and stack[-1]["indent"] >= ind:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            roots.append(node)
        stack.append(node)

    def walk(node, path):
        if node["children"]:
            name, desc, doc = split_name_desc(node["text"])
            walk_path = path + [name] if name else path
            for c in node["children"]:
                walk(c, walk_path)
        else:
            name, desc, doc = split_name_desc(node["text"])
            if not name:
                return
            ops.append({
                "resource": " / ".join([p for p in path if p]),
                "operation": name,
                "description": desc.lstrip(":-\u2013\u2014 ").strip(),
                "doc": doc,
            })

    for r in roots:
        walk(r, [])
    return ops



KV_RE = re.compile(r"(?:\[\*\*(.+?)\*\*\]\([^)]*\)|\*\*(.+?)\*\*)\s*[:\uff1a]?\s*(.*)$")
SKIP_HEADS = {"common issues", "related resources", "templates and examples", "overview",
              "related resources and templates"}


def parse_kv_bullets(text):
    out, seen = [], set()
    rows = []
    for line in text.split("\n"):
        m = BULLET_RE.match(line)
        if m:
            rows.append((indent_of(m.group(1)), m.group(2).strip()))
    if not rows:
        return out
    minind = min(r[0] for r in rows)
    for ind, body_txt in rows:
        if ind > minind:
            continue
        mm = KV_RE.match(body_txt)
        if not mm:
            continue
        name = plain(mm.group(1) or mm.group(2))
        desc = plain(mm.group(3))
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        out.append({"name": name, "description": desc[:300]})
    return out


def anchor_slug(h):
    h = plain(h).lower()
    h = re.sub(r"[^a-z0-9\s-]", "", h).strip()
    return re.sub(r"\s+", "-", h)


PARAM_HEADS = {"node parameters", "node options", "parameters", "options", "operations", "node settings"}


def parse_parameters(sections):
    """Extract ### param headings under 'Node parameters' style sections,
    or a plain bullet list of **Param**: description."""
    params, in_params = [], False
    for si, (lvl, head, text) in enumerate(sections):
        h = head.lower()
        if lvl == 2:
            in_params = h in PARAM_HEADS and h not in ("operations",)
            continue
        if not in_params:
            continue
        if lvl == 3 and not text.strip().startswith("#"):
            pass
        if lvl < 3:
            continue
        desc = first_para(text)
        opts = []
        for line in text.split("\n"):
            m = BULLET_RE.match(line)
            if m:
                v = plain(m.group(2))
                if v and len(v) < 80 and not v.endswith("."):
                    opts.append(v)
        tbl_opts = []
        tbl = [l for l in text.split("\n") if l.strip().startswith("|")]
        if len(tbl) > 2:
            for l in tbl[2:]:
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if cells and cells[0] and not set("".join(cells)) <= set("-: "):
                    tbl_opts.append(plain(cells[0]))
        entry = {"name": head}
        if desc:
            entry["description"] = desc[:400]
        if opts:
            entry["options"] = opts[:40]
        elif tbl_opts:
            entry["options"] = tbl_opts[:40]
        params.append(entry)

    # bullet-style parameter sections (common in trigger node docs)
    for si, (lvl, head, text) in enumerate(sections):
        if lvl != 2 or head.lower() not in ("parameters", "node parameters", "node filters",
                                            "node options", "options"):
            continue
        has_subs = any(l2 == 3 for l2, _, _ in sections[si + 1:si + 4])
        if has_subs:
            continue
        for kv in parse_kv_bullets(text):
            if kv["name"].lower() not in {p["name"].lower() for p in params}:
                params.append(kv)
    return params


def extract_credential(text):
    """Find credential reference + auth methods."""
    cred = None
    m = re.search(r"\[([^\]]+?)\s+credentials\]\(([^)]+)\)", text)
    if m:
        cred = {"name": m.group(1).strip(), "doc": m.group(2)}
    if not cred:
        m = re.search(r"\[([^\]]*[Cc]redential[^\]]*)\]\(([^)]+)\)", text)
        if m:
            cred = {"name": plain(m.group(1)), "doc": m.group(2)}
    return cred


def extract_auth_methods(sections):
    methods = []
    for lvl, head, text in sections:
        if "authentication" in head.lower() or "auth method" in head.lower():
            for line in text.split("\n"):
                m = BULLET_RE.match(line)
                if m:
                    v = plain(m.group(2))
                    if v and len(v) < 80:
                        methods.append(v)
    return methods[:10]


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-").lower()
    return s or "node"


STOP = set("""a an and are as at be by for from has have how in into is it its of on or that the
this to use used using with you your node nodes can may will not when what which who documentation
learn follow technical integrate workflows workflow refer more information about other see also
than then there these those per via etc each any all one two documentation includes details
examples example links link configuration configure integrate integration automate wide range
feature features follow technical learn guide guidance information related resources resource
page section refer node's support supports supported built builtin""".split())


def keywords_for(name, slug, category, ops, params, cred, desc):
    kw = set()
    for src in [name, slug.replace("n8n-nodes-base.", "").replace("n8n-nodes-langchain.", ""), category]:
        for w in re.split(r"[^A-Za-z0-9+#.]+", src):
            w = w.lower()
            if len(w) > 1 and w not in STOP:
                kw.add(w)
    for o in ops:
        for w in re.split(r"[^A-Za-z0-9+#]+", (o.get("resource", "") + " " + o.get("operation", ""))):
            w = w.lower()
            if len(w) > 2 and w not in STOP:
                kw.add(w)
    if cred:
        for w in re.split(r"[^A-Za-z0-9+#]+", cred["name"]):
            w = w.lower()
            if len(w) > 2 and w not in STOP:
                kw.add(w)
    for p in params:
        for w in re.split(r"[^A-Za-z0-9+#]+", p["name"]):
            w = w.lower()
            if len(w) > 2 and w not in STOP:
                kw.add(w)
    for w in re.split(r"[^A-Za-z0-9+#]+", desc or ""):
        w = w.lower()
        if len(w) > 3 and w not in STOP:
            kw.add(w)
    return sorted(kw)[:120]


# ---------------------------------------------------------------- discovery
def _dedupe_examples(ex):
    seen, out = set(), []
    for e in ex:
        if e["name"] in seen:
            continue
        seen.add(e["name"])
        out.append(e)
    return out


def discover():
    nodes = []
    for rel, (cat, catdesc) in CATS.items():
        d = os.path.join(SRC, rel)
        if not os.path.isdir(d):
            continue
        for entry in sorted(os.listdir(d)):
            if entry == "README.md" or entry.startswith("."):
                continue
            p = os.path.join(d, entry)
            if os.path.isdir(p):
                pages = [f for f in sorted(os.listdir(p)) if f.endswith(".md")]
                pages.sort(key=lambda f: (f not in ("README.md", "index.md"), f))
                if not pages:
                    continue
                nodes.append({"id": entry, "cat": cat, "catdesc": catdesc,
                              "dir": os.path.join(rel, entry),
                              "pages": [os.path.join(rel, entry, f) for f in pages]})
            elif entry.endswith(".md"):
                nodes.append({"id": entry[:-3], "cat": cat, "catdesc": catdesc,
                              "dir": rel, "pages": [os.path.join(rel, entry)]})
    return nodes


def read(p):
    return open(os.path.join(SRC, p), encoding="utf-8").read()


# ---------------------------------------------------------------- build one node
def build_node(n, CRED_IDS=frozenset()):
    blocks = []
    page_docs = []
    first_page_body = None
    main_fm, main_body = None, None
    md_parts = []
    all_ops, all_params, all_methods = [], [], []
    op_details, events, trigger_methods, examples = [], [], set(), []
    issue_list = []

    for i, relpage in enumerate(n["pages"]):
        raw = read(relpage)
        fm, body = parse_frontmatter(raw)
        origpath = fm.get("originalFilePath") or relpage
        body = convert_demos(body, examples)
        body = convert_html(body)
        body = convert_hints(body)
        body = convert_includes(body, blocks)
        body = convert_tabs(body)
        body = fix_links(body, origpath)
        body = "\n".join(clean_inline(l) if l.strip().startswith("#") else l for l in body.split("\n"))
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        sections = split_sections(body)
        fname = os.path.basename(relpage)

        if i == 0:
            main_fm, main_body = fm, body
        page_docs.append({"page": fname, "title": fm.get("title", ""),
                          "url": fm.get("url", ""), "origpath": origpath})

        for si, (lvl, head, text) in enumerate(sections):
            if lvl == 2 and head.lower() == "operations":
                chunk = text
                for lvl2, head2, text2 in sections[si + 1:]:
                    if lvl2 <= 2:
                        break
                    if lvl2 == 3 and head2:
                        chunk += f"\n\n* **{head2}**\n" + "\n".join(
                            ("    " + l) if BULLET_RE.match(l) else l for l in text2.split("\n"))
                    else:
                        chunk += "\n" + text2
                all_ops.extend(parse_operations(chunk))
        all_params.extend(parse_parameters(sections))
        all_methods.extend(extract_auth_methods(sections))

        for lvl, head, text in sections:
            if lvl == 2 and head.lower() in ("events", "supported events", "trigger events"):
                ev = parse_kv_bullets(text)
                if ev:
                    events.extend(ev)
        low = body.lower()
        if "poll mode" in low or "polling" in low or "poll " in low:
            trigger_methods.add("polling")
        if "webhook" in low:
            trigger_methods.add("webhook")
        if "schedule" in low or "cron" in low:
            trigger_methods.add("schedule")

        if i > 0:
            for si, (lvl, head, text) in enumerate(sections):
                if lvl != 2 or not head or head.lower() in SKIP_HEADS:
                    continue
                sub_params = parse_kv_bullets(text)
                sub_opts = []
                for lvl2, h2, t2 in sections[si + 1:]:
                    if lvl2 <= 2:
                        break
                    if lvl2 == 3:
                        sub_opts.extend(parse_kv_bullets(t2))
                if sub_params or sub_opts:
                    d = {"operation": head, "page": fname,
                         "doc": doc_url_from_relpath(origpath) + "#" + anchor_slug(head)}
                    summ = first_para(text)
                    if summ:
                        d["summary"] = summ[:300]
                    if sub_params:
                        d["parameters"] = sub_params[:40]
                    if sub_opts:
                        d["options"] = sub_opts[:60]
                    op_details.append(d)

        if "common-issues" in fname:
            for lvl, head, text in sections:
                if lvl == 2 and head and head.lower() not in ("common issues", "related resources"):
                    issue_list.append({"title": head, "summary": first_para(text)[:400]})

        if i == 0:
            body = re.sub(r"^#\s+.*?\n", "", body, count=1) if body.startswith("#") else body
            md_parts.append(("", body, fm))
            first_page_body = body
        else:
            page_title = clean_inline(fm.get("title") or fname.replace(".md", "").replace("-", " ").title())
            body = re.sub(r"^(#{1,5})\s", lambda mm: "#" + mm.group(1) + " ", body, flags=re.M)
            md_parts.append((f"---\n\n## {page_title}", body, fm))

    # merge operations (dedupe)
    seen, ops = set(), []
    for o in all_ops:
        key = (o["resource"].lower(), o["operation"].lower())
        if key in seen or not o["operation"]:
            continue
        seen.add(key)
        ops.append(o)

    # attach operation-level details to matching operations
    if op_details:
        def toks(x):
            return {w for w in re.split(r"[^a-z0-9]+", (x or "").lower()) if w}

        for o in ops:
            op_t = toks(o["operation"])
            res_t = toks(o["resource"])
            best, best_score = None, 0
            for d in op_details:
                d_t = toks(d["operation"])
                if not op_t or not op_t <= d_t:
                    continue
                score = len(d_t & (op_t | res_t)) + (2 if res_t and res_t <= d_t else 0)
                if score > best_score:
                    best, best_score = d, score
            if best:
                if best.get("parameters"):
                    o["parameters"] = best["parameters"]
                if best.get("options"):
                    o["options"] = best["options"]
                if not o["doc"]:
                    o["doc"] = best["doc"]

    # dedupe params
    seenp, params = set(), []
    for p in all_params:
        if p["name"].lower() in seenp:
            continue
        seenp.add(p["name"].lower())
        params.append(p)

    full_text = "\n\n".join(p[1] for p in md_parts)
    name = (main_fm.get("nodeTitle") or "").strip()
    h1 = re.search(r"^#\s+(.*)$", main_body or "", re.M)
    if h1:
        cand = clean_inline(h1.group(1)).strip()
        cand = re.sub(r"\s+node documentation$", "", cand, flags=re.I)
        cand = re.sub(r"\s+documentation$", "", cand, flags=re.I)
        cand = re.sub(r"\s+node$", "", cand, flags=re.I)
        display = cand or name
    else:
        display = name
    if not display or display.lower().startswith("n8n-nodes-"):
        display = re.sub(r"^(n8n-nodes-base|n8n-nodes-langchain)\.", "", n["id"]).replace("-", " ").title()

    body_para = first_para(first_page_body if first_page_body is not None else (main_body or ""))
    fm_desc = (main_fm.get("description") or "").strip()
    desc = body_para if len(body_para) >= 60 else (fm_desc or body_para)
    desc = re.sub(r"\s+", " ", desc).strip()
    # keep first sentence-ish, max 400
    if len(desc) > 400:
        desc = desc[:397].rsplit(" ", 1)[0] + "..."

    cred = extract_credential(full_text)
    if cred:
        slug = cred["doc"].rstrip("/").split("/")[-1]
        cred["slug"] = slug
        if slug in CRED_IDS:
            cred["json_file"] = f"credentials/{slug}.json"
            cred["markdown_file"] = f"credentials/{slug}.md"
    is_trigger = n["cat"] == "trigger-node" or n["id"].endswith("trigger") or bool(
        re.search(r"\btrigger\b", (main_fm.get("title") or ""), re.I))
    ai_tool = any(b["id"] == "6vuTxJwns2nA8U7V56ij" for b in blocks)
    credential_only = any(b["id"] == "7QbEnpnpOks3Rq0SiMFb" for b in blocks)

    record = {
        "id": n["id"],
        "name": display,
        "category": n["cat"],
        "category_description": n["catdesc"],
        "node_type": n["id"],
        "is_trigger": is_trigger,
        "is_ai_tool": ai_tool,
        "is_credential_only": credential_only,
        "description": desc,
        "doc_url": (main_fm.get("url") or doc_url_from_relpath(n["pages"][0])),
        "credentials": cred,
        "authentication_methods": sorted(set(all_methods))[:10],
        "operations": ops,
        "operation_count": len(ops),
        "parameters": params,
        "events": events,
        "trigger_methods": sorted(trigger_methods) if is_trigger else [],
        "operation_details": op_details,
        "examples": _dedupe_examples(examples),
        "common_issues": issue_list,
        "keywords": keywords_for(display, n["id"], n["cat"], ops, params, cred, desc),
        "reusable_blocks": blocks,
        "pages": page_docs,
        "files": {
            "json": f"nodes/{n['cat']}/{n['id']}.json",
            "markdown": f"nodes/{n['cat']}/{n['id']}.md",
        },
        "source": {"repo": "n8n-io/n8n-docs", "path": "docs/" + n["pages"][0],
                   "license": "Sustainable Use License (n8n docs)"},
        "generated": TODAY,
    }

    # ---- markdown file
    md = [f"<!-- n8n built-in node reference: {n['id']} | source: {record['doc_url']} -->", ""]
    for header, body, fm in md_parts:
        if header:
            md.append(header)
            md.append("")
        md.append(body)
        md.append("")
    md_md = "\n".join(md)
    md_md = re.sub(r"\n{3,}", "\n\n", md_md).strip() + "\n"
    return record, md_md


# ---------------------------------------------------------------- main
WORKFLOWS_SRC = os.path.join(REPO, "docs", "_workflows")


def copy_workflow_examples():
    """Copy the real workflow JSON files bundled with the docs, plus an index."""
    outdir = os.path.join(OUT, "examples", "workflows")
    if not os.path.isdir(WORKFLOWS_SRC):
        return []
    os.makedirs(outdir, exist_ok=True)
    index = []
    for root, _, files in os.walk(WORKFLOWS_SRC):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            src = os.path.join(root, f)
            rel = os.path.relpath(src, WORKFLOWS_SRC).replace("\\", "/")
            dst = os.path.join(outdir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            try:
                wf = json.load(open(src))
            except Exception:
                continue
            types = sorted({n.get("type", "") for n in wf.get("nodes", []) if n.get("type")})
            index.append({
                "file": f"examples/workflows/{rel}",
                "name": wf.get("name") or os.path.basename(rel),
                "node_count": len(wf.get("nodes", [])),
                "node_types": types,
                "description": (wf.get("meta") or {}).get("description") or "",
            })
    json.dump({"generated": TODAY,
               "note": "Real n8n workflows shipped with the docs. Use them as structural templates.",
               "count": len(index), "workflows": index},
              open(os.path.join(OUT, "examples", "index.json"), "w"), indent=2, ensure_ascii=False)
    return index


def main():
    # remove only generated parts - hand-written docs (README, AGENT-GUIDE, schema) survive
    for sub in ["nodes", "credentials", "indexes", "examples"]:
        d = os.path.join(OUT, sub)
        if os.path.isdir(d):
            shutil.rmtree(d)
    for f in ["catalog.json", "manifest.json"]:
        fp = os.path.join(OUT, f)
        if os.path.exists(fp):
            os.remove(fp)
    for sub in ["nodes/app-node", "nodes/trigger-node", "nodes/core-node",
                "nodes/cluster-root-node", "nodes/cluster-sub-node",
                "credentials", "indexes", "tools"]:
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    nodes = discover()
    CRED_IDS = frozenset(x["id"] for x in nodes if x["cat"] == "credential")
    records, cred_records = [], []
    stats = {}

    for n in nodes:
        rec, md = build_node(n, CRED_IDS)
        if n["cat"] == "credential":
            cred_records.append((rec, md))
            json.dump(rec, open(os.path.join(OUT, "credentials", n["id"] + ".json"), "w"), indent=2, ensure_ascii=False)
            open(os.path.join(OUT, "credentials", n["id"] + ".md"), "w").write(md)
        else:
            records.append(rec)
            json.dump(rec, open(os.path.join(OUT, rec["files"]["json"]), "w"), indent=2, ensure_ascii=False)
            open(os.path.join(OUT, rec["files"]["markdown"]), "w").write(md)
        stats[n["cat"]] = stats.get(n["cat"], 0) + 1

    # ---------------- catalog
    catalog = {
        "name": "n8n built-in node knowledge base",
        "version": "1.0.0",
        "generated": TODAY,
        "source": "https://docs.n8n.io/integrations/builtin/ (repo: n8n-io/n8n-docs)",
        "counts": stats,
        "node_count": len(records),
        "credential_count": len(cred_records),
        "nodes": [{
            "id": r["id"], "name": r["name"], "category": r["category"],
            "trigger": r["is_trigger"], "ai_tool": r["is_ai_tool"],
            "description": r["description"],
            "operation_count": r["operation_count"],
            "credential": (r["credentials"] or {}).get("name"),
            "doc_url": r["doc_url"],
            "json": r["files"]["json"], "md": r["files"]["markdown"],
        } for r in sorted(records, key=lambda x: (x["category"], x["name"].lower()))],
    }
    json.dump(catalog, open(os.path.join(OUT, "catalog.json"), "w"), indent=2, ensure_ascii=False)

    # ---------------- jsonl indexes
    with open(os.path.join(OUT, "indexes", "nodes.jsonl"), "w") as f:
        for r in sorted(records, key=lambda x: x["id"]):
            f.write(json.dumps({
                "id": r["id"], "name": r["name"], "category": r["category"],
                "trigger": r["is_trigger"], "ai_tool": r["is_ai_tool"],
                "cred": (r["credentials"] or {}).get("name"),
                "ops": [f"{o['resource']}/{o['operation']}" if o["resource"] else o["operation"] for o in r["operations"]][:60],
                "desc": r["description"], "doc": r["doc_url"],
            }, ensure_ascii=False) + "\n")

    with open(os.path.join(OUT, "indexes", "operations.jsonl"), "w") as f:
        for r in sorted(records, key=lambda x: x["id"]):
            for o in r["operations"]:
                f.write(json.dumps({
                    "node": r["id"], "name": r["name"], "category": r["category"],
                    "resource": o["resource"], "operation": o["operation"],
                    "description": o["description"], "doc": r["doc_url"],
                }, ensure_ascii=False) + "\n")

    # keyword index
    kw = {}
    for r in records:
        for k in r["keywords"]:
            kw.setdefault(k, []).append(r["id"])
    kw = {k: sorted(set(v)) for k, v in sorted(kw.items()) if len(v) <= 400}
    json.dump({"generated": TODAY, "keyword_count": len(kw), "keywords": kw},
              open(os.path.join(OUT, "indexes", "keywords.json"), "w"), ensure_ascii=False)

    # by category / triggers / ai tools
    bycat = {}
    for r in records:
        bycat.setdefault(r["category"], []).append(r["id"])
    json.dump(bycat, open(os.path.join(OUT, "indexes", "by-category.json"), "w"), indent=2)
    json.dump({"triggers": [{"id": r["id"], "name": r["name"], "category": r["category"],
                             "description": r["description"]} for r in records if r["is_trigger"]]},
              open(os.path.join(OUT, "indexes", "triggers.json"), "w"), indent=2, ensure_ascii=False)
    json.dump({"ai_tools": [{"id": r["id"], "name": r["name"], "category": r["category"],
                             "description": r["description"]} for r in records if r["is_ai_tool"]]},
              open(os.path.join(OUT, "indexes", "ai-tools.json"), "w"), indent=2, ensure_ascii=False)
    json.dump([{"id": r["id"], "name": r["name"], "auth": r["authentication_methods"],
                "doc": r["doc_url"]} for r, _ in cred_records],
              open(os.path.join(OUT, "indexes", "credentials.json"), "w"), indent=2, ensure_ascii=False)

    # manifest
    total_ops = sum(r["operation_count"] for r in records)
    manifest = {
        "name": "n8n-node-kb", "version": "1.0.0", "generated": TODAY,
        "source": {"docs": "https://docs.n8n.io/integrations/builtin/",
                   "repo": "https://github.com/n8n-io/n8n-docs",
                   "snapshot": "git clone --depth 1, 2026-11-17"},
        "counts": {**stats, "nodes_total": len(records), "credentials_total": len(cred_records),
                   "operations_total": total_ops, "keywords_total": len(kw)},
        "layout": {
            "catalog.json": "every node, one compact entry each - start here",
            "indexes/nodes.jsonl": "one line per node (id, name, ops, desc) - grep friendly",
            "indexes/operations.jsonl": "one line per operation - best file for 'which node does X'",
            "indexes/keywords.json": "keyword -> node ids",
            "indexes/by-category.json": "category -> node ids",
            "indexes/triggers.json": "all trigger nodes",
            "indexes/ai-tools.json": "all nodes usable as AI tools",
            "indexes/credentials.json": "credential types + auth methods",
            "nodes/<category>/<id>.json": "full structured record per node",
            "nodes/<category>/<id>.md": "clean readable reference per node",
            "credentials/<id>.json|.md": "credential type records",
            "tools/search.py": "BM25 search CLI over the KB",
            "schema.json": "JSON Schema for a node record",
        },
    }
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2, ensure_ascii=False)

    wfex = copy_workflow_examples()
    if wfex:
        manifest["counts"]["example_workflows"] = len(wfex)
        manifest["layout"]["examples/index.json"] = "real n8n workflows bundled with the docs, as templates"
        json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=2, ensure_ascii=False)
    print(json.dumps(manifest["counts"], indent=2))
    return records, cred_records, catalog


if __name__ == "__main__":
    main()
