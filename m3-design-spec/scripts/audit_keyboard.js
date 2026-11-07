#!/usr/bin/env node
/*
 * audit_keyboard.js — 找出键盘用户到不了的点击目标。
 *
 * 通过 dom_harness.js 加载页面，枚举所有带 click 监听但不可聚焦的元素。
 * 这是最便宜、最有效的键盘回归测试：被它点名的元素，纯键盘用户一定够不到。
 *
 * 用法：
 *   node audit_keyboard.js <page.html> [--all]
 *
 * 退出码：
 *   0  没有需要修的问题
 *   1  有需要修的问题
 *   2  输入不可用
 *
 * 期望例外（会列出但不计为失败）：
 *   - 遮罩（scrim）：点遮罩关闭只是便利，Esc 才是真正的可访问方式
 *   - 禁用按钮：本就不该可聚焦
 */

const path = require('path');
const H = require(path.join(__dirname, 'dom_harness.js'));

const uri = process.argv[2] || process.env.M3_PAGE;
const showAll = process.argv.indexOf('--all') >= 0;

if (!uri) {
  console.error('用法: node audit_keyboard.js <page.html> [--all]');
  process.exit(2);
}

const { doc, loadError } = H;
if (loadError) {
  console.error('页面加载期异常，无法审计：');
  console.error('  ' + loadError.message);
  process.exit(1);
}

const all = [];
(function walk(el) { all.push(el); (el._children || []).forEach(walk); })(doc);

function focusable(el) {
  if (el.hasAttribute('tabindex')) return true;
  const t = el.tagName;
  if (t === 'BUTTON' || t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') {
    return el._attrs.disabled === undefined;
  }
  if (t === 'A' && el._attrs.href !== undefined) return true;
  return false;
}

function classify(el) {
  const cls = (el.className || '').trim();
  if (/m3-(cmdk-|keys-)?scrim/.test(cls)) return 'scrim';
  if (el._attrs.disabled !== undefined) return 'disabled';
  if (el.tagName === '#DOCUMENT') return 'document';
  return 'needs-fix';
}

const buckets = { scrim: [], disabled: [], document: [], 'needs-fix': [] };
all.forEach(function (el) {
  if (!(el._listeners && el._listeners.click)) return;
  if (focusable(el)) return;
  buckets[classify(el)].push(el);
});

console.log('键盘可达性审计: ' + uri);
console.log('');

const expected = buckets.scrim.length + buckets.disabled.length + buckets.document.length;
console.log('有 click 但不可聚焦: ' + (expected + buckets['needs-fix'].length) +
  ' 个（其中 ' + expected + ' 个是期望例外）');

if (showAll || expected) {
  ['scrim', 'disabled', 'document'].forEach(function (kind) {
    if (!buckets[kind].length) return;
    console.log('');
    console.log('  [期望例外 · ' + kind + '] ' + buckets[kind].length + ' 个');
    buckets[kind].forEach(function (el) {
      const label = (el.textContent || '').trim().slice(0, 30);
      console.log('    ' + (el.className || el.tagName) + (label ? '  「' + label + '」' : ''));
    });
  });
}

console.log('');
if (buckets['needs-fix'].length) {
  console.log('❌ 需要修复 · ' + buckets['needs-fix'].length + ' 个');
  buckets['needs-fix'].forEach(function (el) {
    const label = (el.textContent || '').trim().slice(0, 40);
    console.log('  class   = ' + ((el.className || '').trim() || '(无)'));
    console.log('  text    = ' + JSON.stringify(label));
    console.log('  role    = ' + (el._attrs.role || '无') +
                '   tabindex = ' + (el._attrs.tabindex || '无'));
    console.log('  → 补 tabindex="0" + role + Enter/Space 处理，或改用 <button>');
    console.log('');
  });
  process.exit(1);
}

console.log('✅ 无未预期的不可聚焦点击目标');
process.exit(0);
