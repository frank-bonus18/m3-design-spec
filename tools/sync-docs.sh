#!/usr/bin/env bash
# 在线预览现在由根目录的 index.html 重定向到技能资产，
# 不再保留第二份 515 KB 的副本。这个脚本只做一致性核对。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
ASSET="$ROOT/m3-design-spec/assets/m3-component-library.html"
TARGET="$ROOT/m3-design-spec/assets/m3-component-library.html"

[ -f "$ASSET" ] || { echo "✗ 找不到 $ASSET" >&2; exit 1; }
if grep -q "m3-design-spec/assets/m3-component-library.html" "$ROOT/index.html"; then
  echo "✓ index.html 指向 $TARGET（$(du -h "$ASSET" | cut -f1)）"
else
  echo "✗ index.html 的重定向目标已变更，请同步更新" >&2
  exit 1
fi
