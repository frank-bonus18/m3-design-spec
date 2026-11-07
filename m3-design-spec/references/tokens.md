# 设计令牌表（自动抽取自 `设计规范.html`）

> 本文件由脚本从参考实现的 `:root` 与 `[data-theme="dark"]` 两个令牌块直接抽取，
> 数值与代码完全一致，不要手工改写。

## 主色组 Primary

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

## 次要色组 Secondary

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--secondary` | `#425F80` | `#BBC7E0` |
| `--on-secondary` | `#FFFFFF` | `#0A3150` |
| `--secondary-container` | `#D7E3FB` | `#2A4768` |
| `--on-secondary-container` | `#001C36` | `#D7E3FB` |

## 第三色组 Tertiary

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--tertiary` | `#59588B` | `#C5C1FF` |
| `--on-tertiary` | `#FFFFFF` | `#2C2B5C` |
| `--tertiary-container` | `#E2E0FF` | `#424173` |
| `--on-tertiary-container` | `#161544` | `#E2E0FF` |

## 错误色组 Error

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--error` | `#B3261E` | `#F2B8B5` |
| `--on-error` | `#FFFFFF` | `#601410` |
| `--error-container` | `#F9DEDC` | `#8C1D18` |
| `--on-error-container` | `#410E0B` | `#F9DEDC` |

## 表面层级 Surface

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

## 描边 · 反色 · 遮罩

| 变量 | 亮色 | 暗色 |
|---|---|---|
| `--outline` | `#707884` | `#8A929E` |
| `--outline-variant` | `#C2C7CF` | `#42474E` |
| `--inverse-surface` | `#2E3135` | `#E0E2E8` |
| `--inverse-on-surface` | `#F0F0F6` | `#2E3135` |
| `--inverse-primary` | `#A3C8FF` | `#0058A8` |
| `--inverse-success` | `#9CE8AE` | `#2E7D46` |
| `--inverse-error` | `#FFB4AB` | `#8C1D18` |
| `--scrim` | `#000000` | `#000000` |
| `--scrim-color` | `rgba(0,0,0,.32)` | `rgba(0,0,0,.55)` |

## 规范常量（不随主题变化）

| 变量 | 值 | 说明 |
|---|---|---|
| `--radius-xs` | `8px` | 芯片 / 菜单 / 输入框 |
| `--radius-sm` | `12px` | 列表 / 折叠面板 / 小 FAB |
| `--radius-md` | `16px` | 卡片 / FAB / 分段按钮 |
| `--radius-lg` | `28px` | 大 FAB / 对话框 / 抽屉 |
| `--radius-full` | `999px` | 按钮 / 开关 / 徽标 / 头像 |
| `--ripple-opacity` | `.24` | 水波纹峰值透明度 |
| `--state-hover` | `.08` | 悬停状态层 |
| `--state-focus` | `.12` | 聚焦状态层 |
| `--state-pressed` | `.16` | 按压状态层 |
| `--disabled-opacity` | `.38` | 禁用前景 |
| `--disabled-container` | `.12` | 禁用容器 |
| `--shadow` | `rgba(0,0,0,.12)` |  |
| `--shadow-1` | `0 1px 2px rgba(0,0,0,.30),0 1px 3px 1px rgba(0,0,0,.15)` | 卡片 / 搜索栏 |
| `--shadow-2` | `0 1px 2px rgba(0,0,0,.30),0 2px 6px 2px rgba(0,0,0,.15)` | FAB / 菜单 / 工具栏 |
| `--shadow-3` | `0 4px 8px 3px rgba(0,0,0,.15),0 1px 3px rgba(0,0,0,.30)` | 对话框 / 抽屉 |
| `--shadow-4` | `0 6px 10px 4px rgba(0,0,0,.15),0 2px 3px rgba(0,0,0,.30)` | 高位悬浮 |
| `--shadow-5` | `0 8px 12px 6px rgba(0,0,0,.15),0 4px 4px rgba(0,0,0,.30)` | 最高海拔 |
| `--duration-short` | `150ms` | 短动效 |
| `--duration-medium` | `250ms` | 中等动效 |
| `--duration-long` | `400ms` | 长动效 |
| `--easing-standard` | `cubic-bezier(.2,0,0,1)` | 标准曲线 |
| `--easing-emphasized` | `cubic-bezier(.2,0,0,1)` | 强调曲线 |
| `--nav-rail-w` | `88px` | 侧边导航栏宽度 |
| `--font` | `Roboto,"Roboto Flex",system-ui,-apple-system,"Segoe UI","Noto Sans SC","PingFang SC",sans-serif` | 字体栈 |
| `--star` | `#F5B301` | 评分金星（theme-invariant） |
| `--on-media` | `#FFFFFF` | 饱和色块上的前景（theme-invariant） |

## 派生新配色的规则

1. 由种子色生成 5 档色调：Tone 0（近黑）/ 10 / 30 / 50 / 90（近白）。
2. 亮色：`--primary` 取 Tone 40，`--primary-container` 取 Tone 90，
   `--on-primary` 取 Tone 100，`--on-primary-container` 取 Tone 10。
3. 暗色镜像：`--primary` 取 Tone 80，`--primary-container` 取 Tone 30，
   `--on-primary` 取 Tone 20，`--on-primary-container` 取 Tone 90。
4. 次要色饱和度约为主色三分之一；第三色色相旋转约 60°。
5. 逐对校验对比度：正文 ≥ 4.5:1，大字与图标 ≥ 3:1。不达标时调**色调**，不要调色相。
6. `--error` 系列与种子色无关，使用固定色阶。

## theme-invariant 标记

颜色值但不随主题变化的常量（如 `--star`、`--on-media`）只声明在 `:root`，
并在行尾注释里写 `theme-invariant`，供 `check_m3_html.py` 跳过「暗色缺失」检查。
不要用它掩盖真正的遗漏。

## 渐变例外

出现在 `gradient()` 里的十六进制色值被视为装饰性美术（媒体占位、彩虹色板），
校验器只作为提示列出，不计为错误。其余一律必须走令牌。
