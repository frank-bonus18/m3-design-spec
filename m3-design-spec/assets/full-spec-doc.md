# Material 3 组件库 · 设计规范

> 基于 Android 13 Material You（Material 3）的完整组件库，种子色 **商务蓝 `#0058A8`**，配色方案 **Tonal Spot**，支持亮色 / 暗色双主题与全局按压水波纹。

| 项目 | 值 |
|---|---|
| 主文件 | `设计规范.html` |
| 体积 | 515,645 字节（约 504 KB） |
| 行数 | 10,700+ 行 |
| 依赖 | **零依赖**（纯 HTML + CSS + 原生 JS，无框架 / 无 CDN） |
| 语义区块 | 23 处 |
| 颜色令牌 | 72 个 |
| 组件类 | 280+ 个 `m3-*` 类 |
| 水波纹宿主 | 340+ 处 |
| ARIA 标注 | 350+ 处 `aria-*` 属性 |
| 响应式 | 9 个媒体查询，宽屏分档 900 / 1200 / 1600 / 2100px |
| 缩放适配 | `visualViewport` 感知缩放比例，缩小时按比例放大铺满（不禁止缩放） |
| 图标 | 全部手写内联 SVG，**无 emoji 充当功能图标** |
| 无障碍 | **生产级**：焦点陷阱、背景 `inert`、roving tabindex、实时播报、48dp 触控目标 |
| 键盘 | **全站纯键盘可用**：14 条全局快捷键、`g` 前缀跳转、命令面板、机器可读注册表 |
| 校验 | 静态检查 + 运行时执行 + 键盘审计 + 125 项行为回归，见技能 `scripts/` |

---

## 目录

- [1. 快速开始](#1-快速开始)
- [2. 主题机制](#2-主题机制)
- [3. 设计令牌](#3-设计令牌)
- [4. 规范常量](#4-规范常量)
- [5. 组件总览](#5-组件总览)
- [6. 组件用法](#6-组件用法)
- [7. 水波纹机制](#7-水波纹机制)
- [8. 弹窗与覆盖层](#8-弹窗与覆盖层)
- [9. 声明式 API（data-\*）](#9-声明式-api-data-)
- [10. 无障碍](#10-无障碍)
- [11. 响应式](#11-响应式)
- [12. 扩展指南](#12-扩展指南)

---

## 1. 快速开始

单文件，直接双击用浏览器打开即可，无需构建、无需服务器。

```
设计规范/
└── 设计规范.html      ← 全部内容（样式 + 标记 + 脚本）
```

页面骨架：

```html
<body>
  <nav class="m3-nav-rail">…</nav>      <!-- 宽屏左侧导航栏 -->
  <div class="lib">
    <div class="container">…</div>       <!-- 组件展示列，max-width 440px -->
  </div>
  <div class="fab-dock">…</div>          <!-- 右下角固定 FAB -->
  <div class="m3-scrim" id="scrim"></div><!-- 共享遮罩 -->
  <!-- 对话框 / 抽屉 / Snackbar -->
</body>
```

`.container` 为竖向 flex 列，`gap: 20px`，最大宽度 440px 居中；`.lib` 负责 Rail 与内容列的横向排布（最大 1100px 居中）。

---

## 2. 主题机制

由页面上的 `#themeToggle` 复选框控制（抽屉内的 `#themeToggle2` 与之双向同步）：

```js
// 勾选 → 写入 data-theme="dark"
document.documentElement.setAttribute('data-theme', 'dark');
// 取消 → 移除属性，回退到 :root 亮色
document.documentElement.removeAttribute('data-theme');
```

切换时同步更新：

- `#themeState` 文案（`开` / `关`）
- `<meta name="theme-color">`（`#111418` / `#0058A8`）

> **注意**：本库**不使用 localStorage / sessionStorage**，不记忆主题偏好，**刷新页面即重置为亮色**。这是有意设计——便于设计评审时每次都从基准亮色开始。

暗色模式同时设置 `color-scheme`，使滚动条、`<input type="search">` 清除按钮等原生控件跟随变暗：

```css
:root            { color-scheme: light; }
[data-theme="dark"] { color-scheme: dark; }
```

---

## 3. 设计令牌

全部令牌定义在 `:root`（亮色）与 `[data-theme="dark"]`（暗色）两组中，暗色为完整对位映射。**组件样式一律引用令牌，无硬编码颜色**，因此换肤只需改令牌。

### 3.1 主色组 Primary

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--primary` | `#0058A8` | `#A3C8FF` |
| `--on-primary` | `#FFFFFF` | `#002F59` |
| `--primary-container` | `#D3E3FF` | `#00437F` |
| `--on-primary-container` | `#001A34` | `#D3E3FF` |
| `--primary-fixed` | `#D3E3FF` | `#D3E3FF` |
| `--primary-fixed-dim` | `#A3C8FF` | `#A3C8FF` |
| `--on-primary-fixed` | `#001A34` | `#001A34` |
| `--on-primary-fixed-variant` | `#00458A` | `#00458A` |

### 3.2 次要色组 Secondary

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--secondary` | `#425F80` | `#BBC7E0` |
| `--on-secondary` | `#FFFFFF` | `#0A3150` |
| `--secondary-container` | `#D7E3FB` | `#2A4768` |
| `--on-secondary-container` | `#001C36` | `#D7E3FB` |

### 3.3 第三色组 Tertiary

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--tertiary` | `#59588B` | `#C5C1FF` |
| `--on-tertiary` | `#FFFFFF` | `#2C2B5C` |
| `--tertiary-container` | `#E2E0FF` | `#424173` |
| `--on-tertiary-container` | `#161544` | `#E2E0FF` |

### 3.4 错误色组 Error

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--error` | `#B3261E` | `#F2B8B5` |
| `--on-error` | `#FFFFFF` | `#601410` |
| `--error-container` | `#F9DEDC` | `#8C1D18` |
| `--on-error-container` | `#410E0B` | `#F9DEDC` |

### 3.5 背景与表面层级 Surface

M3 用 5 级 surface container 表达海拔层级，数字越高越靠近用户。

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--background` | `#FAF9FD` | `#111418` |
| `--on-background` | `#191C20` | `#E0E2E8` |
| `--surface` | `#FAF9FD` | `#111418` |
| `--on-surface` | `#191C20` | `#E0E2E8` |
| `--surface-variant` | `#DAE2ED` | `#404854` |
| `--on-surface-variant` | `#42474E` | `#C2C7CF` |
| `--surface-container-lowest` | `#FFFFFF` | `#0C0E12` |
| `--surface-container-low` | `#F4F3F8` | `#191C20` |
| `--surface-container` | `#EEEDF2` | `#1D2024` |
| `--surface-container-high` | `#E8E7EC` | `#282A2F` |
| `--surface-container-highest` | `#E2E2E6` | `#33353A` |
| `--surface-dim` | `#DAD9DE` | `#111418` |
| `--surface-bright` | `#FAF9FD` | `#37393E` |
| `--surface-tint` | `#0058A8` | `#A3C8FF` |

### 3.6 描边、反色与遮罩

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--outline` | `#707884` | `#8A929E` |
| `--outline-variant` | `#C2C7CF` | `#42474E` |
| `--inverse-surface` | `#2E3135` | `#E0E2E8` |
| `--inverse-on-surface` | `#F0F0F6` | `#2E3135` |
| `--inverse-primary` | `#A3C8FF` | `#0058A8` |
| `--scrim` | `#000000` | `#000000` |
| `--scrim-color` | `rgba(0,0,0,.32)` | `rgba(0,0,0,.55)` |

### 3.7 组件专属常量（不随主题变化）

以下两个颜色值不属于语义调色板，亮暗两套主题共用。它们**只声明在 `:root`**，并在行尾注释里带有 `theme-invariant` 标记，用于向校验脚本说明这是有意为之、而非漏写暗色对应值。

| 变量 | 值 | 用途 |
|---|---|---|
| `--star` | `#F5B301` | 星级评分选中色 |
| `--on-media` | `#FFFFFF` | 叠加在饱和色块上的前景（如取色器选中勾） |

```css
:root{
  --star:#F5B301;      /* theme-invariant 星级评分金色 */
  --on-media:#FFFFFF;  /* theme-invariant 饱和色块上的前景 */
}
```

> 标记只能用于**确实与主题无关**的常量。若某颜色本应跟随主题，必须在两套令牌块中都定义，不要用标记掩盖遗漏。

---

## 4. 规范常量

### 4.1 圆角

| 变量 | 值 | 典型用途 |
|---|---|---|
| `--radius-xs` | `8px` | Chip、菜单、Snackbar、下拉、输入框 |
| `--radius-sm` | `12px` | 列表、扩展面板、小 FAB |
| `--radius-md` | `16px` | 卡片、FAB、分段按钮、导航项 |
| `--radius-lg` | `28px` | 大 FAB、对话框、底部抽屉 |
| `--radius-full` | `999px` | 按钮、开关、徽标、头像 |

### 4.2 水波纹与状态层

| 变量 | 值 | 说明 |
|---|---|---|
| `--ripple-opacity` | `.24` | 水波纹峰值透明度，**可在页面「滑块」区实时调节** |
| `--state-hover` | `.08` | 悬停状态层叠加透明度 |
| `--state-focus` | `.12` | 聚焦状态层 |
| `--state-pressed` | `.16` | 按压状态层 |
| `--disabled-opacity` | `.38` | 禁用前景透明度 |
| `--disabled-container` | `.12` | 禁用容器透明度 |

### 4.3 海拔阴影

| 变量 | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--shadow-1` | `.30 / .15` | `.55 / .35` | 卡片、搜索栏、Elevated 按钮 |
| `--shadow-2` | `.30 / .15` | `.55 / .35` | FAB、菜单、工具栏 |
| `--shadow-3` | `.15 / .30` | `.40 / .55` | 对话框、底部抽屉 |
| `--shadow-4` | `.15 / .30` | `.40 / .55` | 高位悬浮 |
| `--shadow-5` | `.15 / .30` | `.40 / .55` | 最高海拔 |

> 暗色模式下阴影整体加重，因为深色背景中低对比阴影几乎不可见。

### 4.4 动效

| 变量 | 值 |
|---|---|
| `--duration-short` | `150ms` |
| `--duration-medium` | `250ms` |
| `--duration-long` | `400ms` |
| `--easing-standard` | `cubic-bezier(.2, 0, 0, 1)` |
| `--easing-emphasized` | `cubic-bezier(.2, 0, 0, 1)` |

### 4.5 字体与布局

| 变量 | 值 |
|---|---|
| `--font` | `Roboto, "Roboto Flex", system-ui, -apple-system, "Segoe UI", "Noto Sans SC", "PingFang SC", sans-serif` |
| `--nav-rail-w` | `88px` |

**全局过渡**：`*` 选择器统一声明 `background-color / color / border-color / box-shadow / fill` 的 250ms 过渡，因此亮暗切换时颜色平滑变化，而非瞬间跳变。

---

## 5. 组件总览

### 5.1 操作 Actions

| 组件 | 类名 | 交互 |
|---|---|---|
| 五种按钮 | `.m3-btn` + `.m3-filled` / `.m3-tonal` / `.m3-elevated` / `.m3-outline` / `.m3-text` | 水波纹、状态层、按压缩放 `0.98` |
| 按钮尺寸 | `.m3-btn-sm` / `.m3-btn-lg` / `.m3-btn-square` / `.m3-btn-block` | 32 / 40 / 48px 高度 |
| 图标按钮 | `.m3-icon-btn` + `.filled` / `.tonal` / `.outlined` / `.toggled` / `.sm` / `.lg` | 圆形水波纹，可切换态 |
| FAB | `.m3-fab` + `.m3-fab-sm` / `.m3-fab-lg` | 悬停放大 `1.03`、按压 `0.96` |
| FAB 语义变体 | `.m3-fab-primary` / `-secondary` / `-tertiary` / `-surface` | 四种配色 |
| 扩展 FAB | `.m3-fab-extended` | 图标 + 文字 |
| 分段按钮 | `.m3-segmented` > `.m3-seg-btn` | 单选，选中填充 secondary-container |
| 拆分按钮 | `.m3-split` | 主操作 + 下拉箭头 |
| 加载按钮 | `.m3-btn.loading` + `.btn-spinner` | 点击后转圈，1.6s 还原 |

### 5.2 通讯 Communication

| 组件 | 类名 | 交互 |
|---|---|---|
| 线性进度 | `.m3-progress-linear` > `i` | 确定进度，宽度过渡 400ms |
| 不确定进度 | `.m3-progress-linear.indeterminate` | 无限循环滑动动画 |
| 环形进度 | `.m3-progress-circular`（`.lg`） | 旋转动画 |
| 确定进度环 | `.m3-progress-circular.determinate` | `conic-gradient` + `--progress` 变量 |
| 徽标 | `.m3-badge`（`.dot`）+ `.badge-host` | 数字 / `99+` / 圆点角标 |
| 工具提示 | `.m3-tooltip` + `.has-tooltip` | hover 淡入，触摸可点按切换 |
| 横幅 | `.m3-banner` | 可关闭，淡出 + 上移 |

### 5.3 容器 Containment

| 组件 | 类名 | 说明 |
|---|---|---|
| 卡片 | `.m3-card` + `--elevated` / `--outlined` / `--filled` / `--clickable` / `--horizontal` | 4 种变体 + 可点击 + 横向布局 |
| 卡片媒体区 | `.m3-card-media` | 渐变占位图 |
| 轮播 | `.m3-carousel` > `.m3-carousel-item` | 滚动吸附 + 指示点 + 前后按钮 |
| 分割线 | `.m3-divider` + `--inset` / `--thick` | 标准 / 内缩 / 加粗分组 |
| 列表 | `.m3-list` > `.m3-list-item` | 头像、标题、副标题、尾部 |

### 5.4 导航 Navigation

| 组件 | 类名 | 说明 |
|---|---|---|
| 顶部应用栏 | `.m3-appbar` + `.center` / `.medium` / `.surface-tint` | 小 / 居中 / 中等标题 |
| 底部应用栏 | `.m3-bottom-appbar` | 操作 + FAB |
| 底部导航栏 | `.m3-nav-bar` > `.m3-nav-item` | 选中项胶囊指示器 |
| 侧边导航栏 | `.m3-nav-rail` > `.m3-rail-item` | 宽屏常驻，滚动联动高亮 |
| 导航抽屉 | `.m3-drawer` > `.m3-drawer-item` | 从左滑入，遮罩可关 |
| 标签页 | `.m3-tabs` > `.m3-tab` + `.tab-indicator` | 主 / 次级双样式，指示器滑动 |

### 5.5 选择 Selection

| 组件 | 类名 | 交互 |
|---|---|---|
| 勾选框 | `.m3-checkbox` > `.m3-checkbox-box` | 含 **indeterminate 半选态** |
| 单选框 | `.m3-radio` > `.m3-radio-circle` | 圆形缩放动画 |
| 开关 | `.m3-switch` > `.m3-switch-track` / `.m3-switch-thumb` | 滑块尺寸 + 位移动画 |
| 单滑块 | `.m3-slider` + `.m3-slider-wrap` | 渐变轨道跟随百分比 |
| 双滑块区间 | `.m3-range` > `.m3-range-track` + 2×`input[type=range]` | 互不越界，最小间隔可配 |
| 标签 | `.m3-chip` + `.assist` / `.input` / `.suggestion` / 选中态 | 筛选多选、可关闭 |
| 菜单 | `.m3-menu` > `.m3-menu-item`（`.danger`）+ `.m3-menu-wrap` | 左右锚点、分组标签 |
| 星级评分 | `.m3-rating` > `button` | 悬停预览 + 点击确认 + 弹跳 |
| 日期选择器 | `.m3-datepicker` | 月历渲染、翻页、今天、选中 |
| 时间选择器 | `.m3-timepicker` | 表盘指针 + 时/分 + AM/PM |

### 5.6 输入 Text & Forms

| 组件 | 类名 | 交互 |
|---|---|---|
| 填充式输入框 | `.m3-field` | 浮动标签 + 2px 聚焦下划线 |
| 轮廓式输入框 | `.m3-field--outlined` | 标签嵌在描边上 |
| 多行文本域 | `.m3-field` + `textarea` | 可拉伸 |
| 错误 / 成功态 | `.m3-field.error` / `.m3-field.valid` | 语义色 + 辅助文案 |
| 搜索栏 | `.m3-searchbar` | 圆角胶囊 + 图标 |
| 搜索视图 | `.m3-search-view` | 返回 + 清空 + 历史记录 |
| 下拉选择 | `.m3-select` > `.m3-select-trigger` + `.m3-select-menu` > `.m3-option` | 点击展开、单选打勾、外部点击收起 |
| 自动补全 | `.m3-combobox` > `.m3-combobox-field` + `.m3-combobox-list` | 实时过滤 + 关键词高亮 |
| 标签输入 | `.m3-tag-field` > `.m3-tag` | 回车 / 逗号添加，✕ 或退格删除 |
| 数字步进器 | `.m3-number` | ± 按钮，长按连续加减，上下限禁用 |
| 验证码 | `.m3-otp` > `input` | 自动跳格、粘贴分发、错误抖动 |
| 实时校验 | `.m3-field` + `.field-row` / `.counter` / `.field-clear` | 字数计数 + 清除按钮 |

### 5.7 展示 Display

| 组件 | 类名 | 交互 |
|---|---|---|
| 骨架屏 | `.m3-skeleton`（`.title` / `.short` / `.avatar`） | 微光扫过动画 |
| 折叠面板 | `.m3-expansion` > `.m3-expansion-head` / `-body` | `grid-template-rows` 平滑展开 |
| 时间线 | `.m3-timeline` > `.m3-timeline-item`（`.done` / `.current`） | 三态节点 |
| 步骤条 | `.m3-steps` > `.m3-step` + `.m3-steps-body` | 上一步/下一步、可跳步 |
| 空状态 | `.m3-empty`（`.error`） | 空 / 错误两套配色 |

### 5.8 数据 Data

| 组件 | 类名 | 交互 |
|---|---|---|
| 数据表格 | `.m3-table-wrap` > `.m3-table` | 点击表头升/降序，中文 localeCompare |
| 分页 | `.m3-pagination` > `.m3-page` | 页码 + 前后翻页，边界禁用 |
| 头像组 | `.m3-avatar-group` > `.m3-avatar`（`.more` / `.lg`） | 重叠排布、`+N` 展开 |

### 5.9 手势 Gesture

| 组件 | 类名 | 交互 |
|---|---|---|
| 滑动删除 | `.m3-swipe-item` > `.m3-swipe-bg` / `.m3-swipe-content` | 指针拖拽，超 80px 删除，高度塌陷 |
| 拖拽排序 | `.m3-sortable` > `.m3-sortable-item` + `.drag-handle` | 实时换位，序号重排 |
| 速度拨号 | `.m3-speed-dial` > `.m3-speed-actions` / `.m3-speed-item` | FAB 旋转 45°，子项错峰入场 |
| 浮动工具栏 | `.m3-toolbar` | 多选切换，状态汇总 |

### 5.10 弹窗 Overlays

| 组件 | 类名 | 说明 |
|---|---|---|
| 遮罩 | `.m3-scrim` | 共享遮罩，点击关闭 |
| 对话框 | `.m3-dialog` | 缩放淡入 |
| 全屏对话框 | `.m3-dialog.fullscreen` | 应用栏 + 可滚动内容 |
| 底部抽屉 | `.m3-bottom-sheet` + `data-height` | 自动 / `half` / `full` 三档 |
| Snackbar | `.m3-snackbar` | 底部滑入，3 秒自动消失，可带动作 |

---

### 5.11 扩展能力 Extended

| 组件 | 类名 | 交互 |
|---|---|---|
| 上下文操作条 | `.m3-cab` > `.m3-cab-count` | 勾选列表项后滑入，显示已选数与批量操作（分享 / 归档 / 删除） |
| 多选列表项 | `.m3-list-item.selected` + `.li-select` | 点击或回车切换选中，同步 `aria-selected` |
| 下拉刷新 | `.m3-pull` > `.m3-pull-indicator` / `.m3-pull-content` | 指针下拉带阻力，超 60px 进入 armed，松手触发刷新 |
| 粘性分组标题 | `.m3-sticky-header` | `position: sticky` + 半透明模糊，滚动时钉在顶部 |
| 可复制字段 | `.m3-copy-field` > `code` / `.copy-state` | 点击复制，剪贴板 API 失败时回退 `execCommand`，2 秒反馈 |
| 就地编辑 | `.m3-inline-edit` > `.m3-inline-edit-value` | 点击文字变输入框，回车或失焦保存，`Esc` 取消 |
| 评分分布 | `.m3-rating-summary` / `.m3-rating-bars` / `.m3-rating-bar` | 5 档占比条 + 加权均分，宽度带过渡动画 |
| 通知堆叠 | `.m3-notif-stack` > `.m3-notif` | 顶部堆叠，最多同时 3 条，超出挤掉最早一条，自动消失 |

---

### 5.12 进阶组件 Advanced

| 组件 | 类名 | 交互 |
|---|---|---|
| 文件拖放区 | `.m3-dropzone` > `.dz-icon` / `.dz-title` | 拖入高亮（`dragenter/over` 加 `.over`），支持点击选择、键盘回车、多选 |
| 文件条目 | `.m3-file-chip` > `.fc-icon` / `.fc-name` / `.fc-size` | 显示文件名与自动换算的大小，可单独移除 |
| 竖向步骤条 | `.m3-vsteps` > `.m3-vstep`（`.done` / `.active`） | 三态节点 + 连接线，当前步显示操作按钮 |
| 树形控件 | `.m3-tree` > `.m3-tree-item` > `.m3-tree-row` / `.m3-tree-children` | 点击展开收起，`grid-template-rows` 动画，↑↓ 导航、←→ 折叠展开 |
| 多选下拉 | `.m3-multiselect` > `.m3-ms-trigger` / `.m3-ms-menu` | 触发器内渲染已选标签，可单个移除，`aria-multiselectable` |
| 引用块 | `.m3-quote`（`.tonal`） | 左侧主色竖条，支持 `footer` 署名 |
| 代码块 | `.m3-code` > `.m3-code-head` / `pre` | 语言标签 + 复制按钮，内置 `.tk-key/str/num/com` 语法着色 |
| 价目卡 | `.m3-price-card`（`.featured`） | 推荐卡加粗描边 + 右上角徽标，含功能对比列表（`.off` 表示未包含） |
| 快捷键表 | `.m3-shortcuts` > `.m3-shortcut-row` / `.m3-kbd` | 分组标题 + 按键胶囊（带下边缘模拟键帽） |
| 引导浮层 | `.m3-tour` + `.m3-tour-ring` | 高亮环跟随目标元素尺寸与位置，气泡自动避让视口，支持 Esc / → 导航 |

---

### 5.13 高级组件 Advanced Plus

| 组件 | 类名 | 交互 |
|---|---|---|
| 语义提示条 | `.m3-alert` + `.info` / `.success` / `.warning` / `.error` | 左侧 4px 语义色边条，可关闭（淡出 + 右移） |
| 统计卡 | `.m3-stat-card` + `.m3-stat-value` / `.m3-stat-delta` | 数值 + 涨跌胶囊（`up`/`down`/`flat`）+ 迷你折线 |
| 迷你折线 | `.m3-sparkline` > `.sp-line` / `.sp-area` / `.sp-dot` | SVG 生成，按数据自动归一化，含面积填充与末点圆点 |
| 对话气泡 | `.m3-chat-row`（`.out` 为发出）+ `.m3-chat-bubble` | 收发两侧自动换色换圆角，含时间与已读勾，`.typing` 三点动画 |
| 收件箱 | `.m3-inbox-item`（`.unread`）+ `.m3-inbox-star` | 未读左侧圆点 + 加粗标题，点击标记已读，星标可切换 |
| 活跃度热力图 | `.m3-heatmap-grid` > `.m3-heatmap-cell[data-lv]` | 5 级色阶（0–4），`title` 提示，自动统计总数 |
| 分段进度 | `.m3-progress-segments` > `i`（`.done` / `.active`） | 分段显示进度，当前段脉冲动画，支持长按自动推进 |
| 数据网格 | `.m3-datagrid`（`.sticky-col`） | 表头吸顶 + 首列吸附、行选中、全选半选、单元格行内编辑 |
| 命令面板 | `.m3-cmdk-scrim` > `.m3-cmdk` | `Ctrl/⌘+K` 唤起，分组过滤、关键词高亮、↑↓/Home/End 导航、`aria-activedescendant` |

---

### 5.14 键盘优先 Keyboard First

| 组件 | 类名 | 交互 |
|---|---|---|
| 快捷键帮助浮层 | `.m3-keys-scrim` > `.m3-keys` | 按 `?` 呼出，从统一注册表渲染，Tab 循环、Esc 关闭 |
| 级联菜单 | `.m3-menu-sub` + `.m3-submenu` | 悬停展开；键盘 `→` 进入子菜单、`←` 返回、Esc 全关 |
| 拆分按钮带菜单 | `.m3-split-menu` > `.m3-split` + `.m3-menu` | 主操作 + 下拉，`↓` 打开并聚焦首项 |
| 底部操作栏 | `.m3-bottom-bar` | 勾选后主按钮解禁，标题实时跟随 |
| 前缀跳转列表 | `.m3-typeahead` > `.m3-list-item` | 输入字母跳到对应开头项并高亮闪烁，1.5 秒缓冲 |

**已补全键盘支持的既有组件**

| 组件 | 补了什么 |
|---|---|
| 日期选择器 | roving tabindex、←→↑↓ 移动、Home/End 到周首尾、PageUp/PageDown 翻月、Enter 选定、每格 `aria-label` |
| 折叠面板 | ↑↓ 在标题间移动，Home/End 到首尾 |
| 筛选 Chip | roving tabindex + 方向键，**用事件委托**所以动态新增也生效 |
| 竖向步骤条 | roving tabindex + ↑↓ 导航 + Enter 执行当前步操作 |
| 多选下拉 | Enter/Space/↓ 打开，↑↓/Home/End 选项间移动，Space 切换，Esc 返回触发器 |
| 可点击头像、时段、轮播项、Tooltip 宿主 | 补 `tabindex` / `role` / Enter·Space 激活 |

### 5.15 供程序驱动的接口（AI 可用）

页面暴露一个**机器可读的快捷键注册表**，AI 或自动化脚本可以直接枚举并调用，无需模拟按键坐标：

```js
window.m3Keys.commands            // [{ id, group, label, keys, run }]
window.m3Keys.format('cmdk')      // → 'Ctrl + K'
window.m3Keys.invoke('theme')     // 执行并返回是否成功
```

其他可用接口：

| 接口 | 作用 |
|---|---|
| `window.m3Keys.open()` / `.close()` | 开关快捷键帮助 |
| `window.openCmdk()` / `closeCmdk()` / `cmdkIsOpen()` | 命令面板 |
| `window.startTour()` / `closeTour()` | 引导浮层 |
| `window.applyTheme(dark)` / `toggleTheme()` | 主题 |
| `window.notify({type,title,text})` | 通知堆叠 |
| `window.announce(msg)` | 读屏播报 |
| `window.m3Enhance(root)` | 对动态插入的节点重新应用无障碍增强 |
| `window.closeLayer()` / `closeAllMenus()` | 关闭浮层 / 菜单 |

**全局按键**：`?` 帮助 · `Ctrl/⌘+K` 命令面板 · `g` 后接字母跳转（`g g` 顶部、`g a` 操作、`g n` 导航、`g f` 表单、`g d` 数据、`g u` 认证、`g k` 键盘、`g t` 主题、`g 1` 引导、`g 2` 通知、`g c` 主内容）· `Esc` 关闭一切。焦点在输入框内时全局按键不劫持。

---

### 5.16 设计规范可视化

| 组件 | 类名 | 用途 |
|---|---|---|
| 字阶 | `.m3-type-row` + `.ts-display/headline/title/body/label` | 展示 M3 五级字号的字号 / 行高 / 字距 |
| 色板网格 | `.m3-swatch-cell` > `.m3-swatch-chip` / `.m3-swatch-badge` | 12 组语义色配对，角标显示 AAA / AA / AA-L 对比度等级，点击复制令牌 |
| 对比度检查器 | `.m3-contrast` > `.m3-preview` / `.m3-ratio` / `.m3-pass` | 双取色器实时计算 WCAG 对比度，分别判定 AA 正文 / AAA 正文 / AA 大字 |
| 海拔对比 | `.m3-elevation-row` > `.m3-elevation-card` | 五级阴影并排展示 |
| 动效曲线 | `.m3-curve` > `.cv-path` + `.m3-curve-ball` | 由 `cubic-bezier` 实时生成 SVG 曲线并驱动小球演示 |
| 间距标尺 | `.m3-ruler-row` > `.m3-ruler-bar` | 4–48px 九档间距可视化 |
| 圆角标尺 | `.m3-radius-sample` | 五个半径令牌的实物对比 |
| 快捷键录制 | `.m3-keycap` | 捕获按键并规范化为 `Ctrl + Shift + K` 形式，修饰键单独按下不完成录制 |
| 搜索筛选 | `.m3-filter-bar` > `.m3-filter-item` | 关键词 + 分类双重过滤，实时计数，无结果空态，↑↓ 导航 |

**可复用的计算接口**

```js
window.m3Contrast.ratio('#000000', '#FFFFFF')   // → 21
window.m3Contrast.luminance('#0058A8')          // → 相对亮度 0..1
window.m3Contrast.grade(4.6)                    // → { aa:true, aaa:false, large:true }
```

**缩放自适应接口**

```js
window.m3Zoom.state()    // { supported, scale, visualWidth, layoutWidth, compensating, factor }
window.m3Zoom.refresh()  // 重新测量并应用
```

`supported` 在无 `visualViewport` 的环境为 `false`，API 依然存在，调用方无需分支判断。

---

## 6. 组件用法

### 6.1 按钮

```html
<!-- 填充主按钮 -->
<button class="m3-btn m3-filled m3-ripple-surface">确定</button>

<!-- 带图标 -->
<button class="m3-btn m3-tonal m3-ripple-surface">
  <svg class="m3-btn-icon" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
  </svg>
  新建
</button>

<!-- 禁用 -->
<button class="m3-btn m3-outline m3-ripple-surface" disabled>不可用</button>
```

### 6.2 输入框

```html
<div class="m3-field">
  <input type="text" id="name" placeholder=" ">
  <label for="name">姓名</label>
  <span class="field-underline"></span>
  <span class="helper">辅助说明文字</span>
</div>
```

> `placeholder=" "` 是**必需**的：浮动标签依赖 `:not(:placeholder-shown)` 判断，空 placeholder 才能让标签在无内容时保持浮动位置。

### 6.3 开关

```html
<label class="m3-switch">
  <input type="checkbox" id="sw">
  <span class="m3-switch-track m3-ripple-surface">
    <span class="m3-switch-thumb"></span>
  </span>
  <span>暗色模式</span>
</label>
```

### 6.4 下拉选择

```html
<div class="m3-select" id="mySelect">
  <button class="m3-select-trigger m3-ripple-surface" aria-haspopup="listbox">
    <span class="sel-col">
      <span class="sel-label">配色方案</span>
      <span class="sel-value">Tonal Spot（默认）</span>
    </span>
    <svg class="sel-arrow" …/>
  </button>
  <div class="m3-select-menu" role="listbox">
    <button class="m3-option m3-ripple-surface selected" data-value="Tonal Spot（默认）">…</button>
  </div>
</div>
```

选中项会写入 `.sel-value` 并触发 Snackbar；组件按 `.m3-select` 自动初始化，新增实例无需额外 JS。

### 6.5 折叠面板

```html
<div class="m3-expansion open">
  <button class="m3-expansion-head m3-ripple-surface" aria-expanded="true">
    标题
    <svg class="exp-arrow" …/>
  </button>
  <div class="m3-expansion-body"><div><p>内容</p></div></div>
</div>
```

> 结构上 `.m3-expansion-body` 内部**必须**再包一层 `<div>`，否则 `grid-template-rows: 0fr → 1fr` 的高度动画不生效。

---

## 7. 水波纹机制

采用**事件委托**：整个文档只挂一个 `pointerdown` 监听，命中 `RIPPLE_SELECTOR` 即就地生成涟漪。

```js
document.addEventListener('pointerdown', function (e) {
  var el = e.target.closest(RIPPLE_SELECTOR);
  // 计算半径 = max(宽, 高) × 2.2，定位到指针处，追加 span.m3-ripple
  // 动画结束（520ms）自动移除，另设 900ms 兜底
}, { passive: true });
```

**关键特性**

- 动态创建的节点（日期格、表盘数字、分页按钮、轮播点、新加标签）**自动获得水波纹**，无需重新绑定
- 涟漪颜色由宿主元素的 `--ripple-color` 决定，未声明时回退 `currentColor`
- 覆盖类名清单：

```
.m3-btn .m3-icon-btn .m3-fab .m3-chip .m3-card .m3-carousel-item
.m3-list-item .m3-seg-btn .m3-tab .m3-menu-item .m3-nav-item
.m3-rail-item .m3-drawer-item .m3-switch-track .m3-checkbox-box
.m3-radio-circle .m3-slider-wrap .dp-cell .tp-num .m3-searchbar
.m3-select-trigger .m3-option .m3-expansion-head .m3-rating button
.m3-swatch .m3-page .m3-avatar .m3-number button .m3-sortable-item
.carousel-dot .m3-ripple-surface
```

若需手动为某个元素开启，直接加类 `.m3-ripple-surface`（自带 `position: relative; overflow: hidden; isolation: isolate`）。

---

## 8. 弹窗与覆盖层

四类覆盖层共用一套状态机：`openLayerEl()` / `closeLayer()` / `openLayer` / `#scrim`。

```js
openLayerEl(el);   // 显示遮罩 + 显示层 + 自动聚焦首个可交互元素
closeLayer();      // 关闭当前层 + 收起遮罩
```

**统一行为**

| 行为 | 实现 |
|---|---|
| 点击遮罩关闭 | `scrim` 的 click 绑定 `closeLayer` |
| Esc 关闭 | 全局 keydown 监听，同时收起菜单与 Snackbar |
| 打开时聚焦 | 延迟 80ms 聚焦首个 `button:not([data-close])` / `input` / `textarea` |
| 同一时刻仅一层 | `openLayerEl` 会先关闭已有层与所有菜单 |

底部抽屉档位通过 `data-height` 属性指定：

```html
<button data-sheet-open="half">底部抽屉 50%</button>  <!-- max-height: 52vh -->
<button data-sheet-open="full">底部抽屉 92%</button>  <!-- max-height: 92vh -->
```

---

## 9. 声明式 API（data-\*）

大部分交互通过 data 属性驱动，无需写 JS。

| 属性 | 作用 | 示例 |
|---|---|---|
| `data-snack` | 点击弹出 Snackbar | `data-snack="已保存"` |
| `data-dialog` | 打开指定 id 的对话框 | `data-dialog="dialogConfirm"` |
| `data-sheet-open` | 打开底部抽屉并指定档位 | `data-sheet-open="half"` |
| `data-close` | 关闭当前覆盖层 | — |
| `data-close-drawer` | 关闭抽屉（用于抽屉内导航项） | — |
| `data-menu` | 打开指定 id 的菜单 | `data-menu="menuDemo1"` |
| `data-goto` | 平滑滚动到指定区块并高亮导航 | `data-goto="sec-nav"` |
| `data-dismiss-banner` | 关闭所属横幅 | — |
| `data-tabs` | 标记标签页组容器（自动生成指示器滑动） | — |
| `data-panel` | 标签页内容面板索引 | `data-panel="1"` |
| `data-seg-group` | 标记分段按钮组（组内单选） | — |
| `data-navbar` | 标记底部导航栏（组内单选） | — |
| `data-tool` | 工具栏按钮名称（多选切换） | `data-tool="加粗"` |
| `data-section` / `data-cat` | 组件筛选的搜索范围与分类别名 | `data-cat="弹窗 dialog"` |
| `data-step` | 数字步进器的加减方向 | `data-step="-1"` |
| `data-min` / `data-max` | 数字步进器上下限 | `data-min="1"` |
| `data-color` | 取色器色值 | `data-color="#0058A8"` |
| `data-key` / `data-type` | 表格列排序字段与类型 | `data-key="count"` |
| `data-v` | 星级评分分值 | `data-v="4"` |
| `data-cat` | 区块分类关键词（供筛选命中） | — |

**全局接口**（调试用）

```js
window.closeLayer      // 关闭当前覆盖层
window.closeAllMenus   // 收起所有菜单
```

---

## 10. 无障碍（生产级）

本节按「可上生产」标准实现，不只是基础标注。

### 10.1 键盘可达性

| 措施 | 实现 |
|---|---|
| 跳转链接 | `<body>` 首个元素 `.skip-link` → `#mainContent`（`role="main"` + `tabindex="-1"`），激活后聚焦主内容 |
| 焦点可见 | 全局 `:focus-visible` 3px primary 描边 + 2px 偏移；深色底自动换用亮色焦点环 |
| 原生控件 | 交互一律用 `<button>` / `<input>`，Tab 顺序天然正确；**不使用可点击的 `<span>`** |
| 组合控件 | 见 10.3 的方向键导航 |

### 10.2 覆盖层焦点管理

| 能力 | 实现 |
|---|---|
| 焦点陷阱 | 覆盖层打开时 Tab 循环限定在层内，`Shift+Tab` 反向循环 |
| 焦点归还 | 关闭时焦点回到打开它的触发元素（`lastFocused` 记录） |
| 背景屏蔽 | 打开时给 `#navRail`、`.lib`、`.fab-dock` 加 `inert` + `aria-hidden="true"`，关闭时移除 |
| 语义角色 | `.m3-dialog` / `.m3-bottom-sheet` / `.m3-drawer` 均带 `role` 与 `aria-modal="true"` |
| 关闭方式 | 遮罩点击、`Esc`、取消按钮三种 |

> 焦点可见性判定用 `getClientRects().length > 0` 而非 `offsetParent`：固定定位祖先的 `offsetParent` 为 `null`，用它会把覆盖层内的按钮全部误判为不可见。

### 10.3 roving tabindex 与方向键

每个组合控件占**一个** Tab 停靠点，组内用方向键移动：

| 控件 | 角色 | 按键 |
|---|---|---|
| 标签页 | `tablist` / `tab` / `tabpanel` | ← →、Home、End，自动跟随激活并同步 `aria-selected` |
| 分段按钮 | `radiogroup` / `radio` | ← →，同步 `aria-checked` |
| 星级评分 | `radiogroup` / `radio` | ← →，同步 `aria-checked` |
| 底部导航栏 | `tablist` / `tab` | ← →，同步 `aria-selected` |
| 轮播指示点 | `tablist` / `tab` | ← →，同步 `aria-current` |
| 步骤条 | `tablist` / `tab` | ← →，同步 `aria-selected` + `aria-current="step"` |
| 下拉选择 | `combobox` / `listbox` / `option` | ↓ 打开并聚焦，↑↓ 移动，Home/End，`Esc` 关闭并回到触发器 |
| 自动补全 | `combobox` + `aria-autocomplete="list"` | ↓ 进入建议列表，↑↓ 移动，`Esc` 关闭 |
| 菜单 | `menu` / `menuitem` | ↓ 打开并聚焦首项，↑↓ 移动，Home/End，`Esc` 关闭并回到触发器 |

不自行处理 `Enter` / `Space`：原生 `<button>` 已触发 click，重复处理会导致动作执行两次。只接管方向键与 Home/End，并在 click 处理里调用返回的 `sync()` 让停靠点跟随视觉选中项。

### 10.4 ARIA 状态同步

被其他逻辑改动的控件，用 `MutationObserver` 监听 class 变化后重绘 ARIA：

| 控件 | 同步的属性 | 触发方 |
|---|---|---|
| 侧边栏 / 抽屉 | `aria-current="page"` | 滚动高亮（`IntersectionObserver`） |
| 步骤条 | `aria-selected` / `aria-current="step"` | 上一步 / 下一步 |
| 轮播指示点 | `aria-current` | 滚动吸附与前后按钮 |
| 折叠面板 | `aria-expanded` | 单个切换与「全部展开 / 收起」 |
| 验证码 | `aria-invalid` | 校验结果 |
| 表格表头 | `aria-sort` | 点击排序 |

监听时限定 `attributeFilter: ['class']`，这是避免死循环的关键——重绘 `aria-*` 不会再次触发观察器。

### 10.5 读屏播报

隐藏的实时区域，先清空再写入（否则重复内容不会被再次朗读）：

```js
var live = document.createElement('div');
live.className = 'sr-only';
live.setAttribute('role','status');
live.setAttribute('aria-live','polite');
live.setAttribute('aria-atomic','true');
document.body.appendChild(live);

function announce(msg){
  live.textContent = '';
  setTimeout(function(){ live.textContent = msg; }, 40);
}
```

播报节点切换、排序结果、选择变更等；Snackbar 自身也是 `role="status" aria-live="polite"`。

### 10.6 触控目标与降级

| 项 | 实现 |
|---|---|
| 触控目标 | 小控件（图标按钮 32px、轮播点 8px）用透明伪元素把命中区扩到 48×48dp，视觉尺寸不变 |
| 降低动效 | `@media (prefers-reduced-motion: reduce)` 把动效压缩到 0.01ms |
| 高对比度 | `@media (prefers-contrast: more)` 加深描边并放大边框宽度 |
| 强制配色 | `@media (forced-colors: active)` 用 `CanvasText` / `Highlight` 系统色，并隐藏水波纹 |
| 对比度 | 前景 / 背景组合取自 M3 Tonal Spot 配对，正文 ≥ 4.5:1，大字 ≥ 3:1 |
| 自动化检查 | `check_m3_html.py` 覆盖 8 项无障碍断言，见技能 `scripts/` |

> 伪元素分配注意：`.m3-checkbox-box::after` 是勾、`.m3-radio-circle::after` 是圆点、`.m3-swatch.selected::after` 是选中勾，均已占用，扩命中区时不要复用 `::after`。

---

## 11. 响应式

### 11.1 断点分档

| 宽度 | 变化 |
|---|---|
| `≤ 520px` | 页面内边距降至 14px，对话框内边距 20px，固定 FAB 贴近边缘，轮播项宽度增至 80% |
| `≤ 900px` | 隐藏左侧 Navigation Rail，内容列独占；改用抽屉导航 |
| `≥ 900px` | 显示 Navigation Rail，`.lib` 放宽到 1200px，阅读列加宽到 560px |
| `≥ 1200px` | `.lib` 1320px，阅读列 680px |
| `≥ 1600px` | `.lib` 1480px，阅读列 760px |
| `≥ 2100px` | 阅读列封顶 820px，避免行宽过长影响可读性 |

> **早期版本曾把 `.container` 恒定为 440px**，导致 900px 以上的屏幕上只有「88px 导航栏 + 一根细条」浮在大片空白中，看起来像坏了。上面按宽度分档放宽，并保证整体居中。

### 11.2 缩放与横向溢出

- **视口元信息**只放 `width=device-width, initial-scale=1.0, viewport-fit=cover`，**不加** `user-scalable=no` 或 `maximum-scale=1` —— 那会阻止用户双指放大看字，违反 WCAG 1.4.4。
- 双指缩小后右侧出现空白，是浏览器行为：**布局视口宽度不变**，可视视口变宽，超出的部分是文档之外。CSS 无法消除，唯一的「解法」是禁止缩放，代价更大，故不做。
- `html` 上加 `overflow-x: clip` 作为防御：覆盖层用 `translateX(±105%)` 移出屏幕，部分 WebView 会把它计入可滚动区域导致横向错位。用 `clip` 而非 `hidden`，因为 `clip` 不创建滚动容器，`.m3-appbar` 与 `.m3-nav-rail` 的 `position: sticky` 因此不受影响。
- `html` 与 `body` 都显式设置背景色，`body` 用 `min-height: 100dvh`（`100vh` 兜底），使绘制区域跟随移动端浏览器工具栏的伸缩。

### 11.3 兼容性兜底

浏览器支持 Chrome / Edge / Firefox / Safari 现代版本。`color-mix()` 处均带纯色回退，且**回退声明写在前面、`color-mix()` 写在后面**（顺序反了会导致 `color-mix` 永远被覆盖，等于没写）。

---

## 12. 扩展指南

### 12.1 换主色

只改一个变量即可全局生效：

```css
:root { --primary: #7B4E00; }
```

页面上的「取色器 → 应用到主色」按钮就是运行时动态设置 `--primary` 与 `--surface-tint` 的示例。

### 12.2 调整圆角 / 阴影 / 波纹

```css
:root {
  --radius-md: 20px;        /* 卡片、FAB、分段按钮同步变化 */
  --shadow-2: …;            /* 菜单、工具栏、FAB 同步变化 */
  --ripple-opacity: .32;    /* 水波纹浓度，也可用页面滑块实时试 */
}
```

### 12.3 新增组件区块

```html
<section id="sec-myblock" data-section data-cat="我的 myblock 关键词">
  <div class="section-title">My Block 我的组件</div>
  <!-- 组件标记 -->
</section>
```

加 `data-section` 后会自动纳入：

1. **组件筛选**（顶部搜索栏会索引该区块全部文本 + `data-cat` 别名，并更新命中计数徽标）
2. **滚动高亮**（`IntersectionObserver` 监听，导航项高亮跟随）

### 12.4 代码约定

| 约定 | 说明 |
|---|---|
| 类名前缀 | 全部使用 `m3-`，变体用 `--`（如 `m3-card--filled`），状态用单类（如 `.selected` `.open` `.loading`） |
| 颜色 | **禁止硬编码**，一律引用 `var(--token)`，否则暗色模式会失效 |
| 交互 | 可点击元素加 `.m3-ripple-surface`；需要悬停状态层加 `.m3-state` |
| 动效 | 时长用 `--duration-*`，曲线用 `--easing-*` |
| 脚本 | 全部包裹在 IIFE 内，`'use strict'` 模式，不污染全局（除两个调试接口） |

---

## 附录：文档校验记录

本文件生成时对 `设计规范.html` 执行的自动校验结果：

```
① HTML 标签闭合        OK
② id 唯一性            OK
③ JS → HTML id 引用    OK
④ JS → HTML class 引用 OK
⑤ 语义区块             17 处
⑥ 水波纹宿主           201 处
⑦ 颜色令牌             70 个
⑧ JS 语法（node --check）    OK
⑨ 加载期运行时          ✅ 无错误

无障碍断言（8 项，均已实测可触发）
A1 html lang            OK
A2 skip link 及目标存在  OK
A3 按钮无障碍名         OK（0 个无名按钮）
A4 覆盖层 role/aria-modal OK
A5 aria-live 实时区域    OK（5 处）
A6 prefers-reduced-motion OK
A7 :focus-visible       OK
A8 触控目标 48dp         OK
```

---

*Material 3 组件库 · 种子色 `#0058A8` · Tonal Spot · 零依赖单文件*
