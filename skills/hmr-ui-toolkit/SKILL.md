---
name: hmr-ui-toolkit
command: hmr
aliases:
  - hmr-ui
  - vir-hmr
  - visual-runtime
category: frontend
tags:
  - HMR
  - VIR
  - VAR
  - visual-intelligence
  - ui-debug
  - browser
  - cdp
version: 1.0.0
license: MIT
created_at: 2026-07-25
updated_at: 2026-07-25
description: >
  Teaches AI agents how to use the workflow_runtime Visual Intelligence Runtime
  (VIR), Visual Assertion Runtime (VAR), and Hot Module Replacement (HMR)
  infrastructure to inspect, modify, and verify UI changes in a real browser
  without restarting the app.
runtime_requirements:
  rules: required
  state: required
  memory: cached
  rag: optional
  environment: required
  browser: required
  cdp: required
---

# Skill: HMR UI Toolkit

> **Architecture domain:** `workflow_runtime.infrastructure.browser` + `workflow_runtime.infrastructure.visual`
>
> **Purpose:** Give agents a concrete, step-by-step guide for using the
> project's built-in VIR/VAR/HMR stack to inspect, patch, and verify UI
> changes in a running browser — without touching source files blindly.

---

## 📐 Module Map

```
workflow_runtime/infrastructure/
├── browser/
│   ├── __init__.py          — public API surface (BrowserSession, open_session, etc.)
│   ├── cdp_bridge.py        — Chrome DevTools Protocol (CDP) full implementation
│   ├── cdp_client.py        — low-level CDP WebSocket client
│   ├── cdp_session.py       — CDP session lifecycle manager
│   ├── dom_inspector.py     — DOM query, attribute inspection
│   ├── screenshot_capturer.py — take screenshots at any point
│   ├── sensory/
│   │   ├── hearing.py       — console log listener (JS errors, network, etc.)
│   │   └── touch.py         — DOM mutation triggers, click/type injection
│   └── sandbox/             — isolated page sandbox helpers
│
└── visual/
    ├── __init__.py
    ├── adapters/
    │   ├── cdp.py           — CDP visual adapter (screenshot → pixel diff)
    │   ├── drission_adapter.py — DrissionPage browser adapter
    │   ├── playwright_adapter.py — Playwright browser adapter
    │   ├── gemini_provider.py   — Gemini vision provider for VIR analysis
    │   ├── baseline_repo.py     — baseline screenshot storage and retrieval
    │   ├── report_repo.py       — visual report writer
    │   ├── adapter_factory.py   — selects adapter by config
    │   └── server.py            — local asset serving for screenshots
    ├── mapper/
    │   ├── scraper.py       — layout scraper (position, visibility)
    │   └── sourcemaps.py    — source map resolver for UI elements
    ├── memory/
    │   ├── baselines.py     — baseline image management
    │   └── learning.py      — learns from pass/fail visual history
    └── varbc/
        ├── base.py          — VAR base assertion class
        └── registry.py      — VAR assertion registry
```

---

## 🔁 HMR Workflow (3-Phase Loop)

### Phase 1 — OBSERVE (vir-runtime)

Before editing any CSS/HTML/JS, use the browser infrastructure to capture
the current visual state:

```python
from workflow_runtime.infrastructure.browser import (
    screenshot_capturer, dom_inspector, cdp_bridge
)

# 1. Open a CDP session to the already-running browser/webview
bridge = cdp_bridge.CdpBridge(debug_port=9222)
session = bridge.new_session()

# 2. Capture baseline screenshot
capturer = screenshot_capturer.ScreenshotCapturer(session)
baseline_png = capturer.capture("before_change")   # saves to .agents/scratch/

# 3. Inspect DOM layout (box model, visibility, computed styles)
inspector = dom_inspector.DomInspector(session)
el = inspector.query_selector("#my-button")
box = inspector.get_box_model(el)
styles = inspector.get_computed_styles(el)
print(box, styles)
```

### Phase 2 — PATCH (hot-inject, no restart)

Inject CSS or DOM changes directly via CDP without restarting:

```python
# Option A: inject CSS via CDP Runtime.evaluate
session.evaluate("""
  const s = document.createElement('style');
  s.textContent = `
    .my-component { background: #1e1e2e; color: #cdd6f4; border-radius: 8px; }
  `;
  document.head.appendChild(s);
""")

# Option B: patch a source file and trigger HMR if Vite/webpack is running
import subprocess
# Edit the file, then the HMR server picks up the change automatically.
# The browser updates without a full reload.
```

### Phase 3 — VERIFY (vir-verify / VAR)

After patching, verify that the change matches the design spec:

```python
from workflow_runtime.infrastructure.visual.adapters.cdp import CdpVisualAdapter
from workflow_runtime.infrastructure.visual.adapters.baseline_repo import BaselineRepo

adapter = CdpVisualAdapter(session)
repo    = BaselineRepo(base_dir=".agents/scratch/baselines")

# Capture "after" screenshot
after_png = capturer.capture("after_change")

# Pixel diff against baseline
diff = adapter.diff(baseline_png, after_png, threshold=0.02)
if diff.changed_pixels > diff.threshold:
    print(f"VISUAL DIFF DETECTED: {diff.changed_pixels} px changed")
else:
    print("Visual PASS — within threshold")

# Or use VAR assertions
from workflow_runtime.infrastructure.visual.varbc.registry import VarRegistry
var = VarRegistry()
var.assert_element_visible("#my-button")
var.assert_computed_style("#my-button", "border-radius", "8px")
var.run_all(session)   # raises AssertionError on failure
```

---

## 🛠️ Adapter Selection Guide

| Adapter | When to use |
|---|---|
| `cdp.py` | Default — direct Chrome DevTools Protocol (no extra deps) |
| `playwright_adapter.py` | When Playwright is available and Ba requests it |
| `drission_adapter.py` | When DrissionPage is the configured browser driver |
| `gemini_provider.py` | Semantic visual analysis ("does this look correct?") via Gemini vision |

The adapter is auto-selected by `adapter_factory.py` based on
`.agents/runtime/browser-config.json`. Do NOT hardcode adapter choice.

---

## 👁️ Sensory Tools

### `hearing.py` — listen to console logs

```python
from workflow_runtime.infrastructure.browser.sensory.hearing import ConsoleHearing
listener = ConsoleHearing(session)
listener.start()
# ... perform UI interaction ...
logs = listener.stop()
errors = [l for l in logs if l["level"] == "error"]
```

### `touch.py` — simulate user interactions

```python
from workflow_runtime.infrastructure.browser.sensory.touch import DomTouch
touch = DomTouch(session)
touch.click("#submit-button")
touch.type("#search-input", "my query")
touch.scroll_to("#footer")
```

---

## 📸 Screenshot Evidence Protocol

Every visual change MUST produce evidence screenshots. Store them in:

```
docs/reports/assets/<work-item-id>/
    before_<component>_<timestamp>.png
    after_<component>_<timestamp>.png
    diff_<component>_<timestamp>.png
```

Reference them in the phase report with **relative paths** — never absolute paths.

```markdown
![Before change](../assets/FEAT-123/before_header_20260725.png)
![After change](../assets/FEAT-123/after_header_20260725.png)
```

---

## 🚫 Prohibition Rules (inherited from VIR Skills Policy)

1. **Never claim UI completion** from static source inspection alone.
2. **Never open browser files** without first calling `vir-runtime`.
3. **Screenshots are mandatory** — a visual review without screenshots = automatic FAIL.
4. **Diff must be documented** — compare before/after every CSS or DOM change.
5. **Console errors block completion** — fix any JS console errors before marking PASS.
6. **Responsive check required** — verify at least 2 breakpoints (mobile + desktop) for layout changes.

---

## 🔄 Integration with VIR Skills

This HMR skill is the **implementation layer**. Use it together with:

| Skill | When |
|---|---|
| `vir-runtime` | Start visual observation session (before coding) |
| `vir-investigate` | Root-cause analysis when a visual diff is unexpected |
| `vir-verify` | Final visual quality gate (score ≥ 95/100) |
| `vir-memory-update` | Store the new passing screenshot as the new baseline |
| `frontend-design` | Design decisions before implementing (typography, color, spacing) |

### Correct sequence for any UI change:

```
vir-runtime (observe baseline)
  → hmr-ui-toolkit (patch via HMR/CDP)
  → vir-investigate (if diff is unexpected)
  → vir-verify (final gate)
  → vir-memory-update (update baseline)
```

---

## 🐛 Debug Port Setup

The browser must be launched with a CDP debug port:

```bash
# Chrome / Chromium
chrome --remote-debugging-port=9222 --user-data-dir="${TMPDIR:-.agents/runtime/tmp}/cdp-profile"

```

Check `.agents/runtime/browser-config.json` for the project-configured port.

---

## ✅ Definition of Done (UI change)

A UI change is considered DONE only when ALL of the following are true:

- [ ] `vir-runtime` baseline screenshot captured before change
- [ ] CSS/HTML/JS patch applied and HMR/CDP-injected
- [ ] `vir-verify` PASS with diff within threshold (default 2%)
- [ ] Console errors: ZERO
- [ ] Network errors blocking UI: ZERO
- [ ] Responsive check: PASS at mobile (375px) and desktop (1440px)
- [ ] Screenshots stored in `docs/reports/assets/<work-item-id>/`
- [ ] Phase report updated with relative screenshot links
- [ ] `vir-memory-update` called to store new baseline
