#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref2hugo.py -- postgresqlref の独自フォーマット (text/*/*.txt) を Hugo 用 Markdown に変換する

使い方 (リポジトリのルートで):
    python3 ref2hugo.py . -o content --static-dir static

    # サブパスで公開する場合 (https://example.com/postgresqlref/ など)
    python3 ref2hugo.py . -o content --static-dir static --url-prefix /postgresqlref

入力 (ref.pl が解釈するものと同じ):
    %TITLE / %FILE / %KEY / %LASTMOD / %COMMENT   メタ情報 (front matter へ)
    %CHAPTER[(id)] / %SECTION[(id)] / %SUBSECTION[(id)] / %COLUMN[(id)]   見出し
    %INCLUDE file                                 ファイルの取り込み
    それ以外                                      HTML (Markdown へ変換)

章構成は template/Header の目次 (<h5> / <a href="./xxx.html">) から読み取り、
  content/_index.md             トップページ (目次と同じ構成の一覧)
  content/<section>/_index.md   セクションのとびら (サイドバー名は目次の <h5> の見出し)
  content/<section>/<slug>.md   各ページ
を作り、weight で目次順を再現します。
 - セクション同士の weight は 10, 20, 30...、セクション内のページは 1, 2, 3...
 - 目次 (Header) に載っていないページ (例: type-12) は、元のサイトでもメニューから辿れない
   ページなので既定では変換しません (警告が出ます)。--include-unlisted を付けると、同じ接頭辞の
   ページと同じセクションに、メニュー非表示 (hidden: true) で変換します。
 - %TITLE の <a href="https://www.postgresql.org/docs/..."> は本文の先頭に「公式ドキュメント: …」
   として残します。

見出しレベル:  %CHAPTER -> ##,  %SECTION -> ###,  %SUBSECTION -> ####,  %COLUMN -> #####
(# はページタイトルとして Hugo のテーマが出力する前提)

変換しきれない HTML (colspan のある表、<pre> 内の装飾、class 付き div など) は
そのまま HTML で残します。Hugo の設定で
    [markup.goldmark.renderer]
      unsafe = true
を有効にしてください。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

VOID = {"br", "hr", "img", "input", "meta", "link", "col", "wbr", "area", "base",
        "embed", "param", "source", "track"}

INLINE_TAGS = {"a", "b", "strong", "i", "em", "u", "s", "del", "strike", "code", "tt",
               "kbd", "samp", "var", "span", "font", "small", "big", "sub", "sup",
               "mark", "img", "br", "abbr", "acronym", "cite", "dfn", "q", "label",
               "nobr", "ins", "wbr"}

RAW_BLOCK_TAGS = {"script", "style", "form", "iframe", "object", "embed", "input",
                  "select", "textarea", "button", "noscript"}

UNWRAP_BLOCK_TAGS = {"center", "section", "article", "main", "header", "footer", "nav",
                     "aside", "tbody", "thead", "tfoot", "tr", "td", "th", "caption",
                     "colgroup", "col", "fieldset", "address", "body", "html", "head"}

CLOSES_P = {"p", "div", "pre", "ul", "ol", "table", "h1", "h2", "h3", "h4", "h5", "h6",
            "blockquote", "dl", "hr", "li", "dt", "dd", "center", "form"}
P_STOP = {"td", "th", "li", "div", "blockquote", "dd", "body", "table", "ul", "ol",
          "pre", "center"}

KNOWN_LANGS = {"sql", "bash", "sh", "shell", "c", "cpp", "python", "perl", "json", "yaml",
               "xml", "html", "text", "plaintext", "diff", "conf", "ini", "console", "plpgsql"}

HEAD_LEVEL = {"CHAPTER": 2, "SECTION": 3, "SUBSECTION": 4, "COLUMN": 5}

DIRECTIVE_RE = re.compile(r"^%(CHAPTER|SECTION|SUBSECTION|COLUMN)(?:\(([^)]*)\))?[ \t]*(.*)$")
META_RE = re.compile(r"^%(TITLE|FILE|KEY|LASTMOD|COMMENT)\b[ \t]*(.*)$")
INCLUDE_RE = re.compile(r"^%INCLUDE\s+(\S+)")

ENTITY_RE = re.compile(r"&(?:#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
ENTITY_SPLIT = re.compile(r"(&(?:#\d+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);)")

CJK = "\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef"
CJK_NEWLINE_RE = re.compile(rf"(?<=[{CJK}])[ \t]*\r?\n[ \t]*(?=[{CJK}])")

BR = "\x00BR\x00"
BRX = re.escape(BR)


# ---------------------------------------------------------------------------
# 簡易 DOM (寛容な HTML パーサ)
# ---------------------------------------------------------------------------

class Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []


class TreeBuilder(HTMLParser):
    """古い HTML (閉じタグ省略、<ul> 無しの <li> など) もそれなりに許容して木にする。"""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("#root")
        self.stack = [self.root]

    # -- テキスト類 --------------------------------------------------------
    def _add_text(self, s):
        top = self.stack[-1]
        if top.children and isinstance(top.children[-1], str):
            top.children[-1] += s
        else:
            top.children.append(s)

    def handle_data(self, data):
        self._add_text(data)

    def handle_entityref(self, name):
        self._add_text(f"&{name};")

    def handle_charref(self, name):
        self._add_text(f"&#{name};")

    def handle_comment(self, data):
        n = Node("#comment")
        n.children = [data]
        self.stack[-1].children.append(n)

    # -- タグ -------------------------------------------------------------
    def _close_until(self, names, stop=()):
        for i in range(len(self.stack) - 1, 0, -1):
            t = self.stack[i].tag
            if t in names:
                del self.stack[i:]
                return True
            if t in stop:
                return False
        return False

    def _start(self, tag, attrs, selfclose):
        tag = tag.lower()
        if tag == "li":
            self._close_until({"li"}, stop={"ul", "ol", "table", "pre"})
        elif tag in ("dt", "dd"):
            self._close_until({"dt", "dd"}, stop={"dl"})
        elif tag in ("td", "th"):
            self._close_until({"td", "th"}, stop={"tr", "table"})
        elif tag == "tr":
            self._close_until({"tr"}, stop={"table", "thead", "tbody", "tfoot"})
        elif tag in ("thead", "tbody", "tfoot"):
            self._close_until({"thead", "tbody", "tfoot"}, stop={"table"})
        if tag in CLOSES_P:
            self._close_until({"p"}, stop=P_STOP)

        node = Node(tag, {k.lower(): (v if v is not None else "") for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID and not selfclose:
            self.stack.append(node)

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, True)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return


def parse_fragment(text: str) -> Node:
    b = TreeBuilder()
    b.feed(text)
    b.close()
    return b.root


# ---------------------------------------------------------------------------
# 目次 (template/Header) の解析
# ---------------------------------------------------------------------------

class TocEntry:
    def __init__(self, slug, title, section, group, subgroup, weight):
        self.slug = slug
        self.title = title
        self.section = section
        self.group = group
        self.subgroup = subgroup
        self.weight = weight
        self.hidden = False     # 目次に無いページ (--include-unlisted 時): メニューには出さない

    @property
    def is_index(self):
        return self.slug == self.section


def _prefix(slug: str) -> str:
    return re.sub(r"-\d+$", "", slug)


class Toc:
    def __init__(self):
        self.pages: dict[str, TocEntry] = {}
        # {name, title, weight, entries: [TocEntry]}  (entries は目次の並び順)
        self.sections: list[dict] = []
        self.site_title = ""

    def section_of(self, name: str):
        for sec in self.sections:
            if sec["name"] == name:
                return sec
        return None

    def adopt(self, slug: str, title: str) -> TocEntry:
        """目次 (Header) に載っていないページを、接頭辞が同じページのいるセクションに収容する。
        例: type-12 は type-01..11 と同じ「関数」セクションの type-11 の直後に入る。"""
        pre = _prefix(slug)
        sibs = [e for e in self.pages.values() if _prefix(e.slug) == pre and not e.is_index]
        if sibs:
            last = sibs[-1]
            sec = self.section_of(last.section)
            entry = TocEntry(slug, title, last.section, last.group, last.subgroup, 0)
            sec["entries"].insert(sec["entries"].index(last) + 1, entry)
        else:
            sec = self.section_of(pre)
            if sec is None:
                sec = {"name": pre, "title": title if slug == pre else pre,
                       "weight": 900 + len(self.sections), "entries": []}
                self.sections.append(sec)
            entry = TocEntry(slug, title, sec["name"], sec["title"], "", 0)
            sec["entries"].append(entry)
        self.pages[slug] = entry
        self.renumber()
        return entry

    def renumber(self):
        """weight を振り直す: セクションのとびらはセクションの weight、
        それ以外のページはセクション内の通し番号 (Relearn は兄弟間の weight で並べる)。"""
        for sec in self.sections:
            n = 0
            for e in sec["entries"]:
                if e.is_index:
                    e.weight = sec["weight"]
                else:
                    n += 1
                    e.weight = n


TOKEN_RE = re.compile(
    r"<h5>(?P<h5>.*?)</h5>"
    r"|<a\s+[^>]*?href=\"(?:\./)?(?P<slug>[^\"#/]+)\.html\"[^>]*>(?P<atitle>.*?)</a>"
    r"|(?:^|\n|<hr>)[ \t]*\[(?P<label>[^\]\n]+)\]",
    re.S | re.I,
)


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\u200b", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s.lstrip("・").strip()


def parse_toc(header_text: str) -> Toc:
    groups = []
    cur = None
    sub = ""
    for m in TOKEN_RE.finditer(header_text):
        if m.group("h5") is not None:
            cur = {"title": _clean(m.group("h5")), "entries": []}
            groups.append(cur)
            sub = ""
        elif m.group("slug") is not None:
            if cur is None:
                continue
            cur["entries"].append((m.group("slug"), _clean(m.group("atitle")), sub))
        elif m.group("label") is not None:
            sub = _clean(m.group("label"))

    toc = Toc()
    m = re.search(r"<h1[^>]*class=\"title\"[^>]*>(.*?)</h1>", header_text, re.S | re.I) \
        or re.search(r"<title>(.*?)</title>", header_text, re.S | re.I)
    toc.site_title = _clean(m.group(1)) if m else ""
    for gi, g in enumerate(groups, 1):
        if not g["entries"]:
            continue
        # セクション名: 連番の付かない slug (とびら) があればそれ、無ければ先頭 slug の接頭辞
        section = None
        for slug, _, _ in g["entries"]:
            if not re.search(r"-\d+$", slug):
                section = slug
                break
        if section is None:
            section = re.sub(r"-\d+$", "", g["entries"][0][0])
        sec = {"name": section, "title": g["title"], "weight": gi * 10, "entries": []}
        toc.sections.append(sec)
        for slug, title, subgroup in g["entries"]:
            e = TocEntry(slug, title, section, g["title"], "" if slug == section else subgroup, 0)
            sec["entries"].append(e)
            toc.pages[slug] = e
    toc.renumber()
    return toc


# ---------------------------------------------------------------------------
# Markdown 生成
# ---------------------------------------------------------------------------

class Block:
    __slots__ = ("kind", "text")

    def __init__(self, kind, text):
        self.kind = kind
        self.text = text


def md_escape(s: str) -> str:
    out = []
    for part in ENTITY_SPLIT.split(s):
        if not part:
            continue
        if ENTITY_RE.fullmatch(part):
            out.append(part)
            continue
        p = part.replace("\\", "\\\\")
        p = re.sub(r"([`*\[\]~])", r"\\\1", p)
        p = p.replace("<", "&lt;")
        p = re.sub(r"(?<![A-Za-z0-9])_|_(?![A-Za-z0-9])", r"\\_", p)
        out.append(p)
    return "".join(out)


def escape_line_start(line: str) -> str:
    line = re.sub(r"^(\s*)(#+)(?=\s|$)", lambda m: m.group(1) + "\\" + m.group(2), line)
    line = re.sub(r"^(\s*)([-+])(?=\s|$)", lambda m: m.group(1) + "\\" + m.group(2), line)
    line = re.sub(r"^(\s*)(\d+)([.)])(?=\s|$)",
                  lambda m: m.group(1) + m.group(2) + "\\" + m.group(3), line)
    line = re.sub(r"^(\s*)>", lambda m: m.group(1) + "\\>", line)
    line = re.sub(r"^(\s*)(=+)\s*$", lambda m: m.group(1) + "\\" + m.group(2), line)
    return line


def is_punct(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "PS"


def split_ws(s: str):
    m = re.match(rf"^((?:\s|{BRX})*)(.*?)((?:\s|{BRX})*)$", s, re.S)
    return m.group(1), m.group(2), m.group(3)


class Converter:
    def __init__(self, toc: Toc, repo: Path, url_prefix="", code_lang="", cjk_join=True,
                 encoding="utf-8"):
        self.toc = toc
        self.repo = repo
        self.url_prefix = url_prefix.rstrip("/")
        self.code_lang = code_lang
        self.cjk_join = cjk_join
        self.encoding = encoding
        self.images: set[str] = set()
        self.warnings: list[str] = []

    # -- URL ------------------------------------------------------------------
    def page_url(self, slug: str) -> str:
        e = self.toc.pages[slug]
        if e.is_index:
            return f"{self.url_prefix}/{e.section}/"
        return f"{self.url_prefix}/{e.section}/{slug}/"

    def fix_href(self, href: str) -> str:
        href = href.strip()
        m = re.match(r"^(?:\./|\.\./html/|html/)?([A-Za-z0-9_\-]+)\.html(#.*)?$", href)
        if m and m.group(1) in self.toc.pages:
            return self.page_url(m.group(1)) + (m.group(2) or "")
        return href

    def fix_src(self, src: str) -> str:
        src = src.strip()
        if re.match(r"^(?:[a-z][a-z0-9+.-]*:|/)", src, re.I):
            return src
        name = src.replace("\\", "/").split("/")[-1]
        self.images.add(src)
        return f"{self.url_prefix}/images/{name}"

    @staticmethod
    def _dest(url: str) -> str:
        return url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")

    # -- インライン -------------------------------------------------------------
    def _text(self, s: str) -> str:
        if self.cjk_join:
            s = CJK_NEWLINE_RE.sub("", s)
        s = re.sub(r"[ \t\r\n\f]+", " ", s)
        return md_escape(s)

    def plain_text(self, node) -> str:
        if isinstance(node, str):
            return html.unescape(node)
        if node.tag == "br":
            return "\n"
        if node.tag == "#comment":
            return ""
        return "".join(self.plain_text(c) for c in node.children)

    @staticmethod
    def code_span(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        if not text.strip():
            return ""
        runs = re.findall(r"`+", text)
        fence = "`" * (max(len(r) for r in runs) + 1) if runs else "`"
        pad = " " if (text.startswith("`") or text.endswith("`")) else ""
        return f"{fence}{pad}{text}{pad}{fence}"

    @staticmethod
    def wrap(inner: str, marker: str, tag: str) -> str:
        lead, core, trail = split_ws(inner)
        if not core:
            return inner
        if is_punct(core[0]) or is_punct(core[-1]):
            # 日本語では ** の直前直後が記号だと強調が効かないので HTML タグにする
            return f"{lead}<{tag}>{core}</{tag}>{trail}"
        return f"{lead}{marker}{core}{marker}{trail}"

    def open_tag(self, n: Node) -> str:
        attrs = "".join(f' {k}="{html.escape(v, quote=True)}"' if v != "" else f" {k}"
                        for k, v in n.attrs.items())
        return f"<{n.tag}{attrs}>"

    def inline(self, nodes) -> str:
        return "".join(self._inline_one(n) for n in nodes)

    def _inline_one(self, n) -> str:
        if isinstance(n, str):
            return self._text(n)
        t = n.tag
        if t == "#comment":
            return f"<!--{n.children[0]}-->"
        if t == "br":
            return BR
        if t == "wbr":
            return ""
        if t in ("code", "tt", "kbd", "samp", "var"):
            return self.code_span(self.plain_text(n))
        if t in ("b", "strong"):
            return self.wrap(self.inline(n.children), "**", "strong")
        if t in ("i", "em", "cite", "dfn"):
            return self.wrap(self.inline(n.children), "*", "em")
        if t in ("del", "s", "strike"):
            lead, core, trail = split_ws(self.inline(n.children))
            return f"{lead}~~{core}~~{trail}" if core else lead + trail
        if t in ("u", "sub", "sup", "mark", "ins"):
            return f"<{t}>{self.inline(n.children)}</{t}>"
        if t == "span" and n.attrs:
            return f"{self.open_tag(n)}{self.inline(n.children)}</span>"
        if t == "a":
            return self._inline_link(n)
        if t == "img":
            return self._inline_img(n)
        # font, small, big, span(属性なし), その他: 中身だけ残す
        return self.inline(n.children)

    def _inline_link(self, n: Node) -> str:
        inner = self.inline(n.children).replace(BR, " ")
        href = n.attrs.get("href")
        anchor = n.attrs.get("id") or n.attrs.get("name")
        pre = f'<a id="{html.escape(anchor, quote=True)}"></a>' if anchor else ""
        if href is None:
            return pre + inner
        lead, core, trail = split_ws(inner)
        if not core:
            core = md_escape(href)
        url = self._dest(self.fix_href(href))
        title = n.attrs.get("title")
        tt = f' "{title.replace(chr(34), "&quot;")}"' if title else ""
        return f"{pre}{lead}[{core}]({url}{tt}){trail}"

    def _inline_img(self, n: Node) -> str:
        src = n.attrs.get("src", "")
        new_src = self.fix_src(src)
        extra = [k for k in n.attrs if k not in ("src", "alt", "title")]
        if extra:
            n2 = Node("img", dict(n.attrs))
            n2.attrs["src"] = new_src
            return self.open_tag(n2)
        alt = n.attrs.get("alt", "").replace("[", "(").replace("]", ")")
        title = n.attrs.get("title")
        tt = f' "{title.replace(chr(34), "&quot;")}"' if title else ""
        return f"![{alt}]({self._dest(new_src)}{tt})"

    # -- ブロック ---------------------------------------------------------------
    def paragraphs(self, run) -> list[str]:
        s = self.inline(run)
        res = []
        for part in re.split(rf"(?:\s*{BRX}\s*){{2,}}", s):
            part = part.strip()
            part = re.sub(rf"^(?:{BRX}\s*)+", "", part)
            part = re.sub(rf"(?:\s*{BRX})+$", "", part).strip()
            if not part:
                continue
            part = re.sub(rf"[ \t]*{BRX}[ \t]*", lambda m: "\\\n", part)
            part = "\n".join(escape_line_start(l) for l in part.split("\n"))
            res.append(part)
        return res

    def blocks(self, nodes) -> list[Block]:
        out: list[Block] = []
        run: list = []

        def flush():
            if run:
                for p in self.paragraphs(run):
                    out.append(Block("p", p))
                run.clear()

        i, total = 0, len(nodes)
        while i < total:
            n = nodes[i]
            if isinstance(n, str) or n.tag in INLINE_TAGS or n.tag == "#comment":
                run.append(n)
                i += 1
                continue
            flush()
            t = n.tag
            if t == "li":      # <ul> 無しの <li>
                items = []
                j = i
                while j < total and ((isinstance(nodes[j], str) and not nodes[j].strip())
                                     or (isinstance(nodes[j], Node) and nodes[j].tag == "li")):
                    if isinstance(nodes[j], Node):
                        items.append(list(nodes[j].children))
                    j += 1
                out.append(self.list_block(items, False, 1, self._alt(out, "ul")))
                i = j
                continue
            if t in ("ul", "ol"):
                groups = self._list_groups(n)
                try:
                    start = int(n.attrs.get("start", "1"))
                except ValueError:
                    start = 1
                kind = "ol" if t == "ol" else "ul"
                out.append(self.list_block(groups, t == "ol", start, self._alt(out, kind)))
            elif t == "pre":
                out.append(self.pre_block(n))
            elif t == "table":
                out.extend(self.table_block(n))
            elif t == "p":
                out.extend(self.blocks(n.children))
            elif re.fullmatch(r"h[1-6]", t):
                level = min(max(int(t[1]) - 1, 2), 6)
                text = self.inline(n.children).replace(BR, " ")
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    out.append(Block("h", "#" * level + " " + text))
            elif t == "hr":
                out.append(Block("hr", "---"))
            elif t == "blockquote":
                inner = "\n\n".join(b.text for b in self.blocks(n.children))
                out.append(Block("quote", "\n".join(("> " + l) if l else ">" for l in inner.split("\n"))))
            elif t == "dl":
                out.append(self.dl_block(n))
            elif t == "div" and n.attrs:
                out.append(Block("html", self.open_tag(n)))
                out.extend(self.blocks(n.children))
                out.append(Block("html", "</div>"))
            elif t in RAW_BLOCK_TAGS:
                out.append(Block("html", self.serialize(n)))
            elif t in ("dt", "dd") or t == "div" or t in UNWRAP_BLOCK_TAGS:
                out.extend(self.blocks(n.children))
            else:
                # 未知のタグ: 中身だけ残す
                out.extend(self.blocks(n.children))
            i += 1
        flush()
        return out

    @staticmethod
    def _alt(out, kind) -> bool:
        return bool(out) and out[-1].kind == kind

    @staticmethod
    def _list_groups(n: Node):
        groups = []
        for c in n.children:
            if isinstance(c, Node) and c.tag == "li":
                groups.append(list(c.children))
            elif isinstance(c, str) and not c.strip():
                continue
            else:
                if groups:
                    groups[-1].append(c)
                else:
                    groups.append([c])
        return groups

    def list_block(self, groups, ordered: bool, start: int, alt: bool) -> Block:
        rendered = [self.blocks(g) for g in groups]
        tight = all(all(b.kind in ("ul", "ol") for b in bl[1:]) and (not bl or bl[0].kind == "p")
                    for bl in rendered)
        sep = "\n" if tight else "\n\n"
        bullet = "*" if alt else "-"
        delim = ")" if alt else "."
        items = []
        num = start
        for bl in rendered:
            marker = f"{num}{delim} " if ordered else f"{bullet} "
            num += 1
            body = sep.join(b.text for b in bl)
            lines = body.split("\n") if body else [""]
            indent = " " * len(marker)
            first = (marker + lines[0]).rstrip()
            rest = [(indent + l) if l.strip() else "" for l in lines[1:]]
            items.append("\n".join([first] + rest))
        return Block("ol" if ordered else "ul", sep.join(items))

    def pre_block(self, n: Node) -> Block:
        if self._has_markup(n):
            return Block("html", self.serialize(n))
        text = self.plain_text(n)
        if text.startswith("\r\n"):
            text = text[2:]
        elif text.startswith("\n"):
            text = text[1:]
        text = text.rstrip("\n").rstrip()
        text = "\n".join(l.rstrip() for l in text.split("\n"))
        lang = self.code_lang
        for c in n.attrs.get("class", "").split():
            if c.lower() in KNOWN_LANGS:
                lang = c.lower()
                break
        for ch in n.children:
            if isinstance(ch, Node) and ch.tag == "code":
                for c in ch.attrs.get("class", "").replace("language-", "").split():
                    if c.lower() in KNOWN_LANGS:
                        lang = c.lower()
        runs = re.findall(r"`{3,}", text)
        fence = "`" * max(3, (max(len(r) for r in runs) + 1) if runs else 3)
        return Block("code", f"{fence}{lang}\n{text}\n{fence}")

    def _has_markup(self, n) -> bool:
        for c in n.children:
            if isinstance(c, Node):
                if c.tag not in ("code", "br", "#comment"):
                    return True
                if self._has_markup(c):
                    return True
        return False

    def dl_block(self, n: Node) -> Block:
        parts = []
        for c in n.children:
            if not isinstance(c, Node):
                continue
            if c.tag == "dt":
                parts.append(self.inline(c.children).replace(BR, " ").strip())
            elif c.tag == "dd":
                body = "\n\n".join(b.text for b in self.blocks(c.children))
                lines = body.split("\n")
                txt = ": " + lines[0] + "".join("\n" + ("    " + l if l.strip() else "") for l in lines[1:])
                parts.append(txt)
        # dt と dd は連続させ、組と組の間に空行
        out, buf = [], []
        for p in parts:
            buf.append(p)
            if p.startswith(": "):
                out.append("\n".join(buf))
                buf = []
        if buf:
            out.append("\n".join(buf))
        return Block("dl", "\n\n".join(out))

    # -- テーブル -------------------------------------------------------------
    def _collect_rows(self, node, rows, caption):
        for c in node.children:
            if isinstance(c, Node):
                if c.tag == "tr":
                    rows.append(c)
                elif c.tag in ("thead", "tbody", "tfoot"):
                    self._collect_rows(c, rows, caption)
                elif c.tag == "caption":
                    caption.append(c)

    def _inline_only(self, nodes) -> bool:
        for ch in nodes:
            if isinstance(ch, str):
                continue
            if ch.tag in INLINE_TAGS or ch.tag == "#comment":
                if not self._inline_only(ch.children):
                    return False
            elif ch.tag == "p" and self._inline_only(ch.children):
                continue
            else:
                return False
        return True

    def table_block(self, t: Node) -> list[Block]:
        rows, caption = [], []
        self._collect_rows(t, rows, caption)
        grid = []
        ok = bool(rows)
        for r in rows:
            cells = [c for c in r.children if isinstance(c, Node) and c.tag in ("td", "th")]
            for c in cells:
                if c.attrs.get("colspan", "1").strip() not in ("1", "") \
                        or c.attrs.get("rowspan", "1").strip() not in ("1", ""):
                    ok = False
                if not self._inline_only(c.children):
                    ok = False
            grid.append(cells)
        ncols = max((len(r) for r in grid), default=0)
        if ncols == 0:
            ok = False
        if not ok:
            return [Block("html", self.serialize(t))]

        out = []
        if caption:
            cap = self.inline(caption[0].children).replace(BR, " ").strip()
            if cap:
                out.append(Block("p", f"**{cap}**" if not (is_punct(cap[0]) or is_punct(cap[-1])) else cap))

        def cell_text(c: Node) -> str:
            nodes = []
            for ch in c.children:
                if isinstance(ch, Node) and ch.tag == "p":
                    if nodes:
                        nodes.append(Node("br"))
                    nodes.extend(ch.children)
                else:
                    nodes.append(ch)
            s = self.inline(nodes).strip()
            s = re.sub(rf"^(?:{BRX}\s*)+", "", s)
            s = re.sub(rf"(?:\s*{BRX})+$", "", s)
            s = re.sub(rf"\s*{BRX}\s*", "<br>", s)
            s = s.replace("\n", " ").replace("|", "\\|")
            return s.strip()

        texts = [[cell_text(c) for c in row] + [""] * (ncols - len(row)) for row in grid]
        aligns = []
        for k in range(ncols):
            a = ""
            if k < len(grid[0]):
                a = grid[0][k].attrs.get("align", "").lower()
            aligns.append({"left": ":---", "right": "---:", "center": ":---:"}.get(a, "---"))
        lines = ["| " + " | ".join(texts[0]) + " |",
                 "| " + " | ".join(aligns) + " |"]
        for row in texts[1:]:
            lines.append("| " + " | ".join(row) + " |")
        out.append(Block("table", "\n".join(lines)))
        return out

    # -- 生 HTML のまま出力 ------------------------------------------------------
    def serialize(self, node, in_pre=False) -> str:
        if isinstance(node, str):
            # パーサが「タグではない」と判断した '<' (例: "<>" や "<日本語") は文字として出す
            node = node.replace("<", "&lt;")
            if in_pre:
                s = re.sub(r"\n[ \t]+(?=\n)", "\n", node)
                return re.sub(r"\n(?=\n)", "&#10;", s)
            return re.sub(r"\n[ \t]*(?:\n[ \t]*)+", "\n", node)
        if node.tag == "#comment":
            return "<!--" + node.children[0].replace("\n\n", "\n") + "-->"
        n2 = Node(node.tag, dict(node.attrs))
        if node.tag == "a" and "href" in n2.attrs:
            n2.attrs["href"] = self.fix_href(n2.attrs["href"])
        if node.tag == "img" and "src" in n2.attrs:
            n2.attrs["src"] = self.fix_src(n2.attrs["src"])
        open_t = self.open_tag(n2)
        if node.tag in VOID:
            return open_t
        inner = "".join(self.serialize(c, in_pre or node.tag == "pre") for c in node.children)
        return f"{open_t}{inner}</{node.tag}>"

    # -- ファイル全体 -------------------------------------------------------------
    def read_text(self, path: Path) -> str:
        data = path.read_bytes()
        for enc in (self.encoding, "utf-8", "euc_jp", "cp932"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    def find_include(self, name: str, base: Path):
        cands = [base.parent / name, self.repo / "text" / "part02" / name, self.repo / name]
        cands += list((self.repo / "text").glob(f"*/{name}"))
        for c in cands:
            if c.is_file():
                return c
        return None

    def heading(self, level: int, hid: str, title: str) -> Block:
        root = parse_fragment(title)
        text = self.inline(root.children).replace(BR, " ")
        text = re.sub(r"\s+", " ", text).strip()
        suffix = f" {{#{hid}}}" if hid and re.fullmatch(r"[\w\-.:]+", hid) else ""
        return Block("h", "#" * level + " " + text + suffix)

    def convert(self, path: Path):
        """戻り値: (meta, body_markdown)"""
        text = self.read_text(path)
        meta: dict[str, str] = {}
        segments = []
        buf: list[str] = []

        def flush():
            if buf:
                segments.append(("html", "\n".join(buf)))
                buf.clear()

        for line in text.splitlines():
            m = DIRECTIVE_RE.match(line)
            if m:
                flush()
                segments.append(("head", HEAD_LEVEL[m.group(1)], (m.group(2) or "").strip(),
                                 m.group(3).strip()))
                continue
            m = META_RE.match(line)
            if m:
                if m.group(1) != "COMMENT":
                    meta[m.group(1)] = m.group(2).strip()
                continue
            m = INCLUDE_RE.match(line)
            if m:
                inc = self.find_include(m.group(1), path)
                if inc is None:
                    self.warnings.append(f"{path}: %INCLUDE {m.group(1)} が見つかりません")
                else:
                    buf.append(self.read_text(inc))
                continue
            buf.append(line)
        flush()

        blocks: list[Block] = []
        for seg in segments:
            if seg[0] == "head":
                blocks.append(self.heading(seg[1], seg[2], seg[3]))
            else:
                blocks.extend(self.blocks(parse_fragment(seg[1]).children))
        body = "\n\n".join(b.text for b in blocks if b.text.strip()) + "\n"
        doc = self.doc_link(meta.get("TITLE", ""))
        if doc:
            body = doc + "\n\n" + body
        return meta, body

    def doc_link(self, title_html: str) -> str:
        """%TITLE <a href="https://www.postgresql.org/docs/...">…</a> のリンクは、
        タイトル(プレーンテキスト化される)から消えてしまうので本文の先頭に残す。"""
        m = re.search(r"<a\s[^>]*?href=[\"'](https?://[^\"']+)[\"']", title_html, re.I)
        if not m:
            return ""
        url = html.unescape(m.group(1))
        label = "公式ドキュメント" if "postgresql.org" in url else "参照"
        return f"{label}: [{md_escape(url)}]({self._dest(url)})"


# ---------------------------------------------------------------------------
# 目次ページ (トップページ / セクションのとびら) の本文
# ---------------------------------------------------------------------------

def toc_blocks(conv: Converter, sec: dict) -> list[str]:
    """セクション内のページを、Header の [小見出し] ごとにまとめたリストにする。"""
    out, items, last = [], [], None

    def flush():
        if items:
            out.append("\n".join(items))
            items.clear()

    for e in sec["entries"]:
        if e.is_index or e.hidden:
            continue
        if e.subgroup and e.subgroup != last:
            flush()
            out.append(Converter.wrap(md_escape(e.subgroup), "**", "strong"))
            last = e.subgroup
        items.append(f"- [{md_escape(e.title)}]({conv._dest(conv.page_url(e.slug))})")
    flush()
    return out


def section_toc_markdown(conv: Converter, sec: dict) -> str:
    blocks = toc_blocks(conv, sec)
    if not blocks:
        return ""
    return "\n\n".join(["---", "## 目次"] + blocks) + "\n"


def home_markdown(conv: Converter, toc: Toc) -> str:
    parts = []
    for sec in toc.sections:
        url = conv._dest(f"{conv.url_prefix}/{sec['name']}/")
        parts.append(f"## [{md_escape(sec['title'])}]({url})")
        parts.extend(toc_blocks(conv, sec))
    return "\n\n".join(parts) + "\n"


# ---------------------------------------------------------------------------
# front matter / 出力
# ---------------------------------------------------------------------------

def q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def plain_title(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def front_matter(title, link_title, weight, group, key, lastmod, hidden=False) -> str:
    lines = ["---", f"title: {q(title)}"]
    if link_title and link_title != title:
        lines.append(f"linkTitle: {q(link_title)}")
    if weight is not None:
        lines.append(f"weight: {weight}")
    if hidden:
        lines.append("hidden: true")      # Relearn: メニュー/一覧に出さない (URL では開ける)
    if group:
        lines.append(f"group: {q(group)}")
    if key:
        lines.append(f"key: {q(key)}")
    if lastmod:
        lines.append(f"lastmod: {lastmod}")
    lines.append("draft: false")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def parse_lastmod(v: str):
    m = re.match(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", v or "")
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="postgresqlref の text/*.txt を Hugo の content に変換する")
    ap.add_argument("repo", nargs="?", default="../", help="リポジトリのルート (既定: ../)")
    ap.add_argument("-o", "--out", default="content", help="出力先の content ディレクトリ (既定: content)")
    ap.add_argument("--header", help="目次を含む Header ファイル (既定: <repo>/template/Header)")
    ap.add_argument("--url-prefix", default="", help="サイト内リンクの接頭辞 例: /postgresqlref")
    ap.add_argument("--static-dir", help="指定すると参照画像を <static-dir>/images/ にコピーする")
    ap.add_argument("--code-lang", default="", help="<pre> に付ける既定の言語 (既定: なし)")
    ap.add_argument("--no-cjk-join", action="store_true",
                    help="日本語文中の改行を空白にせず詰める処理を無効にする")
    ap.add_argument("--encoding", default="utf-8", help="入力の文字コード (既定: utf-8、失敗時は euc-jp/cp932 を試す)")
    ap.add_argument("--site-title", default="", help="トップページのタイトル (既定: Header の <h1> から取得)")
    ap.add_argument("--include-unlisted", action="store_true",
                    help="目次 (Header) に載っていない原稿も、メニュー非表示 (hidden) で変換する")
    ap.add_argument("--no-home", action="store_true", help="トップページ (content/_index.md) を生成しない")
    ap.add_argument("--no-index-toc", action="store_true",
                    help="とびらページ末尾の「目次」一覧を付けない")
    ap.add_argument("--dry-run", action="store_true", help="ファイルを書かず、結果の一覧だけ表示する")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    header_path = Path(args.header) if args.header else repo / "template" / "Header"
    if not header_path.is_file():
        print(f"エラー: 目次ファイルが見つかりません: {header_path}", file=sys.stderr)
        return 1
    text_dir = repo / "text"
    if not text_dir.is_dir():
        print(f"エラー: text ディレクトリが見つかりません: {text_dir}", file=sys.stderr)
        return 1

    conv = Converter(toc=Toc(), repo=repo, url_prefix=args.url_prefix, code_lang=args.code_lang,
                     cjk_join=not args.no_cjk_join, encoding=args.encoding)
    conv.toc = parse_toc(conv.read_text(header_path))
    toc = conv.toc
    if not toc.pages:
        print("エラー: 目次 (<h5> / <a href=\"./xxx.html\">) を読み取れませんでした", file=sys.stderr)
        return 1

    out_root = Path(args.out)
    done_slugs: set[str] = set()
    written = 0
    section_index_written: set[str] = set()

    # 1) 原稿を走査して slug を集める。目次 (Header) に無いページは、同じ接頭辞のページがいる
    #    セクションに収容する (リンクの書き換えが全ページで一貫するよう、変換の前に行う)
    sources = []
    for path in sorted(text_dir.rglob("*.txt")):
        raw = conv.read_text(path)
        m = re.search(r"^%FILE[ \t]+(\S+)", raw, re.M)
        if not m:
            if args.verbose:
                print(f"skip (no %FILE): {path.relative_to(repo)}")
            continue
        slug = Path(m.group(1)).stem
        if slug not in toc.pages:
            # 元のサイトでも目次 (Header) から辿れないページ。古い下書きの残りであることが多いので、
            # 既定では変換しない。--include-unlisted なら、メニューに出さずに変換する。
            if not args.include_unlisted:
                conv.warnings.append(f"{path.relative_to(repo)}: '{slug}' は目次 (template/Header) に無いので"
                                     f" 変換しませんでした (含めるなら --include-unlisted)")
                continue
            t = re.search(r"^%TITLE[ \t]+(.*)$", raw, re.M)
            entry = toc.adopt(slug, plain_title(t.group(1)) if t else slug)
            entry.hidden = True
            conv.warnings.append(f"{path.relative_to(repo)}: '{slug}' は目次 (template/Header) に無いので"
                                 f" セクション '{entry.section}' にメニュー非表示 (hidden) で追加しました")
        sources.append((path, slug))

    # 2) 変換して書き出す
    for path, slug in sources:
        entry = toc.pages[slug]
        meta, body = conv.convert(path)
        title = plain_title(meta.get("TITLE", "")) or entry.title
        if entry.is_index:
            # サイドバー/パンくずには「とびら」ではなく、目次の見出し (<h5>) を使う
            link_title = entry.group
            if not args.no_index_toc:
                extra = section_toc_markdown(conv, toc.section_of(entry.section))
                if extra:
                    body = body.rstrip("\n") + "\n\n" + extra
        else:
            link_title = entry.title
        fm = front_matter(title, link_title, entry.weight, entry.subgroup,
                          meta.get("KEY", ""), parse_lastmod(meta.get("LASTMOD", "")),
                          hidden=entry.hidden)

        name = "_index.md" if entry.is_index else f"{slug}.md"
        dest = out_root / entry.section / name
        if entry.is_index:
            section_index_written.add(entry.section)
        done_slugs.add(slug)
        if "{{<" in body or "{{%" in body:
            conv.warnings.append(f"{dest}: '{{{{<' または '{{{{%' を含むため Hugo がショートコードと解釈する可能性があります")
        if args.dry_run:
            print(f"[dry-run] {path.relative_to(repo)} -> {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(fm + body, encoding="utf-8")
            if args.verbose:
                print(f"{path.relative_to(repo)} -> {dest}")
        written += 1

    # とびらページの無いセクション (param, plpgsql 等) には _index.md を作る
    for sec in toc.sections:
        if sec["name"] in section_index_written:
            continue
        dest = out_root / sec["name"] / "_index.md"
        if args.dry_run:
            print(f"[dry-run] (stub) -> {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            body = "" if args.no_index_toc else re.sub(r"\A---\n\n", "", section_toc_markdown(conv, sec))
            dest.write_text(front_matter(sec["title"], "", sec["weight"], "", "", None) + body,
                            encoding="utf-8")

    # トップページ: Header の目次と同じ構成の一覧
    if not args.no_home:
        dest = out_root / "_index.md"
        site_title = args.site_title or toc.site_title or "Manual"
        if args.dry_run:
            print(f"[dry-run] (home) -> {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(front_matter(site_title, "", None, "", "", None) + home_markdown(conv, toc),
                            encoding="utf-8")

    missing = [s for s in toc.pages if s not in done_slugs]
    for s in missing:
        # とびらのみ無いのは正常なことがあるので警告は穏やかに
        conv.warnings.append(f"目次にあるが text に対応する原稿が無い: {s}")

    # 画像のコピー
    if args.static_dir and conv.images:
        img_dir = Path(args.static_dir) / "images"
        for src in sorted(conv.images):
            name = src.replace("\\", "/").split("/")[-1]
            found = None
            for base in (repo / "html", repo / "Figures", repo):
                cand = base / src
                if cand.is_file():
                    found = cand
                    break
                cand = base / name
                if cand.is_file():
                    found = cand
                    break
            if found is None:
                conv.warnings.append(f"画像が見つかりません: {src}")
                continue
            if not args.dry_run:
                img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(found, img_dir / name)

    print(f"変換: {written} ファイル -> {out_root}/")
    if conv.images:
        print(f"参照画像: {len(conv.images)} 個" + (f" ({args.static_dir}/images/ にコピー)" if args.static_dir else
                                              " (--static-dir を指定するとコピーします)"))
    for w in conv.warnings:
        print("警告:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
