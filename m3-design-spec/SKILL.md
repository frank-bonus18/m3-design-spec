---
name: m3-design-spec
description: >-
  Build, extend, or review Material 3 (Material You / Android 13) HTML UI in a single
  self-contained file: M3 semantic color tokens for light and dark, tonal palettes,
  ripple feedback, elevation, rounded corners, and reusable components. Use when the
  user asks for a Material 3 / Material You / Android 13 / M3 style page, component
  library, design spec, or design system in HTML; when they want dark mode driven by
  CSS variables; or when they want to add M3 components such as filled buttons, FABs,
  cards, text fields, switches, chips, navigation bars, dialogs, bottom sheets,
  snackbars, sliders, tabs, tables, or pickers.
triggers: ["M3", "MD3", "Material 3", "Material You", "Material Design", "Material风格", "M3风格", "安卓13", "Android 13", "谷歌设计", "组件库", "设计规范", "设计系统", "设计令牌", "配色令牌", "暗色模式", "深色模式", "动态取色", "水波纹", "FAB", "底部抽屉", "对话框"]
compatibility: >-
  A writable workspace is needed to save output and to run scripts (python3 for
  check_m3_html.py; node for the harness, the audit and the regression suite).
---

# Material 3 Design Spec

Produce Material 3 UI as one self-contained HTML file: inline `<style>`, inline `<script>`, no CDN, no build step. Colors come only from CSS custom properties so light/dark switching is a variable swap.

Name the artifact with a `.html` extension and keep it openable by double-click (`file://`).

## Non-negotiable rules

1. **Never hardcode a color in a component rule.** Every value must be `var(--token)`. One hardcoded hex breaks dark mode. Colors inside a decorative `gradient()` are the sole exception.
2. **Define the full token set twice**: `:root` for light and `[data-theme="dark"]` for dark, with dark as a complete counterpart (same variable names, no missing keys).
3. **Dark mode is a variable swap only.** Never write separate component rules for dark.
4. **No theme persistence** unless the user asks for it. Default: a checkbox toggles `data-theme` on `<html>`; refresh returns to light.
5. **Ripple via event delegation**, one `pointerdown` listener on `document`, so dynamically created nodes get ripples for free. Never bind a ripple listener per element.
6. **Rounded corners and shadows come from constants** (`--radius-*`, `--shadow-1..5`), not literals in component rules.
7. **Global transition** on `background-color`, `color`, `border-color`, `box-shadow` so theme switching fades instead of snapping.
8. Use `<button>` and `<input>` for interaction so keyboard access and focus rings work without extra code.
9. **Never use an emoji as a functional icon.** Icons are inline `<svg>` with `fill="currentColor"`. This applies to your own output, not just to what you ask the user for. An emoji is acceptable only as decoration — a card media placeholder or an empty-state illustration — and even then it needs `aria-hidden="true"`, or `role="img"` plus `aria-label` if it carries meaning. Never inside a `<button>`, a menu item, a list leading slot, or any control.

## Workflow

1. **Clarify only what you cannot infer.** Seed color, which components are needed, single page or library page, label language. If the user showed a reference file, reuse its structure.
2. **Pick the starting point.**
   - New page → follow the structure below and write the token block yourself.
   - Extend an existing M3 page → edit it in place; do not re-scaffold.
   - Need a large library fast → copy the reference implementation, then edit:
     `cp /skills/m3-design-spec/assets/m3-component-library.html <workspace>/<name>.html`
     It is ~11,000 lines; grep for the section you need instead of reading it whole.
3. **Write the token block first**, then components, then interactions.
4. **Validate** — run all four scripts (see Scripts). Fix everything they report.
5. **Report** the file path, component list, and any deviation from M3.

## File structure to emit

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#0058A8">
<title>…</title>
<style>
/* 1. light tokens        :root { … } */
/* 2. dark tokens         [data-theme="dark"] { … } */
/* 3. reset + global transition + ripple keyframes */
/* 4. components, grouped by M3 family:
      buttons → FAB → cards → chips → text fields → selection →
      navigation → progress → overlays */
/* 5. responsive: max-width AND min-width breakpoints
     @media (prefers-reduced-motion:reduce) */
</style>
</head>
<body>…</body>
<script>(function(){ 'use strict'; … })();</script>
</html>
```

Wrap all JS in one IIFE with `'use strict'`.

## Layout conventions

- Content column: `max-width: 440px; margin: 0 auto`, vertical flex with `gap` around 20px.
- Wide screens add a sticky navigation rail (`88px`) beside the column; hide it under 900px.
- Keep bottom padding generous (~140px) so fixed FABs never cover the last row.
- **A phone-only layout is a defect.** Always ship `min-width` upgrades; see Responsive requirements.

## Component rules that are easy to get wrong

- **Floating label text fields** need `placeholder=" "` (a single space). The label relies on `:not(:placeholder-shown)`.
- **Expansion panels** animate via `grid-template-rows: 0fr → 1fr`, which requires the body to contain exactly one wrapper `<div>`.
- **Buttons**: filled = `--primary` on `--on-primary`; tonal = `--secondary-container` on `--on-secondary-container`; elevated = `--surface-container-low` + `--shadow-1`; outlined = 1px `--outline`; text = transparent.
- **Selected states** use the *container* pair: selected chip / nav item / tab indicator = `--secondary-container` fill with `--on-secondary-container` content.
- **Disabled** = foreground at 38%, container at 12%. Do not just lower `opacity` on the whole element; that fades the shape too.
- **Ripple color** must contrast with what it sits on: on a filled surface use the `on-*` color, on a transparent surface the accent itself. Set `--ripple-color`.
- **Overlays** share one scrim and one open slot; only one open at a time. Support scrim click, `Escape`, and autofocus of the first actionable element.
- **Snackbars** use `--inverse-surface` / `--inverse-on-surface`, auto-dismiss ~3s, optional action.
- **Decorative chips** (badges, status, category) need a static marker such as `.m3-chip--static` and must be excluded from roving tabindex — otherwise keyboard users tab through every label.
- **Notification stacks** must keep their own queue. `while (box.children.length >= MAX) dismiss(box.children[0])` hangs forever because `dismiss` removes asynchronously; splice your queue before animating out.

## Keyboard-first requirements

Any page you build must be operable without a pointer. This is an acceptance bar, not polish.

- **One Tab stop per composite widget.** Tabs, chips, radios, segmented buttons, carousels, dates, trees and listboxes get a single roving `tabindex="0"`, moved with arrow keys.
- **Every click target is focusable.** No clickable `<div>`/`<span>` without `tabindex="0"`, a `role`, and an Enter/Space handler.
- **No global shortcut fires while typing.** Guard on `input`/`textarea`/`select`/`contenteditable`. `Escape` is the only exception.
- **`Escape` closes the innermost open thing** and returns focus to whatever opened it.
- **Focus survives re-renders.** Move focus to the logical successor when a render replaces the focused node.
- **Delegate keys** for anything re-created at runtime; per-node listeners die silently on re-render. Re-run one idempotent `enhanceA11y(root)` after each render, guarded by a flag.
- **Expose a registry** when the page has global shortcuts, so bindings have one source of truth and can be rendered as help, tested, or invoked programmatically.

## Responsive requirements

- **Ship at least one `min-width` breakpoint.** A fixed reading column with no wide upgrade leaves content floating in whitespace on tablets, desktops and landscape phones — it reads as broken even though nothing errored. Widen progressively (440 → ~560 → ~680) and stop around 760–820px so line length stays readable.
- **Never block zoom.** No `user-scalable=no`, no `maximum-scale=1` — that fails WCAG 1.4.4. When a user pinches out, the layout viewport keeps its width and the browser shows blank canvas beyond the document; CSS cannot remove that, and the cure (blocking zoom) is worse than the symptom. If the user insists, implement a `visualViewport` compensation that scales the page up when `scale < 1`, keeping zoom enabled.
- **Guard horizontal overflow** with `overflow-x: clip` on `html`. Prefer `clip` over `hidden`: `clip` does not create a scroll container, so `position: sticky` keeps resolving against the viewport. Off-screen overlays (`translateX(±105%)`) are counted as scrollable overflow by some WebViews.
- **Set the root background** on both `html` and `body`, and use `min-height: 100dvh` with a `100vh` fallback.

## Reference files

Read these only when the task needs the detail.

- [Token tables](references/tokens.md) — every semantic color for light and dark plus all constants, extracted verbatim from the reference implementation. Read before writing the token block or when a specific color role is needed.
- [Component catalog](references/components.md) — class names, minimal markup, interaction patterns (ripple delegation, overlay state machine, `data-*` hooks, gestures). Read when adding or extending a component.
- [Keyboard and automation](references/keyboard.md) — per-component key maps, roving tabindex, prefix sequences, focus restoration, the re-runnable enhancer, the focusable-anything test, and the `window.m3Keys` registry an agent can enumerate and invoke.

Do not restate the token tables from memory; the values are exact and pairing-sensitive.

## Assets

- `/skills/m3-design-spec/assets/m3-component-library.html` — the reference implementation: ~11,000 lines, 72 tokens, 298 `m3-*` classes, 24 sections covering buttons, FABs, cards, chips, fields, selection, navigation, progress, overlays, pickers, tables, gestures, auth forms, keyboard-first components, and spec-visualisation widgets. Fully keyboard operable, exposes `window.m3Keys`, `window.m3Contrast`, `window.m3Zoom`. Copy it and edit, or grep it to match an existing convention. Never paste it wholesale into chat.
- `/skills/m3-design-spec/assets/full-spec-doc.md` — the human-readable spec document for that implementation. Use when the user wants documentation rather than code.

## Scripts

Four scripts. Run all of them after every edit.

### Static check

`/skills/m3-design-spec/scripts/check_m3_html.py`

```
python3 /skills/m3-design-spec/scripts/check_m3_html.py path/to/page.html [--verbose]
```

Checks tag balance, duplicate `id`s, `<script>` syntax (when `node` exists), every id and class the JS references (runtime-created classes count as known), hex colors outside the token blocks, both token blocks with every semantic color mirrored (`theme-invariant` marks intentional constants), ripple presence, and accessibility blockers: missing `lang`, missing or dangling skip link, buttons with no accessible name, overlays without `role` / `aria-modal`, no live region, no reduced-motion fallback, no `:focus-visible`, emoji used as a functional icon. Also checks responsiveness: viewport present, zoom not blocked, at least one `min-width` breakpoint.

Exit 0 = clean, 1 = findings, 2 = unusable input.

### Runtime harness

`/skills/m3-design-spec/scripts/dom_harness.js`

```
node /skills/m3-design-spec/scripts/dom_harness.js path/to/page.html
```

Parses the page's HTML into a minimal DOM, injects the browser APIs the script expects, and executes it. Catches load-time exceptions and lets you drive real clicks and pointer events:

```js
const H = require('/skills/m3-design-spec/scripts/dom_harness.js');
const { doc, fire, loadError } = H;
if (loadError) throw loadError;
doc.querySelector('#themeToggle').click();
fire(doc.querySelector('#dpGrid'), 'keydown', { key:'ArrowRight', preventDefault(){} });
```

`focus()` updates the shared `activeElement`, and `tabIndex` is a reflected property — both are required for keyboard assertions to mean anything.

Limits: not a browser. Canvas is stubbed, layout is constant, observers are no-ops. Use it for logic, never for visuals.

### Keyboard reachability audit

`/skills/m3-design-spec/scripts/audit_keyboard.js`

```
node /skills/m3-design-spec/scripts/audit_keyboard.js path/to/page.html [--all]
```

Reports every element with a click listener that is not focusable. Expected exceptions: scrims and disabled buttons. Exit 0 = clean, 1 = findings, 2 = unusable input.

### Behaviour regression suite

`/skills/m3-design-spec/scripts/regression_tests.js`

```
node /skills/m3-design-spec/scripts/regression_tests.js path/to/page.html
M3_VERBOSE=1 node /skills/m3-design-spec/scripts/regression_tests.js path/to/page.html
```

End-to-end assertions across theme switching, all overlay types (focus trap and `inert` included), snackbar and notification stacking, steppers, the date picker keyboard model, time picker drag and keys, select and multi-select, form widgets, the login form, gestures, the `m3Keys` registry and command palette, composite-widget keyboard rules, spec-visualisation widgets, zoom adaptation, and keyboard support surviving a dynamic re-render. Exit 0 = all pass, 1 = failures, 2 = page threw on load.

Treat it as a template: adapt selectors to the page under test, then keep it as the smoke test.

## Validation checklist

- [ ] Both `:root` and `[data-theme="dark"]` define the same variable names; no color key is missing.
- [ ] Hex codes appear only inside the token blocks (plus intentional gradient accents).
- [ ] Toggling the checkbox changes `document.documentElement`'s `data-theme` and nothing persists it.
- [ ] Every interactive element produces a ripple, including ones created after load.
- [ ] Keyboard: Tab reaches every control, `:focus-visible` is styled, `Escape` closes overlays and menus.
- [ ] Every element with a click handler is focusable (scrim and disabled buttons excepted).
- [ ] Every composite widget has exactly one roving `tabindex="0"` and arrow-key navigation.
- [ ] Decorative chips carry a static marker and are excluded from roving.
- [ ] Global shortcuts do not fire while focus is in a text field.
- [ ] Focus returns to the opener when an overlay closes, and survives re-renders.
- [ ] A page with global shortcuts exposes a registry an agent can enumerate and invoke.
- [ ] Skip link is first in `<body>` and its target exists.
- [ ] `check_m3_html.py` exits 0.
- [ ] `audit_keyboard.js` exits 0.
- [ ] `dom_harness.js` reports no load-time exception.
- [ ] `regression_tests.js` passes, adapted to the page under test.
- [ ] At least one `min-width` breakpoint exists and the wide layout was considered.
- [ ] Viewport meta does not block zoom.
