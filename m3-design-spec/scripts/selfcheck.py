#!/usr/bin/env python3
"""selfcheck.py — 验证检查器本身没有被削弱（变异测试）。

为什么需要：如果检查器被删了几条规则，它会对坏代码照样输出 PASS，
于是「检查通过」变成一句空话。这个脚本对已知缺陷逐个打补丁，断言对应
检查器必须失败。任何规则被悄悄删掉，这里就会红。

用法：
    python3 selfcheck.py [--base PATH] [--verbose]

    --base  参考实现路径，默认 ../assets/m3-component-library.html
    --verbose  打印每个变异的具体命中输出

退出码：
    0  所有变异都被检出，基线干净
    1  有变异漏检（说明规则被削弱），或基线本身不干净
    2  环境不可用
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent


def run(cmd, timeout=180):
    """执行命令，返回 (退出码, 输出)。"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, '（超时）'
    except FileNotFoundError:
        return 127, '（命令不存在）'


def has(cmd):
    return shutil.which(cmd) is not None


# ---------------------------------------------------------------- 变异定义
# (名称, 需要哪个检查器, 变异函数)
def mut_drop_dark_token(src):
    return src.replace('  --surface-container-high:#282A2F;\n', '', 1)


def mut_hardcode_hex(src):
    return src.replace('.m3-card{', '.m3-card{color:#FF00AA;', 1)


def mut_remove_minwidth(src):
    return re.sub(r'@media \(min-width:\d+px\)\{[^}]*\{[^}]*\}[^}]*\}', '', src)


def mut_block_zoom(src):
    return src.replace('initial-scale=1.0,', 'initial-scale=1.0, user-scalable=no,', 1)


def mut_remove_skiplink(src):
    return re.sub(r'<a class="skip-link"[^>]*>[^<]*</a>', '', src, count=1)


def mut_emoji_icon(src):
    return src.replace('data-snack="Filled 按钮">Filled',
                       'data-snack="Filled 按钮">🚀 Filled', 1)


def mut_empty_aria(src):
    return src.replace('id="searchBtn" aria-label="搜索"',
                       'id="searchBtn" aria-label=""', 1)


def mut_swallow_catch(src):
    out = src.replace(
        '  /* =====================================================================\n     1. 主题切换',
        '  try {\n  /* =====================================================================\n     1. 主题切换', 1)
    return out.replace('  })();\n\n})();', '  })();\n\n} catch(e){}\n})();', 1)


def mut_env_sniff(src):
    return src.replace(
        '  /* =====================================================================\n     1. 主题切换',
        "  if (navigator.userAgent === 'node') { return; }\n"
        '  /* =====================================================================\n     1. 主题切换', 1)


def mut_fake_tabindex(src):
    return src.replace(
        '<div class="m3-list-item m3-ripple-surface" data-sheet="复制链接">',
        '<div class="m3-list-item m3-ripple-surface" data-sheet="复制链接" tabindex="0">', 1)


def mut_hollow_shell(src):
    """把页面掏空成只剩最外层壳：结构检查全满足，但没有任何内容。"""
    import re
    head = re.search(r'(<!DOCTYPE.*?<body[^>]*>)', src, re.S)
    if not head:
        return src
    return head.group(1) + """
<a class="skip-link" href="#mainContent">跳到主要内容</a>
<div class="lib"><div class="container" id="mainContent" role="main" tabindex="-1"></div></div>
<div class="m3-scrim" id="scrim" role="dialog" aria-modal="true"></div>
<div class="sr-only" role="status" aria-live="polite"></div>
<script>
document.addEventListener('pointerdown', function(e){ /* RIPPLE_SELECTOR */ }, {passive:true});
</script>
</body></html>"""


def mut_break_js(src):
    return src.replace('var RIPPLE_SELECTOR = [', 'var RIPPLE_SELECTOR = [[', 1)


def mut_clickable_div(src):
    """给页面加一个可点击但不可聚焦的 div —— 键盘审计必须抓到。"""
    out = src.replace('<body>', '<body>\n<div id="spy-probe">点我</div>', 1)
    return out.replace('})();\n</script>',
                       "document.getElementById('spy-probe')"
                       ".addEventListener('click', function(){});\n})();\n</script>", 1)


def mut_break_date_roving(src):
    return src.replace('btn.tabIndex = sameDay(d, selected) ? 0 : -1;', '', 1)


MUTATIONS = [
    ('删掉一个暗色令牌',            'static',   mut_drop_dark_token),
    ('组件里硬编码颜色',            'static',   mut_hardcode_hex),
    ('删掉全部 min-width 断点',     'static',   mut_remove_minwidth),
    ('viewport 禁止缩放',           'static',   mut_block_zoom),
    ('删掉跳转链接',                'static',   mut_remove_skiplink),
    ('用 emoji 当按钮图标',         'static',   mut_emoji_icon),
    ('按钮 aria-label 写成空串',    'static',   mut_empty_aria),
    ('用空 catch 吞掉初始化异常',   'static',   mut_swallow_catch),
    ('按 userAgent 嗅探测试环境',   'static',   mut_env_sniff),
    ('div 加 tabindex 冒充可聚焦',  'static',   mut_fake_tabindex),
    ('空壳页面（结构对但没内容）',   'static',   mut_hollow_shell),
    ('破坏 JS 语法',                'harness',  mut_break_js),
    ('可点击但不可聚焦的 div',      'audit',    mut_clickable_div),
    ('删掉日期格的 roving tabindex', 'regress', mut_break_date_roving),
]

CHECKERS = {
    'static':  ('静态校验',  'check_m3_html.py'),
    'harness': ('运行时',    'dom_harness.js'),
    'audit':   ('键盘审计',  'audit_keyboard.js'),
    'regress': ('回归测试',  'regression_tests.js'),
}


def main():
    ap = argparse.ArgumentParser(description='变异测试：确认检查器能抓到已知缺陷。')
    ap.add_argument('--base', default=str(SKILL / 'assets' / 'm3-component-library.html'))
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    base = Path(args.base)
    if not base.is_file():
        print(f'✗ 找不到基线文件: {base}', file=sys.stderr)
        return 2
    if not has('node'):
        print('✗ 需要 node（运行时、审计、回归都要用）', file=sys.stderr)
        return 2

    src = base.read_text(encoding='utf-8')
    print(f'基线: {base}')
    print(f'大小: {len(src.encode()) / 1024:.1f} KB')
    print()

    # ---- 0. 基线必须全部干净 ----
    failures = []
    print('基线自检（应全部通过）')
    for kind, (label, script) in CHECKERS.items():
        path = HERE / script
        cmd = ([sys.executable, str(path)] if script.endswith('.py')
               else ['node', str(path)])
        code, out = run(cmd + [str(base)])
        ok = (code == 0)
        print(f'  {"✓" if ok else "✗"} {label:<6} exit={code}')
        if not ok:
            failures.append(f'基线不干净：{label}')
            if args.verbose:
                print('\n'.join('      ' + l for l in out.strip().splitlines()[-8:]))
    print()

    # ---- 1. 逐个变异 ----
    print('变异测试（每个都必须被检出）')
    tmpdir = tempfile.mkdtemp(prefix='m3-selfcheck-')
    missed = []
    try:
        for i, (name, kind, fn) in enumerate(MUTATIONS, 1):
            mutated = fn(src)
            if mutated == src:
                print(f'  ⚠ {name:<26} 变异未生效（锚点已变），请更新 selfcheck')
                missed.append(f'{name}（变异未生效）')
                continue

            path = Path(tmpdir) / f'm{i}.html'
            path.write_text(mutated, encoding='utf-8')

            label, script = CHECKERS[kind]
            spath = HERE / script
            cmd = ([sys.executable, str(spath)] if script.endswith('.py')
                   else ['node', str(spath)])
            code, out = run(cmd + [str(path)])

            caught = (code == 1)
            print(f'  {"✓" if caught else "✗"} {name:<26} → {label} exit={code}')
            if not caught:
                missed.append(f'{name} → {label} 漏检')
                if args.verbose:
                    print('\n'.join('      ' + l for l in out.strip().splitlines()[-10:]))
            elif args.verbose:
                hit = [l.strip() for l in out.splitlines()
                       if l.strip().startswith('[') or 'FAIL' in l][:3]
                for h in hit:
                    print(f'      {h[:110]}')
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print()
    total = len(MUTATIONS)
    caught_n = total - len(missed)
    print(f'检出 {caught_n} / {total}')

    if missed:
        print()
        print('✗ 有漏检，检查器可能被削弱了：')
        for m in missed:
            print(f'  - {m}')
        return 1

    if failures:
        print()
        for f in failures:
            print(f'✗ {f}')
        return 1

    print('✅ 所有变异都被检出，基线干净')
    return 0


if __name__ == '__main__':
    sys.exit(main())
