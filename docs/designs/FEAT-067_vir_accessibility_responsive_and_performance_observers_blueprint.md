<!-- File path: docs/designs/FEAT-067_vir_accessibility_responsive_and_performance_observers_blueprint.md -->

---
feature_id: FEAT-067
feature_name: Visual Intelligence Runtime — Accessibility, Responsive & Performance Observers
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-067_vir_accessibility_responsive_and_performance_observers_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Accessibility, Responsive & Performance Observers

## 0. Baseline Context & References
- **Memory Baseline**: Memory of axe-core javascript injection rules and CDP performance buffers.
- **RAG Query Summaries**: Sensory observations route events to `AsyncEventBus` and log findings to SQLite tables (`FEAT-061`).
- **Inspected Source Files**:
  - [FEAT-067 Plan](file:///e:/AgentsProject/docs/plans/FEAT-067_vir_accessibility_responsive_and_performance_observers_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/observers/accessibility/engine.py` | Create | Audit target page configurations against WCAG 2.1 rules | None | High. Core accessibility scanner. |
| `vir_runtime/observers/accessibility/veto.py` | Create | Intercept critical accessibility trap states and dispatch VETOs | `engine.py` | Medium. Enforces decision gates. |
| `vir_runtime/observers/responsive/engine.py` | Create | Run multi-viewport breakpoint resizing and scan for overflow leaks | None | High. Audit layouts at screen sizes. |
| `vir_runtime/observers/performance/engine.py` | Create | Collect Web Vitals LCP/CLS metrics and locate CLS DOM nodes | None | High. Tracks client performance latency. |
| `vir_runtime/observers/performance/fps.py` | Create | Track active window rendering frames per second (FPS) | None | Low. Collects animation jank info. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── observers/
    ├── accessibility/
    │   ├── engine.py
    │   └── veto.py
    ├── performance/
    │   ├── engine.py
    │   └── fps.py
    └── responsive/
        └── engine.py
```

---

## 3. Complete Class & Module Design

### 3.1 AccessibilityObserver
- **Class / Module Name**: `vir_runtime.observers.accessibility.engine.AccessibilityObserver`
  - **Responsibilities**: Inject Axe-core scripts, analyze aria roles/focus behaviors, and package findings as `AccessibilityFinding` objects.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter`
  - **Public Methods**:
    - `async def run_a11y_scan() -> List[AccessibilityFinding]`
  - **Dependencies**: `axe-core` dependencies wrapped in script injections.

### 3.2 ResponsiveObserver
- **Class / Module Name**: `vir_runtime.observers.responsive.engine.ResponsiveObserver`
  - **Responsibilities**: Resize browser viewports to configured breakpoints, evaluate overlaps, and detect horizontal scrolls.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter`
    - `breakpoints: List[int]`
  - **Public Methods**:
    - `async def verify_responsive_layouts() -> List[ResponsiveFinding]`

### 3.3 PerformanceObserver
- **Class / Module Name**: `vir_runtime.observers.performance.engine.PerformanceObserver`
  - **Responsibilities**: Query performance metrics from Chrome DevTools Protocol (CDP), trace DOM elements causing layout shifts.
  - **Constructor Parameters**:
    - `adapter: BrowserAdapter`
  - **Public Methods**:
    - `async def capture_web_vitals() -> PerformanceFinding`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def run_a11y_scan() -> List[AccessibilityFinding]`
  - **Parameters**: None.
  - **Return Types**: Returns a list of `AccessibilityFinding` dataclasses.
  - **Exceptions**:
    - `AxeCoreInjectionFailedError` - If JS environment blocks axe injection scripts.

---

## 5. Configuration Schema

- **Target Schema (`vir_observers.yaml`)**:
```yaml
observers:
  accessibility:
    wcag_level: "AA"
    veto_on_missing_alt: false
  responsive:
    breakpoints: [375, 768, 1440]
  performance:
    cls_max_threshold: 0.1
    lcp_max_threshold_seconds: 2.5
```

---

## 6. Database & Storage Design
- Observers findings are stored in `vir_evidence` table using classification `accessibility`, `responsive`, or `performance`.

---

## 7. Cache Architecture
- No caching is defined for observers layers.

---

## 8. Error Model

- **Exception Class**: `AccessibilityVetoTriggered`
  - **Trigger Condition**: A MUST-level WCAG check fails (e.g. keyboard trap).
  - **Recovery Strategy**: Issue VETO event to event bus logs, lowering quality scores.
  - **Logging Requirements**: WARNING log referencing target DOM node bounding boxes.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Performance Auditing Flow**:
  1. `PerformanceObserver` queries page performance timeline buffers via CDP.
  2. CLS shift metrics are parsed.
  3. Elements causing layout shift are identified.
  4. Web vitals packed into `PerformanceFinding`.
  5. Findings published on Event Bus.

---

## 12. Security & Safety
- **Breakpoint constraints validation**: Viewport parameters values are verified before calling resize commands, preventing memory locks in headless browser engines.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-01` | Unit Test | `tests/unit/test_a11y_compliance.py` | `engine.py` | `self.assertGreater(len(findings), 0)` |
| `FR-08` | Unit Test | `tests/unit/test_responsive_viewports.py` | `engine.py` | `self.assertTrue(has_horizontal_scroll)` |

---

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Class `AccessibilityObserver` -> `engine.py` -> `test_a11y_compliance.py` -> Verified.
- `FR-08` -> Task 1.8 -> Class `ResponsiveObserver` -> `engine.py` -> `test_responsive_viewports.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/observers/performance/engine.py`
  - **Purpose**: Collect Web Vitals metrics via CDP.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on browser devtools protocol support.
