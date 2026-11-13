#!/usr/bin/env bash
#
# check.sh — 一条命令跑完四项检查。
#
# 默认输出 5 行摘要；失败时自动展开细节。这样「跑检查」的成本从
# 记四条命令 + 读四种输出，降成敲一次。
#
# 用法：
#   ./check.sh                          # 检查默认的参考实现
#   ./check.sh path/to/page.html        # 检查指定页面
#   ./check.sh --verbose                # 总是展开每项的输出
#   ./check.sh --json                   # 机器可读结果（给 agent 解析）
#
# 退出码：
#   0  全部通过
#   1  有检查未通过
#   2  环境不完整（缺 node / python3），无法给出结论
#
# 重要：缺依赖时退出码是 2 而不是 0。「没检查」绝不能看起来像「检查通过」。

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"
DEFAULT_PAGE="$ROOT/assets/m3-component-library.html"

PAGE=""
VERBOSE=0
JSON=0

for arg in "$@"; do
  case "$arg" in
    --verbose|-v) VERBOSE=1 ;;
    --json)       JSON=1 ;;
    -h|--help)
      sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    -*)
      echo "未知参数: $arg（试试 --help）" >&2
      exit 2 ;;
    *)
      PAGE="$arg" ;;
  esac
done

[ -z "$PAGE" ] && PAGE="$DEFAULT_PAGE"

if [ ! -f "$PAGE" ]; then
  echo "✗ 找不到文件: $PAGE" >&2
  exit 2
fi

# ---- 依赖预检：缺什么就直接说，不假装通过 ----
HAVE_PY=0; HAVE_NODE=0
command -v python3 >/dev/null 2>&1 && HAVE_PY=1
command -v node    >/dev/null 2>&1 && HAVE_NODE=1

MISSING=""
[ "$HAVE_PY" -eq 0 ]   && MISSING="python3"
[ "$HAVE_NODE" -eq 0 ] && MISSING="${MISSING:+$MISSING, }node"

if [ -n "$MISSING" ]; then
  echo "✗ 缺少依赖: $MISSING" >&2
  echo "  静态校验需要 python3；运行时 / 审计 / 回归需要 node。" >&2
  echo "  退出码 2 表示「无法给出结论」，不是「通过」。" >&2
  exit 2
fi

START=$(date +%s)
RESULTS=()          # "name|status|detail"
FAILED=0
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

run_one() {
  # $1=标签 $2=命令… 
  local label="$1"; shift
  local out="$TMP/$label.out"
  if "$@" >"$out" 2>&1; then
    RESULTS+=("$label|pass|")
  else
    local code=$?
    if [ "$code" -eq 2 ]; then
      RESULTS+=("$label|skip|无输出")
    else
      RESULTS+=("$label|fail|$(tail -n 1 "$out" | tr -d '\r')")
      FAILED=1
    fi
  fi
}

run_one "静态校验" python3 "$HERE/check_m3_html.py" "$PAGE"
run_one "运行时"   node    "$HERE/dom_harness.js" "$PAGE"
run_one "键盘审计" node    "$HERE/audit_keyboard.js" "$PAGE"
run_one "行为回归" node    "$HERE/regression_tests.js" "$PAGE"

ELAPSED=$(( $(date +%s) - START ))

# ---- 从输出里抽一句要点 ----
detail_of() {
  local label="$1" out="$TMP/$label.out"
  case "$label" in
    静态校验)
      local b c
      b=$(grep -oE '^substance : [0-9]+' "$out" | grep -oE '[0-9]+')
      c=$(grep -oE '[0-9]+ component classes' "$out" | grep -oE '^[0-9]+')
      echo "${b} 个按钮 · ${c} 个组件类" ;;
    运行时)   grep -oE '[0-9]+' <<<"$(grep '元素总数' "$out")" | head -1 | sed 's/$/ 个元素/' ;;
    键盘审计)
      local n
      n=$(grep -oE '其中 [0-9]+ 个是期望例外' "$out" | grep -oE '[0-9]+' | head -1)
      if [ -n "$n" ]; then echo "无不可达目标（$n 个期望例外）"; else echo "无不可达目标"; fi ;;
    行为回归) grep -oE '通过 [0-9]+ 项' "$out" | head -1 ;;
  esac
}

if [ "$JSON" -eq 1 ]; then
  printf '{"page":"%s","elapsed":%d,"failed":%s,"checks":[' "$PAGE" "$ELAPSED" "$([ $FAILED -eq 1 ] && echo true || echo false)"
  first=1
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r label status detail <<<"$r"
    [ $first -eq 0 ] && printf ','
    first=0
    printf '{"name":"%s","status":"%s"}' "$label" "$status"
  done
  printf ']}\n'
  exit $FAILED
fi

echo "检查 $PAGE"
echo
for r in "${RESULTS[@]}"; do
  IFS='|' read -r label status detail <<<"$r"
  case "$status" in
    pass)
      d=$(detail_of "$label")
      printf "  ✓ %-8s %s\n" "$label" "${d:-通过}" ;;
    fail)
      printf "  ✗ %-8s %s\n" "$label" "未通过" ;;
    skip)
      printf "  – %-8s 跳过\n" "$label" ;;
  esac
done

# 失败时展开细节
if [ "$FAILED" -eq 1 ] || [ "$VERBOSE" -eq 1 ]; then
  echo
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r label status detail <<<"$r"
    if [ "$status" = "fail" ] || [ "$VERBOSE" -eq 1 ]; then
      echo "── $label ──"
      tail -n 25 "$TMP/$label.out" | sed 's/^/  /'
      echo
    fi
  done
fi

if [ "$FAILED" -eq 1 ]; then
  echo "结果: ✗ 有检查未通过（${ELAPSED}s）"
  echo
  echo "修完再跑一次 ./check.sh，直到四项全绿。"
  exit 1
fi

echo "结果: ✅ 全部通过（${ELAPSED}s）"
exit 0
