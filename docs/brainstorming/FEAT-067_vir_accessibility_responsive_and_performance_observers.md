<!-- docs/brainstorming/FEAT-067_vir_accessibility_responsive_and_performance_observers.md -->

---
feature_id: FEAT-067
feature_name: Visual Intelligence Runtime — Accessibility, Responsive & Performance Observers
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-066_vir_quality_gates_and_reporting_system.md
next_artifact: ../plans/FEAT-067_vir_observers_plan.md
---

# Master Requirement Document – VIR Accessibility, Responsive & Performance Observers

## 1. Feature ID & Name
- **Feature ID**: FEAT-067
- **Feature Name**: Visual Intelligence Runtime — Accessibility, Responsive & Performance Observers

## 2. Original Idea
Design three specialized observer agents for VIR: the Accessibility Engine (with veto power over critical a11y failures), the Responsive Engine (breakpoint-aware layout validation), and the Performance Observer (Core Web Vitals monitoring and animation quality assessment). Each is a domain-expert agent in the multi-agent architecture.

## 3. Business Problem
- **Problem**: Accessibility, responsive behavior, and performance are specialized domains that generic visual inspection cannot adequately evaluate. A button that looks enabled may be inaccessible. A layout that looks correct on desktop may break at 768px. A page that looks fast may have poor CLS or INP. Each domain requires specialist knowledge and dedicated evaluation criteria.
- **Why it matters**: Accessibility is a legal requirement. Responsive is a user experience requirement. Performance is a business requirement. All three are common failure modes in modern web applications.
- **Who is affected**: Accessibility Agent (veto power), Responsive Agent, Performance Agent, Design Authority, Consensus Engine, Quality Gate.
- **Expected outcome**: Three specialized observer agents with formal Agent Contracts, domain authority, configurable thresholds, and structured evidence output.

## 4. Requirement Discovery

### Functional Requirements

#### Accessibility Engine
- FR-01: Accessibility Engine must run WCAG 2.1 AA compliance checks (minimum; configurable to AAA).
- FR-02: Checks must include: color contrast ratio (WCAG 1.4.3, 1.4.6), keyboard navigability (WCAG 2.1.1, 2.1.2), focus visibility (WCAG 2.4.7), ARIA roles and attributes (WCAG 4.1.2), alt text on images (WCAG 1.1.1), form labels (WCAG 1.3.1), heading hierarchy (WCAG 1.3.1), skip navigation links (WCAG 2.4.1), timeout warnings (WCAG 2.2.1), live region announcements (WCAG 4.1.3), motion/animation preference support (WCAG 2.3.3), reflow at 320px (WCAG 1.4.10).
- FR-03: Accessibility Engine uses Vision Engine Layer 1 (DOM inspection) as primary source; Vision Layer 2 for contrast validation.
- FR-04: Accessibility Engine must have VETO power over Quality Gate when: contrast ratio < WCAG threshold for any text element, keyboard trap detected, missing alt text on informational image, form field without label, critical ARIA violation.
- FR-05: WCAG thresholds configurable per project (default: AA).
- FR-06: Accessibility findings published as AccessibilityFinding Evidence objects with: WCAG criterion, current value, required value, affected element, severity.

#### Responsive Engine
- FR-07: Responsive Engine must test defined breakpoints: configurable per project (defaults: 320, 375, 768, 1024, 1280, 1440, 1920px).
- FR-08: For each breakpoint: capture screenshot, inspect layout, check for overflow, check text readability, check touch target sizes (≥44×44px), check horizontal scrollbar absence, check element overlap, check navigation usability.
- FR-09: Responsive Engine must detect: element overflow at breakpoint, content hidden that should be visible, layout collapse/reflowing incorrectly, images not scaling, fixed-width elements causing scroll, text truncation at wrong breakpoints.
- FR-10: Responsive Engine publishes ResponsiveFinding Evidence objects per breakpoint.
- FR-11: Responsive Engine must not issue VETO; findings are FAIL-contributing but Design Authority makes final design call.

#### Performance Observer
- FR-12: Performance Observer must capture Core Web Vitals: LCP (Largest Contentful Paint), FCP (First Contentful Paint), CLS (Cumulative Layout Shift), INP (Interaction to Next Paint), TTFB (Time to First Byte), FID (First Input Delay, for browsers not supporting INP).
- FR-13: Performance thresholds configurable (defaults follow Google Core Web Vitals GOOD thresholds).
- FR-14: Performance Observer must detect: layout shifts with their sources (CLS contributors), render-blocking resources, large unoptimized images, long tasks (> 50ms), excessive JavaScript bundle sizes (if detectable), animation performance (frame rate monitoring).
- FR-15: Animation Observer: monitor animation frame rate; detect janky animations (< 60fps), frozen animations, animation triggered on non-GPU-composited layers.
- FR-16: Performance Observer publishes PerformanceFinding Evidence objects with metric name, value, threshold, classification (GOOD/NEEDS_IMPROVEMENT/POOR).
- FR-17: Performance Observer does not issue VETO; classification POOR contributes to FAIL if critical performance threshold exceeded.

### Non-functional Requirements
- NFR-01: Accessibility Engine scan < 3s for standard page complexity.
- NFR-02: Responsive Engine scan < 5s for 6 breakpoints.
- NFR-03: Performance Observer capture < 8s per full Core Web Vitals capture.
- NFR-04: All three observers operate concurrently when in Standard+ profile.
- NFR-05: Observers must not inject any JavaScript that affects application behavior.

### Technical Constraints
- TC-01: Accessibility Engine uses Browser Adapter (Playwright a11y API + axe-core optional integration).
- TC-02: Responsive Engine uses Browser Adapter (viewport resize + screenshot).
- TC-03: Performance Observer uses Browser Adapter (CDP Performance domain + PerformanceObserver API).
- TC-04: All three agents registered in Agent Registry with standard Agent Contract.
- TC-05: WCAG and performance thresholds configured in `vir_observers.yaml`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | WCAG 2.1 AA checks | BP-VIR-016 | Run on WCAG test fixtures | Known violations detected; compliant pages pass |
| FR-04 | Must | A11y VETO power | BP-VIR-016 | Inject keyboard trap | VETO issued; PASS blocked |
| FR-07 | Must | Responsive breakpoints | BP-VIR-016 | Test 6 breakpoints | 6 screenshot captures + findings |
| FR-09 | Must | Responsive violations | BP-VIR-016 | Inject overflow at 375px | ResponsiveFinding published |
| FR-12 | Must | Core Web Vitals | BP-VIR-016 | Capture LCP/FCP/CLS/INP on test page | All 4 metrics captured with values |
| FR-14 | Must | CLS source detection | BP-VIR-016 | Inject known CLS source | Source element identified in finding |
| FR-15 | Should | Animation frame rate | BP-VIR-016 | Run 30fps animation | Janky animation detected |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Accessibility Specialists | Primary | High | Critical | Automated WCAG compliance without manual audit |
| Frontend Developers | Primary | High | High | Performance bottleneck identification |
| Design Authority Agent | Internal | Medium | High | Accessibility findings complement design findings |
| Consensus Engine | Internal | High | High | A11y veto + performance classification |
| Legal/Compliance Teams | External | High | Critical | WCAG compliance documentation |

## 7. Scope Boundary

### In Scope
- Full Accessibility Engine (WCAG 2.1 AA)
- Responsive Engine (configurable breakpoints)
- Performance Observer (Core Web Vitals + animation)
- Structured Evidence objects per observer
- A11y VETO mechanism
- WCAG and performance threshold configuration

### Out of Scope
- Assistive technology testing (screen reader simulation — deferred)
- Automated accessibility fix application
- WCAG AAA by default (configurable)

### Deferred Scope
- Screen reader API integration (NVDA/JAWS simulation)
- Color blindness simulation
- Browser-level performance tracing (Lighthouse integration)

### Future Scope
- Manual accessibility audit documentation workflow
- Automated remediation suggestions with fix code generation

## 8. Dependency Graph Preview

- FEAT-067: Observers (Should)
  - FEAT-056: Event Bus (prerequisite)
  - FEAT-057: Browser Adapter (prerequisite)
  - FEAT-058: Vision Engine Layer 1 (a11y uses DOM data)
  - FEAT-063: Multi-Agent (observers are registered agents)
  - FEAT-066: Quality Gates (receives observer findings)

## 9. Data Flow Preview

- Standard profile → 3 observers activated concurrently
  └── A11y Engine: DOM inspection → contrast ratio 2.8:1 (< 4.5:1 AA) → AccessibilityFinding
      └── VETO issued: `accessibility.contrast_ratio_fail`
  └── Responsive Engine: viewport 375px → horizontal scroll detected → ResponsiveFinding severity=ERROR
  └── Performance Observer: CLS 0.32 (> 0.1 threshold → POOR) → PerformanceFinding
      └── CLS source: `.promo-banner` element identified
  All findings published to event bus → Evidence Engine aggregates
      └── Consensus Engine: A11y VETO active → Gate = FAIL

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-visual-debug (basic contrast check) | SKILL.md | Replace | Procedural contrast check replaced by A11y Engine |
| axe-core (external) | npm package | Optional wrap | A11y rule library (optional integration) |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: High — A11y veto can block releases; performance findings affect release confidence

## 12. Migration Strategy

- **Backward Compatibility**: A11y and performance checks in old skill replaced by formal agents
- **Migration Phases**: Phase 5: A11y + Responsive; Phase 5: Performance Observer

## 13. Architecture Principles

- **Provider First**: All observers use Browser Adapter; no direct Playwright calls
- **Domain Authority**: A11y Agent is the sole WCAG authority in VIR
- **Configurable Thresholds**: No hardcoded WCAG values; all from configuration

## 14. Non Goals

- Observers do not fix accessibility issues
- Performance Observer does not profile backend performance
- Responsive Engine does not redesign layouts

## 15. ROI Analysis

- **Legal Risk Reduction**: WCAG compliance automation prevents costly accessibility lawsuits
- **User Experience**: Responsive detection catches mobile UX issues before users do
- **Performance Revenue**: CLS and INP improvements directly correlate with user retention

## 16. Success Metrics

- **A11y Coverage**: 100% of WCAG 2.1 AA criteria checked
- **VETO Accuracy**: > 98% agreement with human a11y expert on test fixtures
- **Responsive Coverage**: 100% of configured breakpoints tested
- **Performance Capture**: LCP, FCP, CLS, INP all captured successfully on test page

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| False positive contrast violations (anti-aliasing) | High | Medium | 3px sampling area for contrast; configurable sampling | A11y Engineer |
| Responsive test timing issues (animations mid-layout) | Medium | High | Screenshot after layout-stable event; configurable settle wait | Frontend Engineer |
| Performance metrics unreliable in headless CI | Medium | High | Configurable profiles; CI uses consistent hardware/throttling | Infrastructure |
| axe-core library version incompatibility | Medium | Low | Optional integration; native implementation primary | Frontend Engineer |

## 18. Technical Questions

- Should the Accessibility Engine use axe-core or implement WCAG checks natively?
- What is the minimum wait time after viewport resize before Responsive Engine captures?
- Should CLS be measured on full page load or also after interactions?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| axe-core vs native WCAG | Pending | Native primary; axe-core as optional enhancement |
| Responsive Engine settle time | Pending | Default 500ms after resize; configurable |
| CLS measurement scope | Pending | Full page load + configurable interaction triggers |

## 20. ADR Detection

- **ADR Required**: No — observer patterns follow established agent architecture

## 21. Knowledge Update Impact

- **patterns**: Yes — Observer Agent pattern; A11y veto pattern
- **architecture**: Yes — Three specialized observer agents

## 22. Test Strategy Preview

- **Unit Tests**: Each WCAG check independently tested with known compliant/non-compliant fixtures; CWV metric capture; responsive overflow detection
- **Integration Tests**: Full observer pipeline on test pages (compliant page → PASS; violating page → FAIL)
- **Veto Tests**: Keyboard trap detection → VETO → Gate FAIL

## 23. Extension Impact

- **Extension UI Changes**: A11y findings panel; Performance gauge; Responsive breakpoint switcher
- **Affected ViewModels**: WCAG compliance score; CWV gauges; breakpoint status grid

## 24. Complexity Estimation

- **Implementation Complexity**: Medium-High
- **Estimated Refactoring Percentage**: 5% existing / 95% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 5 (Observers) → concurrent with Cognitive Engines
- **Prerequisites**: FEAT-056, FEAT-057, FEAT-058 (Vision Layer 1), FEAT-063 (Agent Contract)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| A11y veto power? | Yes — veto on critical WCAG violations |
| Responsive testing? | Yes — configurable breakpoints |
| Animation monitoring? | Yes — frame rate, jank detection |
| Performance metrics? | Yes — Core Web Vitals (LCP, FCP, CLS, INP) |

## 27. Requirement Readiness Score

- **Score**: 94/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Known WCAG 2.1 AA violations detected on WCAG test fixtures
- [ ] AC-02 (FR-04): Keyboard trap detected → VETO issued → Gate FAIL
- [ ] AC-03 (FR-07): 6 breakpoints tested; 6 screenshots + findings produced
- [ ] AC-04 (FR-12): LCP, FCP, CLS, INP all captured with values on test page
- [ ] AC-05 (FR-14): CLS source element identified in finding; not just CLS value

## 35. Final Planning Prompt

### Problem Statement
VIR needs three specialized observer agents: Accessibility Engine (WCAG 2.1 AA, veto power), Responsive Engine (configurable breakpoints), Performance Observer (Core Web Vitals + animation).

### Architectural Details
- `vir_runtime/agents/accessibility/accessibility_engine.py` — WCAG checks + veto
- `vir_runtime/agents/accessibility/wcag_rules.py` — WCAG rule library
- `vir_runtime/agents/responsive/responsive_engine.py` — Breakpoint testing
- `vir_runtime/agents/performance/performance_observer.py` — CWV + animation
- `vir_runtime/agents/performance/animation_observer.py` — Frame rate monitoring
- `config/vir_observers.yaml` — Threshold configuration

### Verification Checklist
- [ ] docs/plans/FEAT-067_vir_observers_plan.md generated and approved
- [ ] docs/designs/FEAT-067_vir_observers_blueprint.md generated and approved
