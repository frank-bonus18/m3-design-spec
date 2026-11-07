#!/usr/bin/env node
/*
 * regression_tests.js — 单文件 M3 页面的端到端行为回归。
 *
 * 通过 dom_harness.js 加载页面，逐项验证参考实现交付的组件：
 * 覆盖层、选择器、手势、表单、认证、键盘模型、规范可视化。
 * 改完页面跑一遍；也可以把它当作模板，替换选择器来测你自己生成的页面。
 *
 * 用法：
 *   node regression_tests.js <page.html>
 *   M3_VERBOSE=1 node regression_tests.js <page.html>   # 逐条打印通过项
 *
 * 退出码：
 *   0  全部通过
 *   1  有失败项
 *   2  输入不可用 / 页面加载期抛错
 */

const path = require('path');
const H = require(path.join(__dirname, 'dom_harness.js'));

const uri = process.argv[2] || process.env.M3_PAGE;
if (!uri) {
  console.error('用法: node regression_tests.js <page.html>');
  process.exit(2);
}

const { doc, fire, loadError } = H;
if (loadError) {
  console.error('页面加载期异常:');
  console.error('  ' + loadError.message);
  (loadError.stack || '').split('\n').slice(1, 6).forEach(l => console.error('  ' + l.trim()));
  process.exit(2);
}

let failed = 0;
let passed = 0;

function ok(name, cond, extra) {
  if (cond) {
    passed++;
    if (process.env.M3_VERBOSE) console.log('  ok   ' + name);
  } else {
    failed++;
    console.log('  FAIL ' + name + (extra === undefined ? '' : '  → ' + extra));
  }
}
function group(title) {
  if (process.env.M3_VERBOSE) console.log('\n== ' + title + ' ==');
}

function byClass(root, cls) {
  const out = [];
  (function walk(el) {
    if (el.classList && el.classList.contains(cls)) out.push(el);
    (el._children || []).forEach(walk);
  })(root || doc);
  return out;
}
function allEls() {
  const out = [];
  (function walk(el) { out.push(el); (el._children || []).forEach(walk); })(doc);
  return out;
}

/* ---------------------------------------------------------------- */
group('主题');
(function () {
  const toggle = doc.querySelector('#themeToggle');
  ok('主题开关存在', !!toggle);
  if (!toggle) return;
  toggle.checked = true;
  fire(toggle, 'change', { target: toggle });
  ok('勾选后写入 data-theme', doc.documentElement.hasAttribute('data-theme'));
  toggle.checked = false;
  fire(toggle, 'change', { target: toggle });
  ok('取消后移除 data-theme', !doc.documentElement.hasAttribute('data-theme'));
})();

group('跳转链接与主内容');
(function () {
  const skip = doc.querySelector('.skip-link');
  ok('跳转链接存在', !!skip);
  ok('指向 mainContent', skip && skip.getAttribute('href') === '#mainContent',
    skip && skip.getAttribute('href'));
  const main = doc.querySelector('#mainContent');
  ok('主内容可聚焦', main && main.getAttribute('tabindex') === '-1');
})();

group('覆盖层');
(function () {
  const scrim = doc.querySelector('#scrim');
  ok('遮罩存在', !!scrim);

  const openBtn = allEls().filter(el => el.getAttribute && el.getAttribute('data-dialog') === 'dialogConfirm')[0];
  ok('删除对话框触发按钮存在', !!openBtn);
  if (openBtn) {
    openBtn.click();
    const dlg = doc.querySelector('#dialogConfirm');
    ok('对话框已打开', dlg.classList.contains('show'));
    ok('遮罩已显示', scrim.classList.contains('show'));
    ok('背景被 inert', doc.querySelector('.lib').hasAttribute('inert'));
    const close = dlg.querySelector('[data-close]');
    if (close) close.click();
    ok('关闭后遮罩收起', !scrim.classList.contains('show'));
    ok('关闭后解除 inert', !doc.querySelector('.lib').hasAttribute('inert'));
  }

  const sheetBtn = allEls().filter(el => el.getAttribute && el.getAttribute('data-sheet-open'))[0];
  ok('底部抽屉触发按钮存在', !!sheetBtn);
  if (sheetBtn) {
    sheetBtn.click();
    ok('抽屉已打开', doc.querySelector('#sheet').classList.contains('show'));
    scrim.click();
    ok('点遮罩可关闭', !doc.querySelector('#sheet').classList.contains('show'));
  }

  const ssBtn = doc.querySelector('#sideSheetBtn');
  ok('侧边表单按钮存在', !!ssBtn);
  if (ssBtn) {
    ssBtn.click();
    ok('侧边表单已打开', doc.querySelector('#sideSheet').classList.contains('show'));
    ok('侧边表单有 aria-modal', doc.querySelector('#sideSheet').getAttribute('aria-modal') === 'true');
    const apply = doc.querySelector('#sideSheetApply');
    if (apply) apply.click();
    ok('应用后关闭', !doc.querySelector('#sideSheet').classList.contains('show'));
  }
})();

group('反馈');
(function () {
  const snack = allEls().filter(el => el.getAttribute && el.getAttribute('data-snack'))[0];
  ok('有 data-snack 触发点', !!snack);
  if (snack) {
    snack.click();
    ok('Snackbar 显示', doc.querySelector('#snackbar').classList.contains('show'));
  }

  const stack = doc.querySelector('#notifStack');
  ok('通知容器存在', !!stack);
  if (stack && window.notify) {
    for (let i = 0; i < 5; i++) window.notify({ type: 'info', title: 't' + i, text: 'x' });
    const active = stack._children.filter(c => !c.classList.contains('leaving')).length;
    ok('活动通知不超过 3 条', active <= 3, active);
  }
})();

group('数字步进器');
(function () {
  const num = doc.querySelector('#num1');
  ok('步进器存在', !!num);
  if (!num) return;
  const input = num.querySelector('input');
  const btns = num.querySelectorAll('button');
  const inc = btns.filter(b => b.getAttribute('data-step') === '1')[0];
  const dec = btns.filter(b => b.getAttribute('data-step') === '-1')[0];
  ok('有加减按钮', !!inc && !!dec);
  if (!inc || !dec) return;
  const before = parseInt(input.value, 10);
  inc.click();
  ok('加一', parseInt(input.value, 10) === before + 1, input.value);
  dec.click();
  dec.click();
  ok('连减两次', parseInt(input.value, 10) === before - 1, input.value);
})();

group('日期选择器键盘');
(function () {
  const grid = doc.querySelector('#dpGrid');
  ok('日历存在', !!grid);
  if (!grid) return;
  const cells = () => byClass(grid, 'dp-cell');
  ok('42 个格子', cells().length === 42, cells().length);
  ok('恰好一个 Tab 停靠点',
    cells().filter(c => c.getAttribute('tabindex') === '0').length === 1);
  ok('每格有 aria-label', cells().every(c => !!c.getAttribute('aria-label')));

  const sel = cells().filter(c => c.classList.contains('selected'))[0];
  if (!sel) return;
  const day = parseInt(sel.textContent, 10);
  sel.focus();
  fire(grid, 'keydown', { key: 'ArrowRight', preventDefault() {} });
  ok('右移到下一天', parseInt(doc.activeElement.textContent, 10) === day + 1,
    doc.activeElement.textContent);
  fire(grid, 'keydown', { key: 'ArrowDown', preventDefault() {} });
  ok('下移一周', parseInt(doc.activeElement.textContent, 10) === day + 8,
    doc.activeElement.textContent);
  const month = doc.querySelector('#dpTitle').textContent;
  fire(grid, 'keydown', { key: 'PageUp', preventDefault() {} });
  ok('PageUp 翻月', doc.querySelector('#dpTitle').textContent !== month);
  fire(grid, 'keydown', { key: 'PageDown', preventDefault() {} });
  ok('PageDown 翻回', doc.querySelector('#dpTitle').textContent === month);
})();

group('时间选择器');
(function () {
  const dial = doc.querySelector('#tpDial');
  ok('表盘存在', !!dial);
  if (!dial) return;
  ok('注册了 pointerdown', Object.keys(dial._listeners || {}).indexOf('pointerdown') >= 0);
  ok('注册了 keydown', Object.keys(dial._listeners || {}).indexOf('keydown') >= 0);

  const hourEl = doc.querySelector('#tpHour');
  hourEl.click();
  fire(dial, 'pointerdown', { pointerId: 1, clientX: 600, clientY: 480, buttons: 1, cancelable: true });
  fire(dial, 'pointerup', { pointerId: 1, clientX: 600, clientY: 480, buttons: 0 });
  ok('拖到下方得到 6 点', hourEl.textContent === '6', hourEl.textContent);

  const before = hourEl.textContent;
  fire(dial, 'keydown', { key: 'ArrowUp', preventDefault() {} });
  ok('方向键调小时', hourEl.textContent !== before, hourEl.textContent);
})();

group('下拉 / 多选');
(function () {
  const sel = doc.querySelector('#select1');
  ok('下拉存在', !!sel);
  if (sel) {
    const trigger = sel.querySelector('.m3-select-trigger');
    trigger.click();
    ok('点击展开', sel.classList.contains('open'));
    const opts = byClass(sel, 'm3-option');
    ok('有选项', opts.length > 1, opts.length);
    if (opts[1]) {
      opts[1].click();
      ok('选择后收起', !sel.classList.contains('open'));
      ok('选中态已更新', opts[1].getAttribute('aria-selected') === 'true',
        opts[1].getAttribute('aria-selected'));
    }
  }

  const ms = doc.querySelector('#ms1');
  ok('多选存在', !!ms);
  if (ms) {
    const trig = ms.querySelector('.m3-ms-trigger');
    fire(trig, 'keydown', { key: 'ArrowDown', preventDefault() {} });
    ok('方向键可打开', ms.classList.contains('open'));
    ok('有多选项', byClass(ms, 'm3-ms-option').length > 1);
  }
})();

group('表单');
(function () {
  const tagInput = doc.querySelector('#tagInput');
  ok('标签输入存在', !!tagInput);
  if (tagInput) {
    tagInput.value = '新标签';
    fire(tagInput, 'keydown', { key: 'Enter', preventDefault() {} });
    const tags = byClass(doc.querySelector('#tagField'), 'm3-tag');
    ok('回车添加标签', tags.some(t => t.textContent.indexOf('新标签') >= 0),
      tags.map(t => t.textContent).join('|'));
  }

  const otp = doc.querySelector('#otp');
  ok('验证码存在', !!otp);
  if (otp) {
    const inputs = otp.querySelectorAll('input');
    inputs[0].value = '2';
    fire(inputs[0], 'input', { target: inputs[0] });
    ok('输入后自动跳格', doc.activeElement === inputs[1]);
    const fill = doc.querySelector('#otpFill');
    if (fill) {
      fill.click();
      ok('填充示例后校验通过', doc.querySelector('#otpMsg').className.indexOf('ok') >= 0,
        doc.querySelector('#otpMsg').className);
    }
  }

  const ie = doc.querySelector('[data-inline-edit]');
  ok('就地编辑存在', !!ie);
  if (ie) {
    const view = ie.querySelector('.m3-inline-edit-value');
    const text = ie.querySelector('.ie-text');
    view.click();
    const inp = ie.querySelector('input');
    ok('点击出现输入框', !!inp);
    if (inp) {
      inp.value = '新名称';
      fire(inp, 'keydown', { key: 'Enter', preventDefault() {} });
      ok('回车保存', text.textContent === '新名称', text.textContent);
      ok('输入框移除', !ie.querySelector('input'));
    }
  }
})();

group('登录表单');
(function () {
  const form = doc.querySelector('#loginForm');
  ok('登录表单存在', !!form);
  if (!form) return;
  const email = doc.querySelector('#loginEmail');
  const pw = doc.querySelector('#loginPw');
  const submit = doc.querySelector('#loginSubmit');
  ok('邮箱/密码/按钮齐全', !!(email && pw && submit));

  fire(form, 'submit', { preventDefault() {} });
  ok('空提交显示错误', !doc.querySelector('#loginError').hidden);
  ok('邮箱字段标红', email.closest('.m3-field').classList.contains('error'));

  email.value = 'not-an-email';
  pw.value = '12345678';
  fire(form, 'submit', { preventDefault() {} });
  ok('非法邮箱被拦', email.closest('.m3-field').classList.contains('error'));

  email.value = 'a@b.co';
  fire(email, 'input', { target: email });
  fire(form, 'submit', { preventDefault() {} });
  ok('合法邮箱通过字段校验', !email.closest('.m3-field').classList.contains('error'));

  const toggle = doc.querySelector('.pw-toggle[data-pw-toggle="loginPw"]');
  ok('密码显隐按钮存在', !!toggle);
  if (toggle) {
    toggle.click();
    ok('切换为明文', pw.type === 'text', pw.type);
    ok('aria-pressed 同步', toggle.getAttribute('aria-pressed') === 'true');
    toggle.click();
    ok('切回密文', pw.type === 'password', pw.type);
  }
})();

group('手势');
(function () {
  const list = doc.querySelector('#swipeList');
  ok('滑动列表存在', !!list);
  if (list) {
    const items = byClass(list, 'm3-swipe-item');
    ok('有可滑项', items.length > 0, items.length);
    const content = items[0] && items[0].querySelector('.m3-swipe-content');
    if (content) {
      fire(content, 'pointerdown', { pointerId: 1, clientX: 300, clientY: 100, button: 0, buttons: 1 });
      fire(content, 'pointermove', { pointerId: 1, clientX: 150, clientY: 100, buttons: 1 });
      fire(content, 'pointerup', { pointerId: 1, clientX: 150, clientY: 100, buttons: 0 });
      ok('滑动不抛异常', true);
    }
  }
  const sortable = doc.querySelector('#sortable');
  ok('排序列表存在', !!sortable);
  if (sortable) ok('有拖拽手柄', byClass(sortable, 'drag-handle').length > 0);
})();

group('键盘');
(function () {
  ok('m3Keys 已暴露', !!window.m3Keys);
  if (window.m3Keys) {
    const cmds = window.m3Keys.commands;
    ok('命令数 > 10', cmds.length > 10, cmds.length);
    ok('每条结构完整',
      cmds.every(c => c.id && c.group && c.label && c.keys && c.keys.length));
    ok('format 可用', window.m3Keys.format('cmdk') === 'Ctrl + K',
      window.m3Keys.format('cmdk'));

    const before = doc.documentElement.hasAttribute('data-theme');
    const okRun = window.m3Keys.invoke('theme');
    const after = doc.documentElement.hasAttribute('data-theme');
    ok('invoke 可执行并改变状态', okRun === true && before !== after);
    ok('未知命令返回 false', window.m3Keys.invoke('nope') === false);

    window.m3Keys.open();
    const scrim = doc.querySelector('#keysScrim');
    ok('帮助浮层可打开', scrim.classList.contains('show'));
    ok('渲染了快捷键行',
      byClass(doc.querySelector('#keysGroups'), 'm3-keys-row').length === cmds.length);
    window.m3Keys.close();
    ok('帮助浮层可关闭', !scrim.classList.contains('show'));
  }

  const cmdkScrim = doc.querySelector('#cmdkScrim');
  ok('命令面板存在', !!cmdkScrim);
  if (cmdkScrim && window.openCmdk) {
    window.openCmdk();
    ok('命令面板可打开', cmdkScrim.classList.contains('show'));
    const list = doc.querySelector('#cmdkList');
    const items = byClass(list, 'm3-cmdk-item');
    ok('命令项已渲染', items.length > 5, items.length);
    const inp = doc.querySelector('#cmdkInput');
    const cur0 = items.findIndex(i => i.classList.contains('cursor'));
    fire(inp, 'keydown', { key: 'ArrowDown', preventDefault() {} });
    const cur1 = byClass(list, 'm3-cmdk-item').findIndex(i => i.classList.contains('cursor'));
    ok('方向键移动光标', cur1 === cur0 + 1, cur0 + '→' + cur1);
    inp.value = '配色';
    fire(inp, 'input', { target: inp });
    ok('过滤生效', byClass(list, 'm3-cmdk-item').length < items.length);
    inp.value = 'zzzz';
    fire(inp, 'input', { target: inp });
    ok('无结果空态', byClass(list, 'm3-cmdk-empty').length === 1);
    window.closeCmdk();
    ok('命令面板可关闭', !cmdkScrim.classList.contains('show'));
  }
})();

group('组合控件键盘');
(function () {
  const heads = byClass(doc, 'm3-expansion-head');
  ok('折叠面板存在', heads.length > 1, heads.length);
  if (heads.length > 1) {
    const ex = heads[0].closest('.m3-expansion');
    const open0 = ex.classList.contains('open');
    heads[0].click();
    ok('点击切换展开态', ex.classList.contains('open') !== open0);

    heads[0].focus();
    fire(heads[0], 'keydown', { key: 'ArrowDown', preventDefault() {} });
    ok('方向键移到下一个标题', doc.activeElement === heads[1]);
  }

  const vsteps = byClass(doc.querySelector('#vsteps') || doc, 'm3-vstep');
  ok('竖向步骤存在', vsteps.length > 1, vsteps.length);
  if (vsteps.length > 1) {
    ok('步骤可聚焦', vsteps.every(s => s.hasAttribute('tabindex')));
    vsteps[0].focus();
    fire(vsteps[0], 'keydown', { key: 'ArrowDown', preventDefault() {} });
    ok('方向键下移步骤', doc.activeElement === vsteps[1]);
  }

  const chips = byClass(doc, 'm3-chip').filter(c =>
    !c.classList.contains('assist') && !c.classList.contains('input') &&
    !c.classList.contains('suggestion') && !c.classList.contains('with-avatar') &&
    !c.classList.contains('m3-chip--static'));
  ok('有可筛选 chip', chips.length > 0, chips.length);
  const owners = [];
  chips.forEach(c => { if (owners.indexOf(c._parent) < 0) owners.push(c._parent); });
  const bad = owners.filter(p =>
    chips.filter(c => c._parent === p).filter(c => c.getAttribute('tabindex') === '0').length !== 1);
  ok('每组恰好一个 Tab 停靠点', bad.length === 0, bad.length + ' 组不合规');

  // 事件委托：动态新增的 chip 也能用方向键
  const group0 = chips.filter(c => c._parent === chips[0]._parent);
  if (group0.length > 1) {
    group0.forEach((c, i) => { c.tabIndex = i === 0 ? 0 : -1; });
    group0[0].focus();
    fire(group0[0], 'keydown', { key: 'ArrowRight', preventDefault() {} });
    ok('chip 方向键（事件委托）', doc.activeElement === group0[1]);
  }
})();

group('规范可视化');
(function () {
  const grid = doc.querySelector('#swatchGrid');
  ok('色板网格存在', !!grid);
  if (grid) {
    const cells = byClass(grid, 'm3-swatch-cell');
    ok('12 组色板', cells.length === 12, cells.length);
    ok('每块可聚焦', cells.every(c => c.getAttribute('tabindex') === '0'));
    ok('有对比度角标', byClass(grid, 'm3-swatch-badge').length === 12);
  }

  ok('m3Contrast 已暴露', !!window.m3Contrast);
  if (window.m3Contrast) {
    ok('黑白 = 21:1', Math.abs(window.m3Contrast.ratio('#000000', '#FFFFFF') - 21) < 0.01,
      window.m3Contrast.ratio('#000000', '#FFFFFF'));
    ok('同色 = 1:1', Math.abs(window.m3Contrast.ratio('#123456', '#123456') - 1) < 0.001);
    const g = window.m3Contrast.grade(7.2);
    ok('grade(7.2) 三项全过', g.aa && g.aaa && g.large);
    const g2 = window.m3Contrast.grade(3.5);
    ok('grade(3.5) 仅大字过', !g2.aa && !g2.aaa && g2.large);
  }

  const fg = doc.querySelector('#cFg');
  ok('对比度检查器存在', !!fg);
  if (fg) {
    ok('初始色值已反射', /^#[0-9a-f]{6}$/i.test(fg.value), fg.value);
    fg.value = '#000000';
    doc.querySelector('#cBg').value = '#ffffff';
    fire(fg, 'input', { target: fg });
    ok('黑白算出 21', doc.querySelector('#cRatio').textContent.indexOf('21.00') === 0,
      doc.querySelector('#cRatio').textContent);
    fg.value = '#777777';
    fire(fg, 'input', { target: fg });
    ok('低对比度判不合格',
      byClass(doc, 'm3-pass').some(p => p.classList.contains('no')));
  }

  const curve = doc.querySelector('#curvePath');
  ok('曲线路径已生成', /^M .* C /.test(curve.getAttribute('d') || ''),
    curve.getAttribute('d'));
  const easeBtns = allEls().filter(el => el.getAttribute && el.getAttribute('data-ease'));
  ok('有曲线预设', easeBtns.length === 4, easeBtns.length);
  if (easeBtns[2]) {
    easeBtns[2].click();
    ok('切换曲线生效', /cubic-bezier/.test(doc.querySelector('#curveCode').textContent));
  }

  const flist = doc.querySelector('#filterList');
  ok('筛选列表存在', !!flist);
  if (flist) {
    const items = () => byClass(flist, 'm3-filter-item');
    ok('初始 24 条', items().length === 24, items().length);
    const search = doc.querySelector('#filterSearch');
    search.value = '按';
    fire(search, 'input', { target: search });
    ok('搜索缩小结果', items().length > 0 && items().length < 24, items().length);
    search.value = 'zzzz';
    fire(search, 'input', { target: search });
    ok('无结果空态', byClass(flist, 'm3-filter-empty').length === 1);
    search.value = '';
    fire(search, 'input', { target: search });
    const chips = byClass(doc.querySelector('#filterChips'), 'm3-chip');
    ok('分类 chip 已渲染', chips.length >= 5, chips.length);
    if (chips[2]) {
      const label = chips[2].textContent;
      chips[2].click();
      const fresh = byClass(doc.querySelector('#filterChips'), 'm3-chip');
      const active = fresh.filter(c => c.classList.contains('selected'));
      ok('分类筛选生效并高亮',
        active.length === 1 && active[0].textContent === label,
        active.map(c => c.textContent).join(','));
    }
  }

  const kc = doc.querySelector('#keycap');
  ok('快捷键录制区存在', !!kc);
  if (kc) {
    kc.click();
    ok('进入录制态', kc.classList.contains('listening'));
    fire(kc, 'keydown', {
      key: 'k', ctrlKey: true, shiftKey: true,
      preventDefault() {}, stopPropagation() {},
    });
    ok('解析为 Ctrl + Shift + K',
      doc.querySelector('#kcResult').textContent.indexOf('Ctrl + Shift + K') >= 0,
      doc.querySelector('#kcResult').textContent);
    ok('退出录制态', !kc.classList.contains('listening'));
  }
})();

group('缩放自适应');
(function () {
  ok('m3Zoom 始终暴露', !!window.m3Zoom);
  if (window.m3Zoom) {
    const st = window.m3Zoom.state();
    ok('state 字段完整',
      'supported' in st && 'scale' in st && 'compensating' in st);
    ok('未缩放时不误加 data-zoom-out',
      !doc.documentElement.hasAttribute('data-zoom-out'));
  }
})();

group('动态重建后键盘支持仍在');
(function () {
  const inbox = doc.querySelector('#inbox');
  ok('收件箱存在', !!inbox);
  if (inbox) {
    const star = byClass(inbox, 'm3-inbox-star')[0];
    if (star) {
      star.click();
      const chips = byClass(inbox, 'm3-chip')
        .filter(c => !c.classList.contains('m3-chip--static'));
      ok('重建后 chip 仍可聚焦',
        chips.every(c => c.getAttribute('tabindex') !== null),
        chips.filter(c => c.getAttribute('tabindex') === null).length + ' 个丢失');
    }
  }
})();

/* ---------------------------------------------------------------- */
console.log('');
console.log('通过 ' + passed + ' 项' + (failed ? '，失败 ' + failed + ' 项' : ''));
if (failed) {
  console.log('❌ 有失败项');
  process.exit(1);
}
console.log('✅ 全部通过');
process.exit(0);
