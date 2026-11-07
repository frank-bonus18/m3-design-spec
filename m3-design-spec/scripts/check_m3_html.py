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
    styles = re.findall(r"<style[^>]*>(.*?)</style>", src, re.S)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", src, re.S)
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


def check_hex_colors(css_after_tokens):
    """Return (errors, notes).

    Hex values that only appear inside a gradient are decorative artwork and are
    reported as notes. Everything else must be a token, or it will not follow
    the theme.
    """
    cleaned = re.sub(r"url\([^)]*\)", "", css_after_tokens)
    errors, notes = [], []
    lines = cleaned.splitlines()
    for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", cleaned):
        line = cleaned.count("\n", 0, m.start()) + 1
        snippet = lines[line - 1].strip() if 0 < line <= len(lines) else ""
        entry = (line, m.group(0), snippet[:100])
        if "gradient(" in snippet:
            notes.append(entry)
        else:
            errors.append(entry)
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
