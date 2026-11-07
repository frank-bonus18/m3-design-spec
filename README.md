# m3-design-spec

一个 **Material 3（Material You / Android 13）设计规范技能**，给 AI 助手用。

装上它之后，助手能按统一的令牌体系产出 M3 界面，并且自带四个检查工具把质量卡住：静态校验、运行时执行、键盘可达性审计、129 项行为回归。

产物是**单文件、零依赖**的 HTML：双击就能打开，不联网、不起服务器也能跑。

---

## 它解决什么问题

手写 M3 界面时，反复踩的坑就那么几个：

- 颜色硬编码 → 暗色模式失效
- 暗色令牌漏写几个 → 切主题时局部不变色
- 水波纹逐个元素绑定 → 动态插入的节点没有反馈
- 可点元素不是按钮 → 键盘用户够不到
- 只做了手机宽度 → 平板上是「一根细条浮在空白里」
- 通知上限写成 `while (children.length >= 3) dismiss(children[0])` → **同步死循环，整个标签页卡死**

这个技能把这些都变成了可自动化检查的规则，而不是靠人记。

---

## 内容

```
m3-design-spec/
├── SKILL.md                    技能主体（196 行）
├── references/
│   ├── tokens.md               72 个设计令牌，亮/暗双值（从代码自动抽取）
│   ├── components.md           298 个类的目录、标记、交互要点
│   └── keyboard.md             键位表、roving tabindex、AI 驱动接口
├── scripts/
│   ├── check_m3_html.py        静态校验器
│   ├── dom_harness.js          在 Node 里真实执行页面脚本
│   ├── audit_keyboard.js       键盘可达性审计
│   └── regression_tests.js     129 项行为回归
└── assets/
    ├── m3-component-library.html   参考实现（约 11,000 行，24 个区块）
    └── full-spec-doc.md            人类可读的规范文档
```

参考实现覆盖：按钮 / FAB / 卡片 / 芯片 / 输入框 / 选择控件 / 导航 / 进度 / 覆盖层 / 日期时间选择器 / 表格 / 手势 / 认证表单 / 键盘优先组件 / 设计规范可视化。

---

## 安装

技能需要放在助手的 `skills` 目录下（本仓库默认 `/skills`），**目录名必须保持 `m3-design-spec`** —— 因为 `SKILL.md` 里的脚本路径是绝对路径 `/skills/m3-design-spec/scripts/...`。

### 一键安装

```bash
git clone https://github.com/frank-bonus18/m3-design-spec.git
cd m3-design-spec
./install.sh
```

`install.sh` 会：

1. 把 `m3-design-spec/` 复制到 `${SKILLS_DIR:-/skills}/`
2. 给脚本加执行权限
3. 跑一遍静态校验、运行时执行和 129 项回归，确认装好了

如果已有旧版本，会先备份到 `${SKILLS_DIR}/.m3-backups/` —— 特意放在点目录里，因为 skills 目录下任何含 `SKILL.md` 的子目录都可能被扫描器当成一个技能，备份到同级会凭空多出一个无效技能。

验证失败时脚本会列出失败项并以非零码退出，但文件已经就位，方便你排查。

### 手动安装

```bash
mkdir -p /skills
cp -a m3-design-spec /skills/
chmod +x /skills/m3-design-spec/scripts/*
```

### 装到别的位置

```bash
SKILLS_DIR=~/my-skills ./install.sh
```

> 装到非 `/skills` 位置时，`SKILL.md` 里的绝对路径需要相应替换。若你的助手支持别的加载路径，改一遍 `SKILL.md` 里的 `/skills/m3-design-spec` 即可。

---

## 验证

装完跑一遍，四项全绿就说明可用：

```bash
cd /skills/m3-design-spec
ASSET=assets/m3-component-library.html

python3 scripts/check_m3_html.py "$ASSET"
node    scripts/dom_harness.js "$ASSET"
node    scripts/audit_keyboard.js "$ASSET"
node    scripts/regression_tests.js "$ASSET"
```

预期输出：

```
result    : PASS — no findings
结果      : ✅ 加载期无异常
✅ 无未预期的不可聚焦点击目标
✅ 全部通过            ← 129 项
```

---

## 四个工具各自管什么

### `check_m3_html.py` — 静态校验

```bash
python3 scripts/check_m3_html.py page.html [--verbose]
```

- HTML 标签闭合、`id` 唯一
- `<script>` 语法（有 `node` 时）
- JS 引用的 id / class 是否存在（运行时动态创建的也算）
- 令牌块外的硬编码颜色（渐变色算装饰，只提示）
- 两套令牌是否完整镜像；`theme-invariant` 标记的常量会被跳过
- 无障碍：`lang`、跳转链接、按钮无障碍名、覆盖层 `role` / `aria-modal`、实时播报区、`prefers-reduced-motion`、`:focus-visible`、emoji 当图标
- 响应式：viewport、是否禁止缩放、是否有 `min-width` 断点

退出码：`0` 干净 / `1` 有问题 / `2` 输入不可用。

### `dom_harness.js` — 运行时执行

```bash
node scripts/dom_harness.js page.html
```

解析 HTML 建最小 DOM，注入浏览器 API，执行页面脚本。抓的是静态分析看不见的东西：加载期异常、同步死循环、交互逻辑写错。

也可以在测试脚本里 require 它，直接驱动页面：

```js
const H = require('/skills/m3-design-spec/scripts/dom_harness.js');
const { doc, fire, loadError } = H;
if (loadError) throw loadError;

doc.querySelector('#themeToggle').click();
fire(doc.querySelector('#dpGrid'), 'keydown', { key: 'ArrowRight', preventDefault() {} });
```

**能力边界**：不是浏览器。Canvas 是桩、布局是常量、观察器是空实现。只用来验证逻辑，不能验证视觉。

### `audit_keyboard.js` — 键盘可达性

```bash
node scripts/audit_keyboard.js page.html [--all]
```

找出「有点击监听但不可聚焦」的元素 —— 被它点名的，纯键盘用户一定够不到。遮罩和禁用按钮算期望例外。

### `regression_tests.js` — 行为回归

```bash
node scripts/regression_tests.js page.html
M3_VERBOSE=1 node scripts/regression_tests.js page.html   # 逐条打印
```

覆盖主题切换、四类覆盖层（含焦点陷阱与 `inert`）、通知堆叠、步进器、日期选择器键盘模型、时间选择器拖动、下拉与多选、表单、登录表单校验、手势、命令面板、组合控件键盘规则、规范可视化、缩放适配、以及**动态重建后键盘支持是否还在**。

可以当模板改选择器，用来测你自己生成的页面。

---

## 关于「禁止缩放」

`check_m3_html.py` 会报 `user-scalable=no` 和 `maximum-scale=1`，因为那会让视力不佳的人无法放大看字（违反 WCAG 1.4.4）。

双指缩小后右侧出现空白，是浏览器行为：布局视口宽度不变，可视视口变宽，多出来的是文档之外。CSS 无法消除。如果确实要处理，参考实现里的做法是用 `visualViewport` 感知缩放比、缩小时按比例放大整页 —— **保留缩放能力**，而不是禁用它。

---

## 环境要求

- **Python 3.8+**（只用于静态校验器，纯标准库）
- **Node.js 18+**（运行时执行、键盘审计、回归测试）
- 无第三方依赖，不需要 `npm install`、不需要 `pip install`

## 兼容性

生成的页面面向现代浏览器：Chrome / Edge / Firefox / Safari。`color-mix()` 处一律带纯色兜底，且**兜底声明写在前面**（顺序反了会让 `color-mix` 永远被覆盖）。

## 许可

[MIT](LICENSE)

## 已知限制

- 运行时 harness 不实现布局，`getBoundingClientRect` 返回常量矩形 —— 滚动跟随、粘性定位、焦点环是否被 `overflow` 裁切，仍需真机验证
- 参考实现的第三方登录图标是手写单色 SVG，形状未逐像素校对；商用前建议换成官方素材
- 日期选择器的初始「今天」写死在参考实现里（2026-10-11），复制使用时记得改
