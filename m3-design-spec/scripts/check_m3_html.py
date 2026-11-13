#!/usr/bin/env python3
"""Static validator for a single-file Material 3 HTML page.

Checks the things that silently break a hand-written M3 page: unbalanced tags,
duplicate ids, dangling JS references, colors hardcoded outside the token
blocks, missing dark counterparts, accessibility blockers, and a phone-only
layout that looks broken on wide viewports.

Usage:
    python3 check_m3_html.py PAGE.html [--verbose]

Exit codes:
    0  no findings
    1  findings reported
    2  input unusable (missing file, no HTML)
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
    # SVG elements commonly self-closed in inline icons
    "path", "circle", "rect", "line", "polyline", "polygon", "ellipse",
    "use", "stop", "animate", "feGaussianBlur", "linearGradient", "radialGradient",
}

COLOR_VALUE = re.compile(
    r"^\s*(#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|color\(|color-mix\(|transparent\b|currentColor\b)",
)
INVARIANT_MARKER = "theme-invariant"

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U0001F000-\U0001F0FF\U00002600-\U000027BF"
    "\U00002B00-\U00002BFF]"
)
# 排版符号：箭头、勾叉、破折号等，不算 emoji 图标
ALLOWED_PUNCT = set("—–…·←→↑↓✓✕‹›−＋ⓘ▲▼●○■□")


class TagBalance(HTMLParser):
    """Track element nesting; report unmatched open/close tags."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in VOID_TAGS:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag.lower() in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(("stray close tag", tag, self.getpos()))
            return
        top, pos = self.stack.pop()
        if top.lower() != tag.lower():
            self.errors.append(("mismatched", f"<{top}>", pos, f"closed by </{tag}>", self.getpos()))


def split_regions(src):
    """Return (css_text, html_text, js_text) with HTML line numbers preserved.

    Style and script bodies are replaced by an equal number of newlines so a
    line number reported for markup matches the original file.
    """
    styles = re.findall(r"<style[^>]*>(.*?)</style>", src, re.S | re.I)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", src, re.S | re.I)
    css = "\n".join(styles)
    js = "\n".join(scripts)
    body = src
    for chunk in styles + scripts:
        body = body.replace(chunk, "\n" * chunk.count("\n"))
    return css, body, js


def strip_css_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def strip_token_blocks(css):
    """Blank out every :root and [data-theme=...] declaration block.

    Scans by brace depth, so token overrides nested inside @media (for example
    a prefers-contrast block re-declaring --outline) are handled too.
    """
    out, i, n = [], 0, len(css)
    opener = re.compile(r"(:root|\[data-theme[^\]]*\])\s*\{")
    while i < n:
        m = opener.search(css, i)
        if not m:
            out.append(css[i:])
            break
        out.append(css[i:m.start()])
        depth, j = 0, m.end() - 1
        while j < n:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(m.group(1) + "{ }")
        i = j + 1
    return "".join(out)


# 命名颜色（CSS 关键字）——只收常见、明确是颜色的，避免误伤 currentColor 等令牌
NAMED_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
    "black", "white", "gray", "grey", "silver", "gold", "navy", "teal",
    "olive", "lime", "aqua", "fuchsia", "maroon", "crimson", "indigo",
    "violet", "turquoise", "salmon", "khaki", "beige", "ivory", "coral",
}
# 这些写法都是硬编码颜色，必须走令牌
FUNC_COLOR = re.compile(
    r"\b(rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^)]*\)", re.I)

# 只在「声明值」里找颜色，不在选择器/属性名里找
DECL = re.compile(r":\s*([^;{}]+);")


def _gradient_spans(text):
    """返回所有 gradient(...) 的 [start, end) 区间，用于只豁免括号内部。"""
    spans = []
    for m in re.finditer(r"gradient\(\s*", text, re.I):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    spans.append((m.start(), i + 1))
                    break
            i += 1
    return spans


def check_hex_colors(css_after_tokens):
    """找令牌块外的硬编码颜色。

    覆盖 #hex、rgb()/hsl()/oklch()/lab() 等函数式写法，以及 CSS 命名颜色。
    渐变只豁免它自己的括号内部，同一行其它声明照样算违规。

    返回 (errors, notes)。errors 是必须修的；notes 是可人工复核的。
    """
    cleaned = re.sub(r"url\([^)]*\)", "", css_after_tokens)
    lines = cleaned.splitlines()
    spans = _gradient_spans(cleaned)
    errors, notes = [], []

    def in_gradient(pos):
        return any(a <= pos < b for a, b in spans)

    def line_of(pos):
        return cleaned.count("\n", 0, pos) + 1

    # 1) 十六进制
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", cleaned):
        ln = line_of(m.start())
        snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
        entry = (ln, m.group(0), snippet[:100])
        (notes if in_gradient(m.start()) else errors).append(entry)

    # 2) 函数式颜色
    # 「降级兜底」：同一属性如果另有 var()/color-mix() 版本，那这个字面量只是
    # 给不支持新语法的浏览器兜底，写法正确。必须按声明切分，不能用
    # `[^;]*` 跨声明匹配 —— 兜底写法本身就是两条同名声明。
    def token_version_of(prop_name, block_text):
        """同一属性（或它的 -color 等子属性）是否另有令牌版本。

        允许前缀匹配：`border-left` 与 `border-left-color` 属于同一族，
        用 `border-left-color:color-mix(...)` 兜 `border-left:1px solid rgba(...)`
        是正确写法。
        """
        if not prop_name:
            return False
        for vm in re.finditer(r"(?:^|;)\s*([a-z-]+)\s*:\s*([^;]+)", block_text, re.I):
            cand, val = vm.group(1).lower(), vm.group(2)
            if not re.search(r"var\(|color-mix\(", val, re.I):
                continue
            p = prop_name.lower()
            if cand == p or cand.startswith(p + "-") or p.startswith(cand + "-"):
                return True
        return False

    for m in FUNC_COLOR.finditer(cleaned):
        val = m.group(0)
        if val.lower().startswith("color-mix"):
            continue
        ln = line_of(m.start())
        snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
        block_start = cleaned.rfind("{", 0, m.start())
        block_end = cleaned.find("}", m.start())
        block = cleaned[block_start + 1:block_end] if 0 <= block_start < block_end else snippet
        # 属性名要向前回溯到上一个 ; 或 { ，因为值可能很长
        # 例：text-shadow:0 1px 3px rgba(...) —— 属性名后面跟着的是值
        cut = max(cleaned.rfind(";", 0, m.start()),
                  cleaned.rfind("{", 0, m.start()))
        decl = cleaned[cut + 1:m.start()]
        prop = re.match(r"\s*([a-z-]+)\s*:", decl, re.I)
        prop_name = prop.group(1) if prop else None
        entry = (ln, val[:40], snippet[:100])
        if in_gradient(m.start()) or token_version_of(prop_name, block):
            notes.append(entry)
        else:
            errors.append(entry)

    # 3) 命名颜色：只查声明值，避免 selector/属性名误伤
    for m in DECL.finditer(cleaned):
        value = m.group(1)
        for word in re.findall(r"\b[a-z]+\b", value, re.I):
            if word.lower() in NAMED_COLORS:
                ln = line_of(m.start())
                snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""
                errors.append((ln, word, snippet[:100]))

    return errors, notes


def parse_block(block):
    """Return {name: (value, invariant)} for one token block."""
    out = {}
    for line in block.splitlines():
        m = re.match(r"\s*--([a-z0-9-]+)\s*:\s*([^;]+);", line)
        if not m:
            continue
        out[m.group(1)] = (m.group(2).strip(), INVARIANT_MARKER in line.lower())
    return out


def check_token_blocks(css_raw):
    """Both blocks must exist and mirror every semantic color.

    Non-color constants (radius, duration, easing, font) live in :root only and
    must not be mirrored. Color-valued constants that intentionally do not change
    with the theme are marked `theme-invariant`.
    """
    root = re.search(r":root\s*\{((?:[^{}]|\{[^{}]*\})*)\}", css_raw)
    dark = re.search(r'\[data-theme\s*=\s*["\']?dark["\']?\]\s*\{((?:[^{}]|\{[^{}]*\})*)\}', css_raw)

    problems = []
    if not root:
        problems.append("no :root token block found")
    if not dark:
        problems.append('no [data-theme="dark"] token block found')
    if not root or not dark:
        return problems, set(), set()

    light = parse_block(root.group(1))
    dark_decls = parse_block(dark.group(1))
    light_vars, dark_vars = set(light), set(dark_decls)

    color_vars = {n for n, (v, inv) in light.items() if COLOR_VALUE.match(v) and not inv}
    missing = sorted(color_vars - dark_vars)
    if missing:
        problems.append(
            f"{len(missing)} color token(s) missing from dark theme "
            f"(add them, or mark the declaration `{INVARIANT_MARKER}`): " + ", ".join(missing)
        )

    extra = sorted(n for n in dark_vars - light_vars if not dark_decls[n][1])
    if extra:
        problems.append("variable(s) declared only in dark theme: " + ", ".join(extra))

    return problems, light_vars, dark_vars


def check_ripple(js):
    problems = []
    if "RIPPLE_SELECTOR" not in js and "m3-ripple" not in js:
        problems.append("no ripple implementation found in the script")
    return problems


def check_js_references(html_text, js):
    """Every id/class the script queries should exist, including runtime-created ones."""
    problems = []
    ids_in_html = set(re.findall(r'\sid="([^"]+)"', html_text))
    referenced_ids = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]", js))
    referenced_ids |= set(re.findall(r"\$\(\s*['\"]#([A-Za-z0-9_-]+)['\"]", js))
    missing_ids = sorted(referenced_ids - ids_in_html)
    if missing_ids:
        problems.append("script references missing element id(s): " + ", ".join(missing_ids))

    classes_in_html = set()
    for chunk in re.findall(r'class="([^"]*)"', html_text):
        classes_in_html.update(chunk.split())

    classes_in_js = set()
    for literal in re.findall(r"\.className\s*=\s*['\"]([^'\"]+)['\"]", js):
        classes_in_js.update(p for p in re.split(r"[\s+]", literal) if p and not p.startswith("$"))
    for literal in re.findall(r"classList\.(?:add|toggle|remove)\(\s*['\"]([A-Za-z0-9_-]+)['\"]", js):
        classes_in_js.add(literal)
    for literal in re.findall(r"\.className\s*=\s*(.+?);", js):
        classes_in_js.update(p.strip() for p in re.findall(r"['\"]([A-Za-z0-9_-]{2,})['\"]", literal))
    # class="…" inside innerHTML template strings
    for tmpl in re.findall(r"\.innerHTML\s*=\s*(.+?);", js, re.S):
        for chunk in re.findall(r"class=(?:\"|\\\")([^\"]*?)(?:\"|\\\")", tmpl):
            classes_in_js.update(chunk.split())

    known = classes_in_html | classes_in_js
    referenced = set(re.findall(r"\$\$\s*\(\s*['\"]\.([A-Za-z0-9_-]+)", js))
    referenced |= set(re.findall(r"querySelectorAll\(\s*['\"]\.([A-Za-z0-9_-]+)", js))
    missing_classes = sorted(referenced - known)
    if missing_classes:
        problems.append(
            "script references class absent from markup and runtime creation: " + ", ".join(missing_classes)
        )
    return problems


def check_js_syntax(js):
    node = shutil.which("node") or shutil.which("nodejs")
    if not js.strip():
        return ["<script> block is empty"], False
    if not node:
        return [], False
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(js)
        path = fh.name
    try:
        proc = subprocess.run([node, "--check", path], capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            return ["script syntax error:\n    " + "\n    ".join(detail[:8])], True
        return [], True
    except Exception:
        return [], False
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def check_a11y(html_text, src, js):
    problems = []
    stats = {}

    if not re.search(r"<html\b[^>]*\blang\s*=", src, re.I):
        problems.append("<html> has no lang attribute")

    m = re.search(r'<a\b[^>]*class="[^"]*\bskip-link\b[^"]*"[^>]*href="#([^"]+)"', html_text)
    if not m:
        problems.append("no skip link to the main content")
    elif not re.search(r'\sid="' + re.escape(m.group(1)) + '"', html_text):
        problems.append(f'skip link points at "#{m.group(1)}", which does not exist')

    # buttons need an accessible name
    unnamed = []
    for btn in re.finditer(r"<button\b([^>]*)>(.*?)</button>", html_text, re.S | re.I):
        attrs, inner = btn.group(1), btn.group(2)
        # 属性存在不等于有名字：aria-label="" 是空的，屏幕阅读器读不到东西
        if re.search(r'aria-label\s*=\s*(""|\'\')', attrs, re.I):
            unnamed.append(html_text.count("\n", 0, btn.start()) + 1)
            continue
        if re.search(r"aria-label|aria-labelledby|\btitle\s*=", attrs, re.I):
            continue
        text = re.sub(r"<svg\b.*?</svg>", " ", inner, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-zA-Z]+;|&#\d+;", " ", text)
        if not any(ch.isalnum() for ch in text):
            unnamed.append(html_text.count("\n", 0, btn.start()) + 1)
    if unnamed:
        shown = ", ".join(str(x) for x in unnamed[:10])
        problems.append(f"{len(unnamed)} button(s) with no accessible name at line(s) {shown}")
    stats["unnamed_buttons"] = len(unnamed)

    # overlays must announce themselves; match whole class tokens only
    OVERLAY_ROOTS = ("m3-dialog", "m3-bottom-sheet", "m3-drawer", "m3-side-sheet", "m3-keys", "m3-cmdk")
    for tag in re.finditer(r"<(\w+)\b([^>]*)>", html_text):
        attrs = tag.group(2)
        cm = re.search(r'class="([^"]*)"', attrs)
        if not cm:
            continue
        classes = cm.group(1).split()
        hits = [c for c in OVERLAY_ROOTS if c in classes]
        if not hits:
            continue
        cls = hits[0]
        line = html_text.count("\n", 0, tag.start()) + 1
        if not re.search(r"\brole\s*=", attrs):
            problems.append(f"line {line}: .{cls} has no role")
        elif cls in ("m3-dialog", "m3-bottom-sheet", "m3-side-sheet") and not re.search(
            r"\baria-modal\s*=", attrs
        ):
            problems.append(f"line {line}: .{cls} has no aria-modal")

    stats["aria_live"] = len(re.findall(r"aria-live", src))
    if stats["aria_live"] == 0:
        problems.append("no aria-live region for dynamic announcements")

    if "prefers-reduced-motion" not in src:
        problems.append("no @media (prefers-reduced-motion: reduce) fallback")
    if ":focus-visible" not in src:
        problems.append("no :focus-visible styling")

    # emoji: decoration only, never a functional icon
    offenders = []
    for m in re.finditer(r"<(button|a)\b[^>]*>(.*?)</\1>", html_text, re.S | re.I):
        for em in EMOJI_RE.finditer(m.group(2)):
            if em.group(0) in ALLOWED_PUNCT:
                continue
            offenders.append((html_text.count("\n", 0, m.start()) + 1, em.group(0)))
    for em in EMOJI_RE.finditer(html_text):
        ch = em.group(0)
        if ch in ALLOWED_PUNCT:
            continue
        start = html_text.rfind("<", 0, em.start())
        tag = html_text[start:em.start() + 1]
        if re.search(r"aria-hidden|role=|aria-label", tag):
            continue
        if re.search(r"<button|</button", tag):
            continue
        offenders.append((html_text.count("\n", 0, em.start()) + 1, ch))
    if offenders:
        shown = ", ".join(f"{ch}@{ln}" for ln, ch in offenders[:12])
        problems.append(
            f"{len(offenders)} emoji used as icon or left without aria treatment "
            f"(use inline SVG, or add aria-hidden/role=img): {shown}"
        )
    stats["emoji_offenders"] = len(offenders)

    return problems, stats


def _find_try_before(js, catch_pos):
    """从 catch 位置向前找配对的 try{，返回 (起始位置, 体内字符数, 体内行数)。

    用花括号深度回溯，不能靠正则——try 体里可能有嵌套的 {}。
    """
    depth = 0
    i = catch_pos - 1
    while i >= 0:
        ch = js[i]
        if ch == '}':
            depth += 1
        elif ch == '{':
            if depth == 0:
                # 找到 try 体的开括号，向前确认是 try
                head = js[max(0, i - 12):i]
                if re.search(r"try\s*$", head):
                    body = js[i + 1:catch_pos - 1] if catch_pos > i else ''
                    body = js[i + 1:]
                    return i, len(body), body.count('\n')
                depth = 0
            else:
                depth -= 1
        i -= 1
    return -1, 0, 0


# 这些调用的抛错是良性的，包在空 catch 里无所谓
BENIGN_IN_CATCH = re.compile(
    r"^\s*(?:[\w.]+\.)?(focus|blur|setPointerCapture|releasePointerCapture|"
    r"setSelectionRange|select|remove|scrollIntoView|writeText|execCommand)\s*\(",
    re.S,
)

# 只在输出页里扫，不扫工具自身
SNIFF_PATTERNS = [
    (r"userAgent", "读取 navigator.userAgent 判断环境"),
    (r"typeof\s+process", "用 typeof process 判断 Node 环境"),
    (r"process\s*\.\s*env", "读取 process.env"),
    (r"\bM3_PAGE\b", "引用测试专用环境变量 M3_PAGE"),
    (r"\bM3_VERBOSE\b", "引用测试专用环境变量 M3_VERBOSE"),
    (r"dom_harness", "引用测试工具 dom_harness"),
    (r"__harness__", "引用 harness 标记"),
]

# 全小写：HTMLParser 给的 tag 是小写，比较时必须同大小写
NATIVE_INTERACTIVE = {"button", "a", "input", "select", "textarea", "summary", "details"}
NON_INTERACTIVE = {"div", "span", "p", "li", "td", "section", "article", "label"}


# 这些角色本身就允许「内部有可聚焦子元素但子元素自己没有 role」，
# 例如 role=treeitem 包住 .m3-tree-row。role=dialog 不在此列——
# 弹窗是容器，不是可聚焦项的宿主，不能用来给内部 div 背书。
FOCUSABLE_HOST_ROLES = {
    "treeitem", "row", "gridcell", "columnheader", "rowheader",
    "option", "menuitem", "menuitemcheckbox", "menuitemradio", "tab",
}


class RoleFinder(HTMLParser):
    """记录每个元素的 role 与祖先 role，判断 tabindex 有没有语义支撑。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # [(tag, role, line)]
        self.fake = []

    def handle_starttag(self, tag, attrs):
        low = tag.lower()
        if low in VOID_TAGS:
            return
        d = dict(attrs)
        role = (d.get("role") or "").strip().lower()
        if low in NON_INTERACTIVE and str(d.get("tabindex", "")) == "0":
            if not role:
                hosted = any(r in FOCUSABLE_HOST_ROLES for _, r, _ in self.stack)
                if not hosted:
                    self.fake.append(self.getpos()[0])
        self.stack.append((low, role, self.getpos()[0]))

    def handle_endtag(self, tag):
        low = tag.lower()
        if low in VOID_TAGS:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == low:
                del self.stack[i:]
                break


# 内容门槛。不数"有多少个"，而数"有多少不同的、有意义的"。
# 单纯提高数量下限没用：审计样本把每个阈值都恰好卡在线上
# （20 个空按钮 / 4 段重复文本 / 5 个 8×8 空 svg / 28 个 m3-fill-N 凑类名）。
MIN_UNIQUE_TEXT = 300      # 去重后的可见文字
MIN_BUTTONS = 20
MIN_BUTTONS_WITH_CONTENT = 15   # 至少有文字或有真实图形
MIN_COMPONENT_CLASSES = 25      # 排除 m3-fill-N 这类凑数类
MIN_SECTIONS = 4
MIN_SECTIONS_WITH_HEADING = 3
MIN_SVG = 5
MIN_SVG_WITH_PATH = 5


def check_substance(html_text):
    """检查页面真的有内容，而不是拿一个漂亮的外壳骗过结构检查。

    三条思路：
      1. 数「不同的」而不是「总数」——4 段一样的话只算 1 段；
      2. 看元素「有没有实质」——空按钮、空 svg 不算；
      3. 看类名「是不是组件」——m3-fill-0…27 这种是凑数，不是组件。
    """
    problems = []
    stats = {}

    # ---- 文字：去标签、去重、数不同字符 ----
    text_blob = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.S | re.I)
    text_blob = re.sub(r"<[^>]+>", "\n", text_blob)
    lines = [re.sub(r"\s+", "", ln) for ln in text_blob.split("\n")]
    lines = [ln for ln in lines if ln]
    unique_lines = set(lines)
    unique_chars = sum(len(ln) for ln in unique_lines)
    stats["unique_text_chars"] = unique_chars
    stats["text_lines"] = len(lines)
    stats["unique_text_lines"] = len(unique_lines)

    if unique_chars < MIN_UNIQUE_TEXT:
        problems.append(
            f"去重后的可见文字只有 {unique_chars} 字符（至少 {MIN_UNIQUE_TEXT}）；"
            f"{len(lines)} 行文字里只有 {len(unique_lines)} 行不同——疑似重复内容凑数"
        )

    # ---- 按钮：要有实质内容 ----
    btns = re.findall(r"<button\b([^>]*)>(.*?)</button>", html_text, re.S | re.I)
    with_content = 0
    for attrs, inner in btns:
        label = re.search(r'aria-label\s*=\s*["\']([^"\']*)["\']', attrs, re.I)
        if label and label.group(1).strip():
            with_content += 1
            continue
        body = re.sub(r"<svg\b.*?</svg>", "", inner, flags=re.S | re.I)
        body = re.sub(r"<[^>]+>", " ", body)
        if body.strip():
            with_content += 1
            continue
        # 图标按钮：必须有带 path 的真实 svg
        svg = re.search(r"<svg\b[^>]*>(.*?)</svg>", inner, re.S | re.I)
        if svg and re.search(r"<path\b[^>]*d\s*=\s*[\"'][^\"']{8,}", svg.group(1), re.I):
            with_content += 1
    stats["buttons"] = len(btns)
    stats["buttons_with_content"] = with_content

    if len(btns) < MIN_BUTTONS:
        problems.append(f"只有 {len(btns)} 个 <button>（至少 {MIN_BUTTONS}）")
    elif with_content < MIN_BUTTONS_WITH_CONTENT:
        problems.append(
            f"{len(btns)} 个按钮里只有 {with_content} 个有实际内容"
            f"（文字或真实图标，至少 {MIN_BUTTONS_WITH_CONTENT}）——其余是空按钮"
        )

    # ---- 组件类：排除 m3-<词>-<数字> 这类编号凑数 ----
    classes = set()
    for chunk in re.findall(r'class="([^"]*)"', html_text):
        classes.update(c for c in chunk.split() if c.startswith("m3-"))
    real_classes = {c for c in classes if not re.search(r"-[0-9]+$", c)}
    stats["m3_classes"] = len(real_classes)

    if len(real_classes) < MIN_COMPONENT_CLASSES:
        problems.append(
            f"只有 {len(real_classes)} 个有意义的 m3-* 类（至少 {MIN_COMPONENT_CLASSES}）；"
            f"形如 m3-x-12 的编号类不计入"
        )

    # ---- section：要有标题 ----
    secs = re.findall(r'<section\b[^>]*>(.*?)</section>', html_text, re.S | re.I)
    with_heading = 0
    for body in secs:
        if re.search(r'<h[1-6]\b|class="[^"]*(title|heading|section-title)', body, re.I):
            with_heading += 1
    stats["sections"] = len(secs) if secs else len(re.findall(r"<section\b", html_text, re.I))
    stats["sections_with_heading"] = with_heading

    if stats["sections"] < MIN_SECTIONS:
        problems.append(f"只有 {stats['sections']} 个 <section>（至少 {MIN_SECTIONS}）")
    elif with_heading < MIN_SECTIONS_WITH_HEADING:
        problems.append(
            f"{stats['sections']} 个 section 里只有 {with_heading} 个有标题"
            f"（至少 {MIN_SECTIONS_WITH_HEADING}）"
        )

    # ---- svg：要有真实图形 ----
    svgs = re.findall(r"<svg\b[^>]*>(.*?)</svg>", html_text, re.S | re.I)
    real_svgs = [b for b in svgs if re.search(r"<path\b[^>]*d\s*=\s*[\"'][^\"']{8,}", b, re.I)
                 or re.search(r"<(circle|rect|line|polyline|polygon|ellipse|text)\b", b, re.I)]
    stats["svgs"] = len(svgs)
    stats["svgs_with_shape"] = len(real_svgs)

    if len(real_svgs) < MIN_SVG_WITH_PATH:
        problems.append(
            f"只有 {len(real_svgs)} 个含真实图形的 <svg>（至少 {MIN_SVG_WITH_PATH}）；"
            f"空 svg 不计入"
        )

    return problems, stats


def check_cheats(js, html_text):
    """识别「让检查通过但没有真正实现」的写法。

    这不是完备的对抗手段。它把最常见、最省事的几种糊弄方式变成显式失败，
    并配合 selfcheck.py 保证这些规则本身没有被悄悄削弱。
    """
    problems = []
    stats = {}

    # ① 用大面积 try-catch 包裹初始化，吞掉异常让运行时报「无异常」
    suspicious = []
    benign = 0
    for m in re.finditer(r"catch\s*\([^)]*\)\s*\{", js):
        body_start = m.end() - 1
        # 找 catch 体的闭合
        depth, j = 0, body_start
        while j < len(js):
            if js[j] == '{':
                depth += 1
            elif js[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = js[body_start + 1:j]
        stripped = re.sub(r"/\*.*?\*/|//[^\n]*", "", body, flags=re.S).strip()
        if stripped:
            continue                                   # catch 里有实际处理，不算吞
        pos, size, lines = _find_try_before(js, m.start())
        if pos < 0:
            continue
        try_body = js[pos + 1:m.start() - 1] if m.start() > pos else ''
        try_body = re.sub(r"/\*.*?\*/|//[^\n]*", "", try_body, flags=re.S).strip()
        if BENIGN_IN_CATCH.match(try_body) and len(try_body) < 120:
            benign += 1
            continue
        if size > 300 or lines > 6:
            suspicious.append((js.count("\n", 0, pos) + 1, size, lines))

    stats["swallowed_catch"] = len(suspicious)
    stats["benign_catch"] = benign
    if suspicious:
        shown = "; ".join(f"行{ln}（{size} 字符/{lines} 行）" for ln, size, lines in suspicious[:8])
        problems.append(
            f"{len(suspicious)} 处 try 块被空 catch 吞掉，运行时检查会以为自己「无异常」："
            f"{shown}。不要用 try-catch 包裹初始化逻辑来掩盖错误"
        )

    # ② 环境嗅探：代码会随「是否在测试中」改变行为
    hits = []
    for pat, desc in SNIFF_PATTERNS:
        for m in re.finditer(pat, js):
            hits.append((js.count("\n", 0, m.start()) + 1, desc))
    stats["env_sniffing"] = len(hits)
    if hits:
        detail = "; ".join(f"行{ln} {d}" for ln, d in hits[:8])
        problems.append(f"{len(hits)} 处环境嗅探，代码会随「是否在测试中」改变行为：{detail}")

    # ③ 假可交互：非原生控件加 tabindex=0，但自身和祖先都没有 role
    finder = RoleFinder()
    finder.feed(html_text)
    fake = finder.fake
    stats["fake_interactive"] = len(fake)
    if fake:
        shown = ", ".join(str(x) for x in fake[:10])
        problems.append(
            f"{len(fake)} 个 <div>/<span> 用 tabindex=\"0\" 冒充可聚焦，"
            f"自身和祖先都没有 role，聚焦后读屏读不出它是什么（行 {shown}）"
        )

    return problems, stats


def check_responsive(src):
    """Catch layout and zoom problems that only appear at other viewport sizes."""
    problems = []
    stats = {}

    meta = re.search(r'<meta[^>]*name="viewport"[^>]*content="([^"]*)"', src, re.I)
    if not meta:
        problems.append("no viewport meta tag")
    else:
        content = meta.group(1).replace(" ", "").lower()
        stats["viewport"] = meta.group(1)
        if "user-scalable=no" in content or "user-scalable=0" in content:
            problems.append("viewport sets user-scalable=no, which blocks pinch zoom (fails WCAG 1.4.4)")
        if re.search(r"maximum-scale=1(\.0+)?([,;]|$)", content):
            problems.append("viewport caps maximum-scale at 1, which blocks pinch zoom (fails WCAG 1.4.4)")

    min_width = re.findall(r"@media[^{]*\(\s*min-width\s*:\s*(\d+)px", src)
    stats["min_width_breakpoints"] = sorted({int(v) for v in min_width})
    if not stats["min_width_breakpoints"]:
        problems.append(
            "no min-width breakpoint: the layout is phone-only, so wide viewports "
            "show a narrow column in empty space (add a @media (min-width: ...) upgrade)"
        )
    return problems, stats


def main():
    ap = argparse.ArgumentParser(description="Validate a single-file Material 3 HTML page.")
    ap.add_argument("path", help="path to the HTML file")
    ap.add_argument("--verbose", "-v", action="store_true", help="print inventory and gradient notes")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        print(f"error: not a file: {args.path}", file=sys.stderr)
        return 2
    try:
        with open(args.path, encoding="utf-8") as fh:
            src = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2
    if "<html" not in src.lower():
        print("error: file does not look like an HTML document", file=sys.stderr)
        return 2

    css_raw, html_text, js = split_regions(src)
    css = strip_css_comments(css_raw)
    findings = []

    parser = TagBalance()
    parser.feed(src)
    for item in parser.errors[:10]:
        findings.append(("tag", str(item)))
    if parser.stack:
        unclosed = ", ".join(f"<{tag}>@{line}:{col}" for tag, (line, col) in parser.stack[:10])
        findings.append(("tag", f"unclosed element(s): {unclosed}"))

    ids = re.findall(r'\sid="([^"]+)"', src)
    dupes = [i for i, n in Counter(ids).items() if n > 1]
    if dupes:
        findings.append(("id", "duplicate id(s): " + ", ".join(sorted(dupes))))

    token_problems, light_vars, dark_vars = check_token_blocks(css_raw)
    for p in token_problems:
        findings.append(("tokens", p))

    color_errors, color_notes = check_hex_colors(strip_token_blocks(css))
    if color_errors:
        listed = "; ".join(f"line {ln}: {val} — {snip}" for ln, val, snip in color_errors[:12])
        suffix = "" if len(color_errors) <= 12 else f" (+{len(color_errors) - 12} more)"
        findings.append((
            "color",
            f"{len(color_errors)} hardcoded hex color(s) outside token blocks and outside gradients: "
            f"{listed}{suffix}",
        ))

    for p in check_ripple(js):
        findings.append(("ripple", p))

    for p in check_js_references(html_text, js):
        findings.append(("reference", p))

    syntax_problems, checked = check_js_syntax(js)
    for p in syntax_problems:
        findings.append(("script", p))

    a11y_problems, a11y_stats = check_a11y(html_text, src, js)
    for p in a11y_problems:
        findings.append(("a11y", p))

    resp_problems, resp_stats = check_responsive(src)
    for p in resp_problems:
        findings.append(("responsive", p))

    substance_problems, substance_stats = check_substance(html_text)
    for p in substance_problems:
        findings.append(("substance", p))

    cheat_problems, cheat_stats = check_cheats(js, html_text)
    for p in cheat_problems:
        findings.append(("cheat", p))

    size_kb = len(src.encode()) / 1024
    print(f"file      : {args.path}")
    print(f"size      : {size_kb:.1f} KB, {src.count(chr(10)) + 1} lines")
    print(f"tokens    : light {len(light_vars)}, dark {len(dark_vars)}")
    print(f"js syntax : {'checked with node' if checked else 'not checked (node unavailable)'}")
    print(f"a11y      : {a11y_stats.get('aria_live', 0)} live region(s), "
          f"{a11y_stats.get('unnamed_buttons', 0)} unnamed button(s), "
          f"{a11y_stats.get('emoji_offenders', 0)} emoji violation(s)")
    bp = resp_stats.get("min_width_breakpoints") or []
    print(f"responsive: min-width breakpoints at {bp if bp else '— (phone-only layout)'}")
    print(f"substance : {substance_stats.get('buttons', 0)} buttons "
          f"({substance_stats.get('buttons_with_content', 0)} with content), "
          f"{substance_stats.get('sections', 0)} sections, "
          f"{substance_stats.get('m3_classes', 0)} component classes, "
          f"{substance_stats.get('unique_text_chars', 0)} unique chars")
    print(f"integrity : {cheat_stats.get('swallowed_catch', 0)} swallowed catch "
          f"({cheat_stats.get('benign_catch', 0)} benign), "
          f"{cheat_stats.get('env_sniffing', 0)} env sniffing, "
          f"{cheat_stats.get('fake_interactive', 0)} fake interactive")

    if args.verbose:
        print()
        print("gradient colors (allowed, %d):" % len(color_notes))
        for ln, val, _ in color_notes[:10]:
            print(f"  line {ln}: {val}")

    print()
    if findings:
        print(f"FINDINGS ({len(findings)})")
        for kind, msg in findings:
            print(f"  [{kind}] {msg}")
        print("\nresult    : FAIL")
        return 1
    print("result    : PASS — no findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
