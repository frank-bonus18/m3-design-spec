# 组件目录

类名、最小标记、交互与键盘要点。命名约定：`m3-` 前缀，`--` 表示变体（`m3-card--filled`），单词表示状态（`.selected` `.open` `.loading`）。

参考实现共 298 个 `m3-*` 类、24 个语义区块。本文件按 M3 家族分组，不逐个罗列所有子元素类。

## 共享基础设施

### 水波纹

```css
.m3-ripple-surface{position:relative;overflow:hidden;isolation:isolate;
  -webkit-tap-highlight-color:transparent}
.m3-ripple{
  position:absolute;border-radius:50%;pointer-events:none;
  background:var(--ripple-color,currentColor);
  transform:scale(0);opacity:var(--ripple-opacity);
  animation:m3-ripple-in 520ms var(--easing-standard) forwards;
}
@keyframes m3-ripple-in{
  0%{transform:scale(0);opacity:var(--ripple-opacity)}
  70%{opacity:calc(var(--ripple-opacity) * .55)}
  100%{transform:scale(1);opacity:0}
}
```

一个 `document` 级 `pointerdown` 委托覆盖全部宿主，动态节点自动生效：

```js
var RIPPLE_SELECTOR = [
  '.m3-btn','.m3-icon-btn','.m3-fab','.m3-chip','.m3-card','.m3-carousel-item',
  '.m3-list-item','.m3-seg-btn','.m3-tab','.m3-menu-item','.m3-nav-item',
  '.m3-rail-item','.m3-drawer-item','.m3-switch-track','.m3-checkbox-box',
  '.m3-radio-circle','.m3-slider-wrap','.dp-cell','.tp-num','.m3-searchbar',
  '.m3-select-trigger','.m3-option','.m3-expansion-head','.m3-rating button',
  '.m3-swatch','.m3-page','.m3-avatar','.m3-number button','.m3-sortable-item',
  '.carousel-dot','.m3-ripple-surface'
].join(',');
```

`--ripple-color` 决定涟漪颜色：实心面上用 `on-*` 色，透明面上用强调色。

### 状态层

```css
.m3-btn::before{
  content:"";position:absolute;inset:0;background:currentColor;opacity:0;
  pointer-events:none;
  transition:opacity var(--duration-short) var(--easing-standard);
}
.m3-btn:hover::before  {opacity:var(--state-hover)}
.m3-btn:active::before {opacity:var(--state-pressed)}
```

状态层与涟漪分开：`::before` 只做 hover/pressed，涟漪是真实 DOM 节点。**注意** `::after` 已被若干组件占用（勾选框的对勾、单选框的圆点、选中色块的勾），扩触控区时不要复用。

### 覆盖层状态机

对话框、全屏对话框、底部抽屉、侧边表单、抽屉共用一块遮罩与一个打开槽位：

```js
function openLayerEl(el){
  closeMenu();
  lastFocused = document.activeElement;
  scrim.classList.add('show');
  el.classList.add('show');
  openLayer = el;
  setBackgroundHidden(true);          // inert + aria-hidden
  focusableIn(el)[0]?.focus();
}
function closeLayer(){
  openLayer.classList.remove('show');
  scrim.classList.remove('show');
  setBackgroundHidden(false);
  lastFocused?.focus();               // 焦点归还
  openLayer = null;
}
```

锚定浮层（菜单、下拉、自动补全）不加遮罩：给浮层加 `.show`，文档级点击关闭外部，支持 `Escape`。

## 按钮 Buttons

| 类 | 面 | 内容 |
|---|---|---|
| `.m3-btn.m3-filled` | `--primary` | `--on-primary` |
| `.m3-btn.m3-tonal` | `--secondary-container` | `--on-secondary-container` |
| `.m3-btn.m3-elevated` | `--surface-container-low` + `--shadow-1` | `--primary` |
| `.m3-btn.m3-outline` | 透明 + 1px `--outline` | `--primary` |
| `.m3-btn.m3-text` | 透明 | `--primary` |

尺寸与形状：`.m3-btn-sm` 32px、默认 40px、`.m3-btn-lg` 48px、`.m3-btn-square`、`.m3-btn-block`。按压 `scale(.98)`。

```html
<button class="m3-btn m3-filled m3-ripple-surface">确定</button>
<button class="m3-btn m3-tonal m3-ripple-surface">
  <svg class="m3-btn-icon" viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
  新建
</button>
```

禁用态：容器 `color-mix(in srgb, var(--on-surface) 12%, transparent)`，文字 38%。`color-mix` 前必须有一行纯色兜底。

图标按钮 `.m3-icon-btn`：`.filled` `.tonal` `.outlined` `.toggled` `.sm` `.lg`。
浮动按钮 `.m3-fab`：`.m3-fab-sm` 40px、默认 56px、`.m3-fab-lg` 96px，语义变体 `.m3-fab-primary/-secondary/-tertiary/-surface`，以及 `.m3-fab-extended`。
拆分按钮 `.m3-split`、带菜单 `.m3-split-menu`。
加载按钮 `.m3-btn.loading` + `.btn-spinner`。

## 卡片 Cards

`.m3-card` 基础；`--elevated`（`--shadow-2`）、`--outlined`（1px 描边无阴影）、`--filled`（`--surface-container-highest`）、`--clickable`、`--horizontal` + `.m3-card-media`。

## 标签 Chips

`.m3-chip` 基础；`.assist` `.input` `.suggestion` `.with-avatar`；选中态填 `--secondary-container` 并前置对勾。
**装饰性标签**（徽标、状态、分类）必须加 `.m3-chip--static`：它只做视觉标记，不参与 roving tabindex，否则键盘用户会多按很多次 Tab。

## 输入框 Text Fields

```html
<div class="m3-field">
  <input type="text" id="name" placeholder=" ">   <!-- 这个空格是必需的 -->
  <label for="name">姓名</label>
  <span class="field-underline"></span>
  <span class="helper">辅助说明</span>
</div>
```

- `.m3-field` 填充式：标签在 `:focus` 或 `:not(:placeholder-shown)` 时上浮。
- `.m3-field--outlined` 轮廓式：标签嵌在描边上并带背景补丁。
- `.m3-field.error` / `.valid` 切换下划线与辅助文案颜色。
- 图标与前缀：`.has-leading` + `.field-leading`、`.has-trailing` + `.field-trailing`、`.has-prefix` + `.field-prefix`、`.field-affix`。
- 密码：`.pw-toggle[data-pw-toggle="id"]`，图标用 `.pw-icon-show` / `.pw-icon-hide` 切换，切换后**保持光标位置**。
- 密码强度：`.m3-pw-strength[data-level="0-4"]`。
- 搜索：`.m3-searchbar`、`.m3-search-view`。

## 选择 Selection

| 组件 | 标记 | 要点 |
|---|---|---|
| 勾选框 | `.m3-checkbox > input + .m3-checkbox-box` | 支持 indeterminate（JS 设属性） |
| 单选框 | `.m3-radio > input + .m3-radio-circle` | 同 `name` 分组 |
| 开关 | `.m3-switch > input + .m3-switch-track > .m3-switch-thumb` | 选中填充 `--primary`，滑块 16→24px |
| 滑块 | `.m3-slider-wrap > input.m3-slider` | 轨道渐变由 `--slider-percent` 驱动 |
| 数值气泡 | `.m3-slider-bubble` | 拖动时跟随 |
| 分段刻度 | `.m3-slider-stops` + `.m3-slider-stepped` | — |
| 双滑块 | `.m3-range > .m3-range-track + 2×input[type=range]` | 两端不可交叉 |
| 星级 | `.m3-rating > button[data-v]` | 悬停预览、点击确认 |
| 评分分布 | `.m3-rating-bars` / `.m3-rating-bar` | 5 档占比 |
| 取色器 | `.m3-swatch[data-color]` | 选中加勾 |
| 树形 | `.m3-tree > .m3-tree-item > .m3-tree-row` + `.m3-tree-children` | `grid-template-rows: 0fr→1fr` 动画 |
| 多选下拉 | `.m3-multiselect > .m3-ms-trigger` + `.m3-ms-menu` | 触发器内渲染 `.m3-ms-tag` |

滑块必须包在 `.m3-slider-wrap` 里，不要把 `overflow:hidden` 加在 input 上，否则滑块拇指被裁。

## 导航 Navigation

| 组件 | 类 | 要点 |
|---|---|---|
| 顶部应用栏 | `.m3-appbar`（`.center` `.medium` `.large` `.surface-tint`） | 粘性，`color-mix` + `backdrop-filter` |
| 底部应用栏 | `.m3-bottom-appbar` | 操作 + FAB 槽 |
| 底部导航 | `.m3-nav-bar > .m3-nav-item > .nav-indicator` | 选中胶囊 |
| 侧边导航 | `.m3-nav-rail > .m3-rail-item > .rail-indicator`（`.expanded` 展开式） | 900px 以下隐藏 |
| 抽屉 | `.m3-drawer > .m3-drawer-item` | `translateX(-105%)` → `0` |
| 标签页 | `.m3-tabs > .m3-tab` + `.tab-indicator`（`.scrollable` `.secondary`） | 指示器跟随宽高与偏移 |
| 分段按钮 | `.m3-segmented > .m3-seg-btn` | 单选 |
| 底部操作栏 | `.m3-bottom-bar` | 勾选后主按钮解禁 |
| 级联菜单 | `.m3-menu-sub` + `.m3-submenu` | 悬停 / `→` 展开，`←` 返回 |

指示器计算要防隐藏区块：

```js
function move(btn){
  if(!ind || !btn) return;
  if(!btn.offsetWidth){ ind.style.width='0px'; return; }  // 区块被筛选隐藏
  ind.style.width = btn.offsetWidth + 'px';
  ind.style.transform = 'translateX(' + btn.offsetLeft + 'px)';
}
```

轮播滚动定位需要滚动容器 `position: relative`，否则 `item.offsetLeft` 参照更远的祖先。

## 进度与反馈

- `.m3-progress-linear > i`（`.indeterminate`）、`.m3-progress-wavy`、`.m3-progress-circular`（`.determinate` 用 `conic-gradient` + `--progress`）、`.m3-progress-segments > i`（`.done` `.active`）。
- `.m3-badge`（`.dot`）+ `.badge-host`。
- `.m3-tooltip`（`.rich`）+ `.has-tooltip`，触摸可点按显示。
- `.m3-banner`、`.m3-alert`（`.info` `.success` `.warning` `.error`）。
- `.m3-snackbar`、`.m3-notif-stack > .m3-notif`。

```js
// 通知上限必须自己维护队列：dismiss 是延迟移除的，
// 直接读 children.length 会同步死循环。
var ACTIVE = [];
while(ACTIVE.length >= MAX) dismiss(ACTIVE[0]);
```

## 覆盖层 Overlays

| 类 | 动作 |
|---|---|
| `.m3-scrim` | `--duration-medium` 淡入 |
| `.m3-dialog` | `scale(.85)` → `1`，`translate(-50%,-50%)` 居中 |
| `.m3-dialog.fullscreen` | 全屏，带应用栏与可滚动内容 |
| `.m3-bottom-sheet` | `translateY(105%)` → `0`；`data-height="half\|full"` |
| `.m3-side-sheet` | 右侧滑入，`translateX(105%)` → `0` |
| `.m3-snackbar` | 底部滑入，约 3 秒自动消失，可带动作 |
| `.m3-cmdk-scrim > .m3-cmdk` | 命令面板 |
| `.m3-keys-scrim > .m3-keys` | 快捷键帮助 |
| `.m3-tour` + `.m3-tour-ring` | 引导气泡 + 高亮环 |

## 数据展示

- 表格：`.m3-table-wrap > .m3-table`，表头可排序并同步 `aria-sort`。
- 数据网格：`.m3-datagrid`（`.sticky-col` 首列吸附），单元格行内编辑用 `.dg-input`。
- 分页：`.m3-pagination > .m3-page`。
- 头像：`.m3-avatar`（`.more` `.lg`）+ `.m3-avatar-group`。
- 收件箱：`.m3-inbox-item`（`.unread`）+ `.m3-inbox-star`。
- 统计卡：`.m3-stat-card` + `.m3-stat-value` / `.m3-stat-delta` + `.m3-sparkline`。
- 热力图：`.m3-heatmap-grid > .m3-heatmap-cell[data-lv="0-4"]`。
- 对话气泡：`.m3-chat-row`（`.out` 为发出）+ `.m3-chat-bubble`（`.typing`）。
- 时间线：`.m3-timeline > .m3-timeline-item`（`.done` `.current`）。
- 价目卡：`.m3-price-card`（`.featured`）。

## 表单与认证

- 下拉：`.m3-select > .m3-select-trigger` + `.m3-select-menu > .m3-option`。
- 自动补全：`.m3-combobox > .m3-combobox-field` + `.m3-combobox-list`，高亮用 `<mark>`。
- 标签输入：`.m3-tag-field > .m3-tag`。
- 步进器：`.m3-number`，长按连续加减。
- 验证码：`.m3-otp > input`，自动跳格、整段粘贴分发。
- 认证卡：`.m3-auth-card` + `.m3-auth-head` / `.m3-auth-logo` / `.m3-auth-title` / `.m3-auth-body` / `.m3-auth-foot`。
- 错误汇总：`.m3-auth-error`。
- 第三方登录：`.m3-social-btn`（`.filled`），图标手写单色 SVG。
- 带文字分割线：`.m3-divider-text`。

## 手势

- 滑动删除：`.m3-swipe-item > .m3-swipe-bg` + `.m3-swipe-content`，超过 80px 触发。
- 拖拽排序：`.m3-sortable > .m3-sortable-item` + `.drag-handle`。
- 速度拨号：`.m3-speed-dial > .m3-speed-actions`。
- 下拉刷新：`.m3-pull > .m3-pull-indicator` + `.m3-pull-content`，阈值 60px。
- 引导：`.m3-tour`，`window.startTour()` / `closeTour()`。

滑动删除必须先锁轴，否则会抢走纵向滚动：

```js
if(locked === null){
  if(Math.abs(mx) < 6 && Math.abs(my) < 6) return;
  locked = Math.abs(mx) > Math.abs(my) ? 'x' : 'y';
}
if(locked !== 'x') return;
```

## 规范可视化

- 字阶：`.m3-type-row` + `.ts-display/headline/title/body/label`。
- 色板：`.m3-swatch-cell > .m3-swatch-chip` + `.m3-swatch-badge`。
- 对比度：`.m3-contrast` + `.m3-ratio` / `.m3-pass`。
- 海拔：`.m3-elevation-row > .m3-elevation-card`。
- 动效曲线：`.m3-curve` + `.m3-curve-ball`。
- 标尺：`.m3-ruler-row` / `.m3-radius-sample`。
- 快捷键录制：`.m3-keycap`。
- 搜索筛选：`.m3-filter-bar > .m3-filter-item`。

## 声明式钩子

优先用这些 data 属性，不写新 JS：

| 属性 | 效果 |
|---|---|
| `data-snack="text"` | 点击弹 Snackbar |
| `data-dialog="id"` | 打开该对话框 |
| `data-sheet-open="half\|full"` | 打开底部抽屉并指定档位 |
| `data-close` | 关闭当前覆盖层 |
| `data-menu="id"` | 打开该菜单 |
| `data-goto="section-id"` | 平滑滚动到区块 |
| `data-dismiss-banner` | 移除所属横幅 |
| `data-tabs` / `data-panel="n"` | 标签页组与面板 |
| `data-seg-group` / `data-navbar` | 单选组 |
| `data-tool="name"` | 工具栏切换按钮 |
| `data-section` / `data-cat` | 供筛选与滚动高亮索引 |
| `data-step` / `data-min` / `data-max` | 步进器方向与边界 |
| `data-key` / `data-type` | 表格排序字段 |
| `data-color` | 色板值 |
| `data-ease` | 动效曲线预设 |
| `data-pw-toggle="inputId"` | 密码显隐 |
| `data-vstep="next\|prev\|reset"` | 竖向步骤操作 |

## 无障碍默认值

- 用原生 `<button>` / `<input>`，Tab 顺序与 Enter/Space 天然可用。
- `:focus-visible{outline:3px solid var(--primary);outline-offset:2px}`。
- 覆盖层：`role="dialog"` 或 `alertdialog` + `aria-modal="true"`。
- Snackbar：`role="status" aria-live="polite"`。
- 开关类控件保持 `aria-expanded` / `aria-checked` / `aria-pressed` 与视觉同步。
- `@media (prefers-reduced-motion: reduce)` 收敛动效。
