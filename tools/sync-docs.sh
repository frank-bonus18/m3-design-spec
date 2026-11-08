#!/usr/bin/env bash
# 把参考实现同步到 docs/index.html，供 GitHub Pages 提供在线演示。
# 改完 assets 里的组件库后跑一次，否则线上演示会落后。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
cp "$ROOT/m3-design-spec/assets/m3-component-library.html" "$ROOT/docs/index.html"
echo "✓ docs/index.html 已同步（$(du -h "$ROOT/docs/index.html" | cut -f1)）"
