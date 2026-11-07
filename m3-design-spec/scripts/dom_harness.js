#!/usr/bin/env node
/*
 * dom_harness.js — 在 Node 里真实执行单文件 HTML 页面的脚本，用于捕获运行时错误。
 *
 * 为什么需要它：静态检查只能发现语法与引用问题，抓不到「加载期抛异常」和
 * 「逻辑写错导致死循环」这类缺陷。这个 harness 解析 HTML 建 DOM 树，
 * 注入最小浏览器 API，然后执行页面 <script>，于是可以在没有浏览器的
 * 环境里跑真实的点击 / 指针事件测试。
 *
 * 用法：
 *   node dom_harness.js <page.html>          # 只报告加载期异常
 *   # 或在测试脚本里：
 *   const H = require('/skills/m3-design-spec/scripts/dom_harness.js');
 *   const { doc, win, fire, El, loadError } = H;
 *
 * 页面路径来自 process.argv[2] 或环境变量 M3_PAGE。
 *
 * 几个必须正确实现的细节（都踩过坑）：
 *   - 闭合标签匹配必须统一大小写，否则栈永不弹出，整棵树嵌套错乱。
 *   - focus() 必须更新 document.activeElement，否则键盘测试全是假的。
 *   - tabIndex 是反射属性，赋值要写入 tabindex 特性。
 *   - innerHTML 赋值会清空子元素。
 *   - <input value="…"> 要把特性反射到 value 属性。
 *
 * 能力边界：这不是浏览器。Canvas 是桩、布局尺寸是常量、观察器是空实现。
 * 适合验证逻辑与异常，不适合验证视觉与布局。
 */

const fs = require('fs');

const VOID = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
  'param', 'source', 'track', 'wbr',
  'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', 'use',
  'stop', 'animate',
]);

/* ---------- classList ---------- */
class ClassList {
  constructor(el) { this.el = el; }
  get _set() {
    const c = this.el._attrs.class;
    return new Set(c ? c.split(/\s+/).filter(Boolean) : []);
  }
  _write(s) { this.el._attrs.class = Array.from(s).join(' '); }
  contains(c) { return this._set.has(c); }
  add(...cs) { const s = this._set; cs.forEach(c => s.add(c)); this._write(s); }
  remove(...cs) { const s = this._set; cs.forEach(c => s.delete(c)); this._write(s); }
  toggle(c, force) {
    const s = this._set;
    const on = force === undefined ? !s.has(c) : !!force;
    if (on) s.add(c); else s.delete(c);
    this._write(s);
    return on;
  }
}

/* ---------- style ---------- */
function makeStyle() {
  const store = {};
  const target = {
    setProperty(k, v) { store[k] = String(v); },
    getPropertyValue(k) { return store[k] || ''; },
    removeProperty(k) { delete store[k]; },
    get cssText() { return Object.keys(store).map(k => k + ':' + store[k]).join(';'); },
    set cssText(v) {
      String(v).split(';').forEach(p => {
        const i = p.indexOf(':');
        if (i > 0) store[p.slice(0, i).trim()] = p.slice(i + 1).trim();
      });
    },
  };
  return new Proxy(target, {
    get(t, k) { return k in t ? t[k] : (store[k] === undefined ? '' : store[k]); },
    set(t, k, v) { if (k in t) { t[k] = v; } else { store[k] = String(v); } return true; },
  });
}

/* ---------- element ---------- */
class El {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();   // 统一大写；闭合匹配也必须大写
    this._attrs = {};
    this._children = [];
    this._parent = null;
    this._listeners = {};
    this._text = '';
    this._html = '';
    this.classList = new ClassList(this);
    this.style = makeStyle();
    this.disabled = false;
    this.value = '';
    this.files = null;
    this._dataset = new Proxy({}, {
      get: (t, k) => this._attrs['data-' + String(k).replace(/[A-Z]/g, m => '-' + m.toLowerCase())],
      set: (t, k, v) => { this._attrs['data-' + String(k)] = String(v); return true; },
    });
    this.dataset = this._dataset;
  }

  get className() { return this._attrs.class || ''; }
  set className(v) { this._attrs.class = String(v); }

  get id() { return this._attrs.id || ''; }
  set id(v) { this._attrs.id = String(v); }
  set title(v) { this._attrs.title = String(v); }
  get title() { return this._attrs.title || ''; }
  set type(v) { this._attrs.type = String(v); }
  get type() { return this._attrs.type || ''; }
  set src(v) { this._attrs.src = String(v); }
  get src() { return this._attrs.src || ''; }
  set href(v) { this._attrs.href = String(v); }
  get href() { return this._attrs.href || ''; }
  set htmlFor(v) { this._attrs['for'] = String(v); }
  get htmlFor() { return this._attrs['for'] || ''; }

  // 反射属性：写特性，读也读特性
  get tabIndex() {
    const v = this._attrs.tabindex;
    if (v === undefined) {
      // 真实 DOM 里原生可聚焦元素默认 tabIndex 为 0，其余为 -1
      const t = this.tagName;
      if (t === 'BUTTON' || t === 'INPUT' || t === 'SELECT' || t === 'TEXTAREA') {
        return this._attrs.disabled === undefined ? 0 : -1;
      }
      if (t === 'A' && this._attrs.href !== undefined) return 0;
      return -1;
    }
    const n = parseInt(v, 10);
    return isNaN(n) ? -1 : n;
  }
  set tabIndex(v) { this._attrs.tabindex = String(v); }

  get checked() { return !!this._checked; }
  set checked(v) { this._checked = !!v; }

  get textContent() { return this._text; }
  set textContent(v) { this._text = String(v); }

  get innerHTML() { return this._html; }
  set innerHTML(v) {
    this._html = String(v);
    // 真实 DOM 里给 innerHTML 赋值会先清空子元素。
    // 不复现这一点，innerHTML = '' 就无法移除旧节点，测试结果会失真。
    this._children.forEach(c => { c._parent = null; });
    this._children = [];
  }

  get parentNode() { return this._parent || null; }
  get parentElement() { return this._parent || null; }
  get children() { return this._children; }
  get childNodes() { return this._children; }
  get firstChild() { return this._children[0] || null; }
  get lastChild() { return this._children[this._children.length - 1] || null; }
  get firstElementChild() { return this._children[0] || null; }
  get nextSibling() {
    if (!this._parent) return null;
    const s = this._parent._children;
    return s[s.indexOf(this) + 1] || null;
  }
  get previousSibling() {
    if (!this._parent) return null;
    const s = this._parent._children, i = s.indexOf(this);
    return i > 0 ? s[i - 1] : null;
  }
  get nodeType() { return this.tagName === '#TEXT' ? 3 : (this.tagName === '#DOCUMENT' ? 9 : 1); }
  get isConnected() { let n = this; while (n) { if (n === doc) return true; n = n._parent; } return false; }
  get ownerDocument() { return doc; }
  get offsetWidth() { return 100; }
  get offsetHeight() { return 40; }
  get clientWidth() { return 300; }
  get clientHeight() { return 200; }
  get offsetParent() { return this._parent || null; }
  get scrollTop() { return this._scrollTop || 0; }
  set scrollTop(v) { this._scrollTop = v; }
  get scrollHeight() { return 800; }
  get scrollLeft() { return this._scrollLeft || 0; }
  set scrollLeft(v) { this._scrollLeft = v; }

  getAttribute(n) { return this._attrs[n] !== undefined ? this._attrs[n] : null; }
  getAttributeNames() { return Object.keys(this._attrs); }
  setAttribute(n, v) { this._attrs[n] = String(v); }
  hasAttribute(n) { return this._attrs[n] !== undefined; }
  removeAttribute(n) { delete this._attrs[n]; }

  appendChild(c) { c._parent = this; this._children.push(c); return c; }
  insertBefore(c, ref) {
    const i = ref ? this._children.indexOf(ref) : -1;
    c._parent = this;
    if (i >= 0) this._children.splice(i, 0, c); else this._children.push(c);
    return c;
  }
  replaceChild(n, o) {
    const i = this._children.indexOf(o);
    if (i >= 0) { this._children[i] = n; n._parent = this; o._parent = null; }
    return o;
  }
  removeChild(c) {
    const i = this._children.indexOf(c);
    if (i >= 0) this._children.splice(i, 1);
    c._parent = null;
    return c;
  }
  remove() { if (this._parent) this._parent.removeChild(this); }
  contains(node) { let n = node; while (n) { if (n === this) return true; n = n._parent; } return false; }
  insertAdjacentHTML(pos, html) { this._html = (this._html || '') + html; }
  insertAdjacentElement() { return null; }
  before() {} after() {} prepend() {} append() {} normalize() {}

  getBoundingClientRect() { return { left: 0, top: 0, right: 1200, bottom: 800, width: 1200, height: 800, x: 0, y: 0 }; }
  getClientRects() { return [{ left: 0, top: 0, width: 1200, height: 800 }]; }
  setPointerCapture() {}
  releasePointerCapture() {}
  focus() { doc.activeElement = this; }
  blur() { if (doc.activeElement === this) doc.activeElement = bodyEl; }
  select() {}
  setSelectionRange() {}
  scrollIntoView() {}
  scrollTo() {}
  animate() { return { cancel() {}, finished: Promise.resolve() }; }
  matches(sel) { return matchesSel(this, sel); }
  closest(sel) { let n = this; while (n) { if (matchesSel(n, sel)) return n; n = n._parent; } return null; }
  querySelector(sel) { return queryAll(this, sel)[0] || null; }
  querySelectorAll(sel) { return queryAll(this, sel); }
  getElementsByClassName(c) { return queryAll(this, '.' + c); }
  getElementsByTagName(t) { return queryAll(this, t); }
  addEventListener(t, fn) { (this._listeners[t] = this._listeners[t] || []).push(fn); }
  removeEventListener(t, fn) {
    const l = this._listeners[t];
    if (!l) return;
    const i = l.indexOf(fn);
    if (i >= 0) l.splice(i, 1);
  }
  dispatchEvent(e) { fire(this, e.type, e); return true; }
  click() { fire(this, 'click', {}); }
}

/* ---------- 选择器引擎 ---------- */
function matchSimple(el, s) {
  s = String(s).trim();
  if (!s) return true;
  if (s === '*') return true;

  const nots = [];
  s = s.replace(/:not\(([^)]*)\)/g, (m, inner) => { nots.push(inner); return ''; });

  let needChecked = false;
  if (s.includes(':checked')) { needChecked = true; s = s.replace(/:checked/g, ''); }
  s = s.replace(/:(focus-visible|focus|hover|active|disabled|first-child|last-child)/g, '');
  if (needChecked && !(el.checked || 'checked' in el._attrs)) return false;
  for (const n of nots) if (matchSimple(el, n)) return false;

  const re = /([#.]?[A-Za-z0-9_-]+)|\[([A-Za-z0-9_-]+)(?:([~|^$*]?=)"?([^\]"]*)"?)?\]/g;
  let m, ok = true, any = false;
  while ((m = re.exec(s))) {
    any = true;
    if (m[1] !== undefined) {
      const tok = m[1];
      if (tok.startsWith('#')) { if (el.id !== tok.slice(1)) ok = false; }
      else if (tok.startsWith('.')) { if (!el.classList.contains(tok.slice(1))) ok = false; }
      else { if (el.tagName !== tok.toUpperCase()) ok = false; }
    } else {
      const have = el._attrs[m[2]];
      if (m[4] === undefined) { if (have === undefined) ok = false; }
      else if (String(have) !== m[4]) ok = false;
    }
    if (!ok) return false;
  }
  return any ? ok : true;
}

// 从右向左匹配，支持后代（空格）与子代（>）
function matchChain(el, tokens) {
  if (!tokens.length) return true;
  const last = tokens[tokens.length - 1];
  if (last === '>' || last === '+' || last === '~') return false;
  if (!matchSimple(el, last)) return false;

  let i = tokens.length - 2, cur = el;
  while (i >= 0) {
    const tok = tokens[i];
    if (tok === '>') {
      i--;
      if (i < 0) return true;
      const p = cur._parent;
      if (!p || !matchSimple(p, tokens[i])) return false;
      cur = p; i--;
    } else if (tok === '+' || tok === '~') {
      return false;
    } else {
      let p = cur._parent, found = false;
      while (p) { if (matchSimple(p, tok)) { found = true; break; } p = p._parent; }
      if (!found) return false;
      cur = p; i--;
    }
  }
  return true;
}

function matchesSel(el, sel) {
  const groups = String(sel).split(',').map(g => g.trim()).filter(Boolean);
  for (const g of groups) {
    const tokens = g.replace(/\s*>\s*/g, ' > ').replace(/\s+/g, ' ').split(' ').filter(Boolean);
    if (matchChain(el, tokens)) return true;
  }
  return false;
}

function walk(el, out) { out.push(el); el._children.forEach(c => walk(c, out)); return out; }
function queryAll(root, sel) {
  const all = [];
  root._children.forEach(c => walk(c, all));
  return all.filter(el => matchesSel(el, sel));
}

/* ---------- 事件 ---------- */
let WINDOW = null;
function fire(target, type, props) {
  const ev = Object.assign({
    type, target, currentTarget: target, defaultPrevented: false,
    preventDefault() { this.defaultPrevented = true; },
    stopPropagation() { this._stopped = true; },
  }, props);
  let node = target;
  while (node) {
    const l = node._listeners && node._listeners[type];
    if (l) l.slice().forEach(fn => fn.call(node, ev));
    if (ev._stopped) break;
    node = node._parent;
  }
  if (!ev._stopped && WINDOW) {
    const l = WINDOW._listeners && WINDOW._listeners[type];
    if (l) l.slice().forEach(fn => fn.call(WINDOW, ev));
  }
  return ev;
}

/* ---------- Canvas 2D 桩 ---------- */
function makeCtx(canvas) {
  return {
    canvas,
    save() {}, restore() {}, setTransform() {}, resetTransform() {},
    clearRect() {}, fillRect() {}, strokeRect() {}, beginPath() {}, closePath() {},
    arc() {}, rect() {}, ellipse() {}, moveTo() {}, lineTo() {}, fill() {}, stroke() {},
    translate() {}, rotate() {}, scale() {}, drawImage() {}, setLineDash() {}, fillText() {},
    clip() {}, quadraticCurveTo() {}, bezierCurveTo() {},
    createRadialGradient() { return { addColorStop() {} }; },
    createLinearGradient() { return { addColorStop() {} }; },
    createPattern() { return {}; },
    measureText() { return { width: 10 }; },
    getImageData(x, y, w, h) { return { data: new Uint8ClampedArray(Math.max(0, w * h * 4)), width: w, height: h }; },
    putImageData() {},
    globalAlpha: 1, globalCompositeOperation: 'source-over',
    fillStyle: '', strokeStyle: '', lineWidth: 1, lineJoin: '', lineCap: '',
    font: '', textBaseline: '', filter: '', shadowBlur: 0, shadowColor: '',
  };
}

/* ---------- 构建文档 ---------- */
const doc = new El('#document');
const win = new El('#window');
WINDOW = win;
doc.defaultView = win;
doc.documentElement = new El('html');
const bodyEl = new El('body');

doc.getElementById = function (id) { return queryAll(doc, '#' + id)[0] || null; };
doc.getElementsByClassName = function (c) { return queryAll(doc, '.' + c); };
doc.getElementsByTagName = function (t) { return queryAll(doc, t); };
doc.contains = function (el) { let n = el; while (n) { if (n === doc) return true; n = n._parent; } return false; };
doc.addEventListener = El.prototype.addEventListener.bind(doc);
doc.removeEventListener = El.prototype.removeEventListener.bind(doc);
doc.querySelector = El.prototype.querySelector.bind(doc);
doc.querySelectorAll = El.prototype.querySelectorAll.bind(doc);
doc.execCommand = function () { return true; };
doc.createTextNode = function (t) { const e = new El('#text'); e.textContent = t; return e; };
doc.createDocumentFragment = function () { return new El('#fragment'); };
doc.createElement = function (tag) {
  const el = new El(tag);
  if (String(tag).toLowerCase() === 'canvas') {
    el.width = 300; el.height = 150;
    const ctx = makeCtx(el);
    el.getContext = function () { return ctx; };
    el.toDataURL = function () { return 'data:image/png;base64,AAAA'; };
    el.toBlob = function (cb) { cb({}); };
  }
  return el;
};
// SVG 命名空间创建：多数实现里与 createElement 等价，但必须存在，
// 否则任何画 SVG 的代码都会在加载期抛错。
doc.createElementNS = function (ns, tag) { return doc.createElement(tag); };
doc.body = bodyEl;
doc.activeElement = bodyEl;
doc.documentElement._parent = doc;
doc.appendChild(doc.documentElement);
doc.documentElement.appendChild(new El('head'));
doc.documentElement.appendChild(bodyEl);

/* ---------- 解析 body ---------- */
let PAGE = process.argv[2] || process.env.M3_PAGE;
let SRC = null;

function parseInto(html, parent) {
  const re = /<!--[\s\S]*?-->|<(\/?)([a-zA-Z0-9-]+)((?:\s+[^\s=>/]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?)*)\s*(\/?)>|([^<]+)/g;
  let m;
  const stack = [parent];
  while ((m = re.exec(html))) {
    if (m[0].startsWith('<!--')) continue;

    if (m[5] !== undefined) {                     // 文本
      const t = m[5].trim();
      if (t) stack[stack.length - 1]._text += t;
      continue;
    }

    const closing = m[1] === '/';
    const tag = m[2].toLowerCase();
    const attrs = m[3] || '';
    const selfClose = m[4] === '/';

    if (closing) {
      // tagName 统一大写，比较也必须大写，否则栈永不弹出
      const tagU = tag.toUpperCase();
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].tagName === tagU) { stack.length = i; break; }
      }
      continue;
    }

    const el = doc.createElement(tag);
    const are = /([^\s=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
    let a;
    while ((a = are.exec(attrs))) {
      if (a[1] === '/') continue;
      el._attrs[a[1]] = a[2] !== undefined ? a[2] : (a[3] !== undefined ? a[3] : (a[4] !== undefined ? a[4] : ''));
    }
    // 特性要反射到属性，真实 DOM 就是这样初始化的
    if (el.tagName === 'INPUT' && 'checked' in el._attrs) el.checked = true;
    if ((el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && 'value' in el._attrs) {
      el.value = el._attrs.value;
    }
    stack[stack.length - 1].appendChild(el);
    if (!VOID.has(tag) && !selfClose) stack.push(el);
  }
}

/* ---------- 全局对象 ---------- */
global.document = doc;
global.window = win;
Object.assign(global, { document: doc, window: win });
global.devicePixelRatio = win.devicePixelRatio = 1;
win.innerWidth = 412;
win.innerHeight = 900;
global.innerWidth = win.innerWidth;
global.innerHeight = win.innerHeight;
win.matchMedia = function (q) {
  return { matches: false, media: q, addEventListener() {}, addListener() {}, removeEventListener() {} };
};
win.requestAnimationFrame = function (fn) { setTimeout(fn, 0); return 0; };
global.requestAnimationFrame = win.requestAnimationFrame;
win.cancelAnimationFrame = function () {};
global.cancelAnimationFrame = win.cancelAnimationFrame;
win.getComputedStyle = function () {
  // 返回空样式对象；需要读令牌的代码应带兜底
  return { getPropertyValue() { return ''; } };
};
global.getComputedStyle = win.getComputedStyle;
win.scrollTo = function () {};
global.scrollTo = win.scrollTo;
global.scroll = win.scrollTo;
win.setTimeout = setTimeout;
win.clearTimeout = clearTimeout;
win.addEventListener = El.prototype.addEventListener.bind(win);
win.removeEventListener = El.prototype.removeEventListener.bind(win);

global.FileReader = class { readAsDataURL() {} };
global.Image = class { constructor() { this.width = 100; this.height = 100; } };
global.URL = global.URL || { createObjectURL() { return 'blob:x'; }, revokeObjectURL() {} };
global.Blob = global.Blob || class { constructor() {} };
global.matchMedia = win.matchMedia;
global.alert = function () {};
global.confirm = function () { return true; };
global.getSelection = function () {
  return { toString() { return ''; }, removeAllRanges() {}, addRange() {} };
};
global.navigator = {
  userAgent: 'node',
  clipboard: { writeText() { return Promise.resolve(); } },
};

/* 观察器桩：必须在执行页面脚本之前注入 */
class NoopObserver {
  constructor(cb) { this.cb = cb; }
  observe() {} unobserve() {} disconnect() {} takeRecords() { return []; }
}
global.MutationObserver = NoopObserver;
global.IntersectionObserver = NoopObserver;
global.ResizeObserver = NoopObserver;
global.requestIdleCallback = function (fn) { setTimeout(fn, 0); return 0; };
global.cancelIdleCallback = function () {};

/* ---------- 执行页面脚本 ---------- */
let loadError = null;

function load(pagePath) {
  if (!pagePath) {
    console.error('用法: node dom_harness.js <page.html>');
    console.error('   或在代码里设置 M3_PAGE 环境变量后 require');
    process.exit(2);
  }
  PAGE = pagePath;
  SRC = fs.readFileSync(pagePath, 'utf8');

  const bodyStart = SRC.indexOf('<body');
  const bodyOpen = SRC.indexOf('>', bodyStart) + 1;
  const bodySrc = SRC.slice(bodyOpen, SRC.lastIndexOf('<script'));
  parseInto(bodySrc, bodyEl);

  const scriptMatch = SRC.match(/<script[^>]*>([\s\S]*?)<\/script>/);
  if (scriptMatch) {
    try {
      new Function(
        'window', 'document', 'requestAnimationFrame', 'performance',
        'setTimeout', 'clearTimeout', 'FileReader', 'Image', 'URL', 'Blob', 'navigator',
        scriptMatch[1]
      )(
        win, doc, win.requestAnimationFrame, global.performance, setTimeout, clearTimeout,
        global.FileReader, global.Image, global.URL, global.Blob, global.navigator
      );
    } catch (e) {
      loadError = e;
    }
  }
}

if (PAGE) load(PAGE);

module.exports = {
  doc, win, fire, El, loadError, bodyEl, queryAll, matchesSel,
  load, get pagePath() { return PAGE; },
};

/* 直接执行时，报告加载结果 */
if (require.main === module) {
  if (!PAGE) {
    console.error('用法: node dom_harness.js <page.html>');
    process.exit(2);
  }
  console.log('页面      :', PAGE);
  if (loadError) {
    console.log('结果      : ❌ 加载期异常');
    console.log('  ' + loadError.message);
    (loadError.stack || '').split('\n').slice(1, 6).forEach(l => console.log('  ' + l.trim()));
    process.exit(1);
  }
  console.log('结果      : ✅ 加载期无异常');
  console.log('元素总数  :', queryAll(doc, '*').length);
}
