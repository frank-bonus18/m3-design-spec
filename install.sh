#!/usr/bin/env bash
#
# install.sh — 把 m3-design-spec 技能安装到助手的 skills 目录。
#
# 用法：
#   ./install.sh                     # 安装到 /skills
#   SKILLS_DIR=~/my-skills ./install.sh
#   ./install.sh --force             # 已有同名目录时直接覆盖，不备份
#   ./install.sh --no-check          # 跳过安装后的验证
#
# 目录名必须保持 m3-design-spec：SKILL.md 里的脚本路径是
# /skills/m3-design-spec/scripts/... 的绝对路径。

set -euo pipefail

SKILL_NAME="m3-design-spec"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/$SKILL_NAME"
SKILLS_DIR="${SKILLS_DIR:-/skills}"
DEST="$SKILLS_DIR/$SKILL_NAME"

FORCE=0
DO_CHECK=1
for arg in "$@"; do
  case "$arg" in
    --force|-f)   FORCE=1 ;;
    --no-check)   DO_CHECK=0 ;;
    -h|--help)
      sed -n '3,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "未知参数: $arg（试试 --help）" >&2
      exit 2 ;;
  esac
done

echo "m3-design-spec 安装器"
echo "  源目录  : $SRC"
echo "  目标目录: $DEST"
echo

if [ ! -d "$SRC" ]; then
  echo "✗ 找不到源目录 $SRC" >&2
  echo "  请在仓库根目录运行本脚本。" >&2
  exit 1
fi

# 目标父目录
if [ ! -d "$SKILLS_DIR" ]; then
  echo "→ 创建 $SKILLS_DIR"
  if ! mkdir -p "$SKILLS_DIR" 2>/dev/null; then
    echo "✗ 无法创建 $SKILLS_DIR，可能需要管理员权限。" >&2
    echo "  可以改用：SKILLS_DIR=~/my-skills ./install.sh" >&2
    exit 1
  fi
fi

# 写入权限预检
if [ ! -w "$SKILLS_DIR" ]; then
  echo "✗ 没有 $SKILLS_DIR 的写权限。" >&2
  echo "  用 sudo 重跑，或指定别的位置：SKILLS_DIR=~/my-skills ./install.sh" >&2
  exit 1
fi

# 已有安装
if [ -e "$DEST" ]; then
  if [ "$FORCE" -eq 1 ]; then
    echo "→ --force：删除已有安装"
    rm -rf "$DEST"
  else
    # 备份必须放在点目录里：skills 目录下任何含 SKILL.md 的子目录
    # 都可能被扫描器当成一个技能，备份到同级会凭空多出一个无效技能。
    BACKUP_ROOT="$SKILLS_DIR/.m3-backups"
    mkdir -p "$BACKUP_ROOT"
    BACKUP="$BACKUP_ROOT/$SKILL_NAME-$(date +%Y%m%d-%H%M%S)"
    echo "→ 已有安装，备份到 ${BACKUP#$SKILLS_DIR/}"
    mv "$DEST" "$BACKUP"
  fi
fi

echo "→ 复制技能文件"
cp -a "$SRC" "$DEST"

echo "→ 设置脚本执行权限"
chmod +x "$DEST"/scripts/* 2>/dev/null || true

echo "→ 统计安装结果"
FILES=$(find "$DEST" -type f | wc -l | tr -d ' ')
SIZE=$(du -sh "$DEST" | cut -f1)
echo "  $FILES 个文件，共 $SIZE"

if [ "$DO_CHECK" -eq 1 ]; then
  echo
  echo "→ 验证安装"

  ASSET="$DEST/assets/m3-component-library.html"
  FAILED=0

  if command -v python3 >/dev/null 2>&1; then
    if python3 "$DEST/scripts/check_m3_html.py" "$ASSET" >/tmp/m3-check.out 2>&1; then
      echo "  ✓ 静态校验通过"
    else
      echo "  ✗ 静态校验失败："
      sed 's/^/      /' /tmp/m3-check.out | tail -12
      FAILED=1
    fi
  else
    echo "  – 跳过静态校验（未找到 python3）"
  fi

  if command -v node >/dev/null 2>&1; then
    if node "$DEST/scripts/dom_harness.js" "$ASSET" >/tmp/m3-harness.out 2>&1; then
      echo "  ✓ 运行时执行无异常"
    else
      echo "  ✗ 运行时执行报告异常："
      sed 's/^/      /' /tmp/m3-harness.out | tail -8
      FAILED=1
    fi
    if node "$DEST/scripts/regression_tests.js" "$ASSET" >/tmp/m3-regress.out 2>&1; then
      PASSED=$(grep -o '通过 [0-9]* 项' /tmp/m3-regress.out | head -1)
      echo "  ✓ 行为回归 ${PASSED:-通过}"
    else
      echo "  ✗ 行为回归有失败项："
      grep 'FAIL' /tmp/m3-regress.out | head -6 | sed 's/^/      /'
      FAILED=1
    fi
  else
    echo "  – 跳过运行时与回归（未找到 node）"
  fi

  rm -f /tmp/m3-check.out /tmp/m3-harness.out /tmp/m3-regress.out

  if [ "$FAILED" -ne 0 ]; then
    echo
    echo "✗ 安装完成，但验证未通过。文件已就位：$DEST" >&2
    exit 1
  fi
fi

echo
echo "✓ 安装完成：$DEST"
echo
echo "下一步："
echo "  1. 在你的助手的技能管理里启用 $SKILL_NAME"
echo "  2. 让它做点 M3 相关的事试试，比如「用 M3 风格做一个设置页」"
echo
echo "自检命令："
echo "  python3 $DEST/scripts/check_m3_html.py $DEST/assets/m3-component-library.html"
echo "  node    $DEST/scripts/regression_tests.js $DEST/assets/m3-component-library.html"
