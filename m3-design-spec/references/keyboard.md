# 键盘与自动化模型

如何让 M3 页面完全脱离指针操作，以及如何暴露接口让程序或 AI 驱动它。

## 九条硬规则

1. **每个组合控件只占一个 Tab 停靠点。** 标签页、芯片、单选框、日期格、列表行都是「整组一个」，组内移动用方向键。
2. **roving tabindex。** 组内恰好一个元素 `tabindex="0"`，其余 `-1`。移动时同步迁移那个 `0`。**绝不能出现整组都是 `-1`** —— 那组会变得不可达；没有选中项时把第一项设为 `0`。
3. **每个可点击元素都能聚焦。** 没有 `tabindex="0"` + `role` + Enter/Space 处理的可点击 `<div>`/`<span>` 都是 bug。优先用 `<button>`。
4. **处理了方向键就要 `preventDefault()`**，否则页面同时滚动。
5. **不要在 `<button>` 上再处理 Enter/Space。** 原生 click 已经会触发，重复处理会执行两次。
6. **`Escape` 关闭最内层**，并把焦点还给打开它的元素。
7. **焦点不能因重渲染丢失。** 重渲染替换了焦点节点时，把焦点移到逻辑后继节点，否则键盘用户会被弹回文档开头。
8. **输入框内不触发全局快捷键。** 先判断目标是 `input` / `textarea` / `select` / `contenteditable`。`Escape` 是唯一例外。
9. **运行时重建的元素用事件委托处理按键。** 逐节点监听会在重建时静默失效。每次渲染后调用同一个幂等的 `enhanceA11y(root)`，并用标记位防止重复绑定。

## roving tabindex 实现

```js
function rovingGroup(items, getActiveIndex, activate, orientation){
  orientation = orientation || 'both';
  var horiz = orientation === 'horizontal' || orientation === 'both';
  var vert  = orientation === 'vertical'   || orientation === 'both';

  function sync(){
    var idx = getActiveIndex();
    if(idx < 0) idx = 0;                  // 整组不可达是最严重的错误
    items.forEach(function(it, i){ it.tabIndex = (i === idx) ? 0 : -1; });
  }
  items.forEach(function(it, i){
    it.addEventListener('keydown', function(e){
      var last = items.length - 1, next = null;
      if(horiz && e.key === 'ArrowRight')      next = i >= last ? 0 : i + 1;
      else if(horiz && e.key === 'ArrowLeft')  next = i <= 0 ? last : i - 1;
      else if(vert && e.key === 'ArrowDown')   next = i >= last ? 0 : i + 1;
      else if(vert && e.key === 'ArrowUp')     next = i <= 0 ? last : i - 1;
      else if(e.key === 'Home')                next = 0;
      else if(e.key === 'End')                 next = last;
      else return;
      e.preventDefault();
      activate(next);
      sync();
      items[next].focus();
    });
  });
  sync();
  return sync;                             // 在 click 处理里再调用，让停靠点跟随视觉选中
}
```

## 各组件键位

| 组件 | 按键 |
|---|---|
| 标签页 / 分段按钮 / 底部导航 | `←` `→` 移动并选中；`Home` `End` 到两端 |
| 筛选芯片 | `←` `→` 移动焦点；`Space` / `Enter` 切换 |
| 单选框组 | `←` `→` `↑` `↓` 移动并选中（原生行为） |
| 菜单 | `↓` 打开并聚焦首项；`↑` `↓` 移动；`Home` `End`；`Esc` 关闭并回到触发器 |
| 级联菜单 | `→` 展开子菜单并进入；`←` 收起并回到父项 |
| 下拉 / 列表框 | `↓` 打开；`↑` `↓` `Home` `End` 移动；`Enter` 选中；`Esc` 关闭 |
| 自动补全 | `↓` 进入建议列表；输入过滤；`Enter` 接受；`Esc` 关闭 |
| 多选下拉 | `Enter` / `Space` / `↓` 打开；`↑` `↓` 移动；`Space` 切换；`Esc` 回到触发器 |
| 树 | `↑` `↓` 在可见行间移动；`→` 展开；`←` 收起；`Enter` 激活 |
| 日期选择器 | `←` `→` ±1 天；`↑` `↓` ±1 周；`Home` `End` 周首/周末；`PageUp` `PageDown` ±1 月；`Enter` 选定 |
| 滑块 | `←` `→` ±步长（原生）；`Home` `End` 到边界 |
| 命令面板 | 输入过滤；`↑` `↓` `Home` `End` 移动；`Enter` 执行；`Esc` 关闭 |
| 快捷键帮助 | `?` 打开；`Esc` 关闭；`Tab` 在层内循环 |
| 对话框 / 抽屉 / 侧边表单 | `Tab` 层内循环；`Esc` 关闭；焦点归还触发器 |
| 轮播 | `←` `→` 上一张 / 下一张；单项可聚焦 |
| 提示宿主 | 可聚焦，让 Tooltip 不依赖 hover |
| 竖向步骤 | `↑` `↓` 移动；`Enter` 执行当前步操作 |
| 前缀跳转列表 | 输入字母跳到对应开头项；`↑` `↓` `Home` `End`；`Enter` 打开 |

## 焦点可见性

```css
:where(button,a,input,select,textarea,[tabindex]):focus-visible{
  outline:3px solid var(--primary);
  outline-offset:2px;
}
/* 网格类元素用内描边，避免被 overflow:hidden 祖先裁掉 */
.dp-cell:focus-visible,
.tp-num:focus-visible,
.m3-seg-btn:focus-visible{ outline-offset:-3px; }
```

用 `:focus-visible` 而非 `:focus`，鼠标用户不会看到焦点环。

## 全局快捷键注册表

一个数组作为唯一真相来源，帮助浮层、文档、程序接口都从它派生。

```js
var COMMANDS = [
  {id:'help',  group:'全局', label:'打开 / 关闭快捷键帮助', keys:['?'],        run:function(){ toggleKeys(); }},
  {id:'cmdk',  group:'全局', label:'打开 / 关闭命令面板',   keys:['Ctrl','K'], run:function(){ toggleCmdk(); }},
  {id:'theme', group:'全局', label:'切换亮色 / 暗色模式',   keys:['g','t'],    run:function(){ toggleTheme(); }},
  {id:'close', group:'全局', label:'关闭当前浮层',          keys:['Esc'],      run:function(){ closeEverything(); }}
];

window.m3Keys = {
  commands: COMMANDS,
  invoke: function(id){
    var c = COMMANDS.filter(function(x){ return x.id === id; })[0];
    if(!c) return false;
    try{ c.run(); }catch(e){ return false; }
    return true;
  },
  format: function(id){
    var c = COMMANDS.filter(function(x){ return x.id === id; })[0];
    return c ? c.keys.join(' + ') : '';
  }
};
```

`run` 不带参数，这样程序调用、帮助渲染、测试都简单。

参考实现的 14 条命令：`?` 帮助、`Ctrl+K` 命令面板、`Esc` 关闭、`g t` 主题、`g g` 顶部、`g a` 操作、`g n` 导航、`g f` 表单、`g d` 数据、`g u` 认证、`g k` 键盘、`g 1` 引导、`g 2` 通知、`g c` 主内容。

## 两段式前缀序列

`g` 前缀在非拉丁键盘上更友好，也避开修饰键冲突。

```js
var pendingPrefix = null, prefixTimer = null;

document.addEventListener('keydown', function(e){
  if(e.key === 'Escape'){ closeEverything(); return; }
  if(isTyping(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;

  if(pendingPrefix === 'g'){
    clearTimeout(prefixTimer);
    pendingPrefix = null;
    var combo = 'g ' + e.key.toLowerCase();
    for(var i = 0; i < COMMANDS.length; i++){
      if(COMMANDS[i].keys.join(' ').toLowerCase() === combo){
        e.preventDefault();
        COMMANDS[i].run();
        return;
      }
    }
    return;                                  // 前缀不匹配就静默丢弃
  }
  if(e.key === 'g' || e.key === 'G'){
    pendingPrefix = 'g';
    prefixTimer = setTimeout(function(){ pendingPrefix = null; }, 1500);
    return;
  }
  if(e.key === '?'){ e.preventDefault(); toggleKeys(); }
});
```

带修饰键的快捷键必须另挂一个监听器，因为上面的分发器在 `ctrlKey` 时直接返回：

```js
document.addEventListener('keydown', function(e){
  if((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')){
    e.preventDefault();
    toggleCmdk();
  }
});
```

避免 `Ctrl+D`（收藏）、`Ctrl+S`（保存页面）、`Ctrl+W`（关标签）、`Ctrl+N`（新窗口）：页面无法可靠拦截。

## 可重入的无障碍增强器

加载后创建的节点需要同样处理。暴露一个幂等函数，在每个渲染路径里调用。

```js
function makeActionable(el, label){
  if(!el.hasAttribute('tabindex')) el.setAttribute('tabindex','0');
  if(!el.hasAttribute('role')) el.setAttribute('role','button');
  if(label && !el.hasAttribute('aria-label')) el.setAttribute('aria-label', label);
  if(el.__kbWired) return;                   // 防重复绑定
  el.__kbWired = true;
  el.addEventListener('keydown', function(e){
    if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); el.click(); }
  });
}

function enhanceA11y(root){
  root = root || document;
  applyChipRoving(root);                     // 每组只留一个 Tab 停靠点
  $$('.m3-avatar', root).forEach(a => makeActionable(a, a.textContent.trim() + ' 成员'));
  $$('.m3-carousel-item', root).forEach(it => makeActionable(it));
  $$('[data-sheet]', root).forEach(it => makeActionable(it));  // 声明式点击目标
}
window.m3Enhance = enhanceA11y;
```

在每个动态渲染后调用：

```js
function render(){
  host.innerHTML = '';
  /* …建节点… */
  if(window.m3Enhance) window.m3Enhance(host);
}
```

**装饰性芯片不要参与 roving。** 徽标、状态、分类这类纯视觉标记加 `.m3-chip--static`，并在 roving 过滤里排除；否则键盘用户要为每个标签多按一次 Tab。

```js
function isFilterChip(c){
  if(!c.classList.contains('m3-chip')) return false;
  if(c.classList.contains('m3-chip--static')) return false;
  return !(c.classList.contains('assist') || c.classList.contains('input') ||
           c.classList.contains('suggestion') || c.classList.contains('with-avatar'));
}
```

## 最便宜的回归测试

枚举所有带 click 监听的元素，断言它们可聚焦：

```js
function focusable(el){
  if(el.hasAttribute('tabindex')) return true;
  const t = el.tagName;
  if(t === 'BUTTON' || t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA'){
    return el._attrs.disabled === undefined;
  }
  if(t === 'A' && el._attrs.href !== undefined) return true;
  return false;
}
const unreachable = all.filter(el => el._listeners && el._listeners.click && !focusable(el));
```

期望的例外只有两类：遮罩（`Esc` 才是真正的关闭方式）和禁用按钮（本就不该可聚焦）。其余都是 bug。

## 无浏览器验证键盘行为

`dom_harness.js` 跟踪 `activeElement`，因此方向键导航可以测。两个细节必须成立：

- `el.focus()` 更新共享的 `activeElement`，否则所有焦点断言都没有意义。
- `el.tabIndex = 0` 是**反射属性**，会写入 `tabindex` 特性，与真实 DOM 一致。把它当普通字段的实现会读出 `null`，从而掩盖真实 bug。

最小检查：

```js
const cells = doc.querySelectorAll('.dp-cell');
const sel = cells.filter(c => c.classList.contains('selected'))[0];
sel.focus();
fire(grid, 'keydown', { key:'ArrowRight', preventDefault(){} });
// 焦点应落到下一天
assert(parseInt(document.activeElement.textContent, 10) === parseInt(sel.textContent, 10) + 1);
```

## 暴露给程序 / AI 的接口

除快捷键注册表外，把状态变更函数也导出，让调用方不必合成输入事件：

| 导出 | 用途 |
|---|---|
| `window.m3Keys.commands` / `.invoke(id)` / `.format(id)` | 枚举并执行全部全局命令 |
| `window.openKeys()` / `.closeKeys()` | 快捷键帮助浮层 |
| `window.openCmdk()` / `.closeCmdk()` / `.cmdkIsOpen()` | 命令面板 |
| `window.startTour()` / `.closeTour()` | 引导浮层 |
| `window.applyTheme(dark)` / `.toggleTheme()` | 主题 |
| `window.notify({type,title,text})` | 通知堆叠 |
| `window.announce(msg)` | 读屏播报 |
| `window.m3Enhance(root)` | 对动态节点重新应用无障碍处理 |
| `window.m3Contrast.ratio(a,b)` / `.luminance(hex)` / `.grade(r)` | 对比度计算 |
| `window.m3Zoom.state()` / `.refresh()` | 缩放补偿状态 |
| `window.closeLayer()` / `.closeAllMenus()` | 关闭覆盖层 / 菜单 |

每个导出尽量无参或只收一个对象，方便脚本调用。把清单写在调用方能读到的地方（`window.m3Keys.commands` 就是最直接的一份）。
