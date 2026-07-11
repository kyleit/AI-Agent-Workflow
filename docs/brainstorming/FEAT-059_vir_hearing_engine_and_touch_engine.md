<!-- docs/brainstorming/FEAT-059_vir_hearing_engine_and_touch_engine.md -->

---
feature_id: FEAT-059
feature_name: Visual Intelligence Runtime — Hearing Engine & Touch Engine
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-058_vir_vision_engine.md
next_artifact: ../plans/FEAT-059_vir_hearing_touch_engines_plan.md
---

# Master Requirement Document – VIR Hearing Engine & Touch Engine

## 1. Feature ID & Name
- **Feature ID**: FEAT-059
- **Feature Name**: Visual Intelligence Runtime — Hearing Engine & Touch Engine

## 2. Original Idea
Design and implement the VIR Hearing Engine (observer of all non-visual signals from the browser runtime and application) and the Touch Engine (controller of deterministic and human-simulated user interactions). These two engines together form VIR's input-output sensory layer.

## 3. Business Problem
- **Problem**: A visual-only runtime is blind to the runtime dynamics of the application — it cannot see console errors, API failures, authentication events, or state transitions. It also cannot interact with the UI to trigger state changes needed for investigation. Without Hearing and Touch, VIR can only observe a static picture, not a living application.
- **Why it matters**: Most frontend bugs manifest as a combination of visual symptoms and runtime signals (a button looks enabled but the API call fails silently). The Hearing Engine correlates these signals with visual observations to find root causes the Vision Engine alone could never detect.
- **Who is affected**: Evidence Engine, Contradiction Engine, Digital Twin, Business Intelligence Engine, Cognitive Investigation Engine.
- **Expected outcome**: A comprehensive Hearing Engine monitoring all browser runtime signals, and a Touch Engine enabling repeatable and human-simulated user interactions.

## 4. Requirement Discovery

### Functional Requirements

#### Hearing Engine
- FR-01: Monitor browser console logs (all levels: log, info, warn, error, debug).
- FR-02: Capture JavaScript runtime errors and unhandled promise rejections.
- FR-03: Monitor all network activity: Fetch, XHR, GraphQL operations, WebSocket messages, Server-Sent Events.
- FR-04: Monitor network request details: URL, method, status, headers, timing, response body (configurable depth).
- FR-05: Observe page lifecycle events: DOMContentLoaded, load, beforeunload, unload, visibilitychange.
- FR-06: Observe router events: route change, navigation start, navigation complete, navigation error.
- FR-07: Observe authentication events: login, logout, token refresh, session expiry, permission change.
- FR-08: Observe application state transitions from State Adapters (React, Vue, Svelte, Angular).
- FR-09: Observe Service Worker activity: install, activate, fetch intercept, cache operations.
- FR-10: Observe browser performance events: paint, layout shift, LCP, FCP, FID, INP, TTFB.
- FR-11: Observe accessibility announcements (ARIA live regions, role=alert changes).
- FR-12: Optional Audio Adapter: verify media playback state (started, muted, track, blocked, volume, duration, seeking, pause, resume) when feature contains audio.
- FR-13: All observations published as structured Evidence to event bus.
- FR-14: Hearing Engine must correlate related events by time window and request ID into logical Observation Groups.

#### Touch Engine
- FR-15: Mode A (Deterministic): click, double-click, right-click, hover, focus, blur, keyboard input, tab navigation, drag-drop, scroll, swipe, touch tap, form submission, file selection, pointer events, viewport resize, device emulation.
- FR-16: Mode B (Human Behavior Simulation): variable pointer speed, imperfect movement, realistic pauses, double-click timing, repeated clicks, fast/slow typing, partial input, accidental focus loss, scroll hesitation, back navigation, refresh, window resize, mobile swipe, pinch-zoom, interaction during loading, interaction during network latency.
- FR-17: All Mode B randomness must be seeded, reproducible, configurable, and logged.
- FR-18: Touch Engine must always run Deterministic mode first. Human simulation is additional exploratory layer.
- FR-19: Touch Engine publishes all interactions as Evidence (action taken, target element, result, timing).
- FR-20: Touch Engine must support action recording for replay.
- FR-21: Touch Engine must detect when an action has no observable effect (dead click / stuck element).

### Non-functional Requirements
- NFR-01: Hearing Engine must capture 100% of console events with < 10ms timestamp accuracy.
- NFR-02: Hearing Engine must not miss network requests regardless of request timing.
- NFR-03: Touch Engine deterministic actions must be reproducible with 100% consistency.
- NFR-04: Human simulation seed value must produce identical interaction sequence across runs.
- NFR-05: Touch Engine actions must include pre-action screenshot and post-action screenshot for Evidence.

### Technical Constraints
- TC-01: Hearing Engine uses Browser Adapter (Playwright CDP: Page.consoleAPICalled, Network events, Page lifecycle, etc.).
- TC-02: Touch Engine uses Browser Adapter (Playwright interaction APIs).
- TC-03: Hearing Engine event correlation window configurable in milliseconds.
- TC-04: Human simulation seeding via Python `random.seed(config.human_sim_seed)`.
- TC-05: Audio Adapter optional; only activated when feature config includes `audio_testing: true`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Console log monitoring | BP-VIR-005 | Trigger console.error; verify captured | Error evidence with level, message, stack |
| FR-02 | Must | JS runtime errors | BP-VIR-005 | Throw uncaught exception; verify captured | Exception evidence with stack trace |
| FR-03 | Must | Network monitoring | BP-VIR-005 | Make API call; verify request+response captured | Evidence includes URL, status, timing |
| FR-06 | Must | Router event observation | BP-VIR-005 | Navigate SPA routes; verify events captured | Route change evidence with from/to |
| FR-08 | Must | App state transitions | BP-VIR-005 | Trigger state change; verify captured | State before/after in evidence |
| FR-13 | Must | Evidence published to bus | BP-VIR-007 | All hearing events received by Evidence Engine | Evidence object has all required fields |
| FR-14 | Must | Event correlation | BP-VIR-005 | Login flow: network call + auth event + state + visual | Correlation group ID links all events |
| FR-15 | Must | Deterministic Mode A | BP-VIR-005 | Click button; verify click registered | Click evidence with target, timing, result |
| FR-16 | Should | Human simulation Mode B | BP-VIR-005 | Run simulation with seed 12345; run again same seed | Identical action sequence produced |
| FR-21 | Must | Dead click detection | BP-VIR-005 | Click disabled button; verify no-effect detected | Dead click evidence published |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Evidence Engine | Internal | Critical | Critical | Runtime signals as structured evidence |
| Contradiction Engine | Internal | High | High | Hearing signals that contradict visual observations |
| Digital Twin | Internal | High | High | Runtime/authentication/business state dimensions |
| Business Intelligence Engine | Internal | High | High | Business flow validation through hearing signals |
| Cognitive Investigation Engine | Internal | High | High | Network failures, errors as investigation inputs |

## 7. Scope Boundary

### In Scope
- Full Hearing Engine (console, network, lifecycle, router, auth, state, SW, performance, a11y)
- Touch Engine Mode A (deterministic) and Mode B (human simulation)
- Event correlation engine
- Dead click detection
- Audio Adapter (optional)
- Action recording for replay

### Out of Scope
- Speech-to-Text, Text-to-Speech, waveform analysis, frequency analysis, microphone (explicit out-of-scope per clarification answers)
- Network analysis visualization (Reporting — FEAT-066)
- Accessibility Engine detailed logic (FEAT-067)

### Deferred Scope
- Voice/audio adapters for features requiring voice testing
- Background audio monitoring

### Future Scope
- WebRTC monitoring
- IndexedDB observation
- Background sync observation

## 8. Dependency Graph Preview

- FEAT-059: Hearing & Touch Engines (Must — Sensory layer)
  - FEAT-056: Event Bus (prerequisite)
  - FEAT-057: Browser Adapter (prerequisite)
  - FEAT-060: Digital Twin (consumer — runtime/auth state)
  - FEAT-061: Evidence Domain (consumer of hearing/touch output)
  - FEAT-062: Cognitive Engine (uses hearing signals for investigation)

## 9. Data Flow Preview

- Browser session active → Hearing Engine attached via Browser Adapter
  └── Hearing monitors console → error event captured → Evidence published
  └── Hearing monitors network → API 401 captured → Auth evidence published
      └── Auth evidence + Visual evidence (login screen visible) → correlated → Observation Group
          └── Contradiction Engine checks: API says logged-in + Visual shows login screen → Contradiction
              └── Digital Twin updated: Authentication State = CONTRADICTED
  └── Touch Engine executes deterministic click on Login button
      └── Pre-action screenshot + Action event + Post-action screenshot published as Evidence
          └── Hearing Engine captures resulting network call → links to action via request correlation ID

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-visual-debug (console check) | `.agents/skills/frontend-visual-debug/SKILL.md` | Replace | Procedural console check replaced by Hearing Engine |
| Playwright Page events API | External | Use via Browser Adapter | Console, network, lifecycle events |

## 11. Dependency & Blast Radius Analysis

- **Affected Agents**: Evidence Engine, Contradiction Engine, Digital Twin, Business Intelligence
- **Impact Level**: High — Hearing is the primary non-visual sensory input

## 12. Migration Strategy

- **Backward Compatibility**: Hearing replaces existing console/network checks in frontend-visual-debug
- **Migration Phases**: Phase 2: core console + network; Phase 3: state + auth + lifecycle; Phase 5+: correlation engine

## 13. Architecture Principles

- **Provider First**: Hearing uses Browser Adapter exclusively; no direct Playwright calls
- **Memory First**: Previous network error patterns consulted before flagging new error
- **API First**: Evidence schema defined before Hearing Engine implemented
- **Reproducibility**: All human simulation seeded and logged

## 14. Non Goals

- Hearing Engine does not analyze audio frequencies or speech
- Touch Engine does not redesign UI interactions
- Neither engine makes pass/fail decisions

## 15. ROI Analysis

- **Value**: Detection of runtime errors, API failures, and state inconsistencies that vision alone misses
- **Regression Prevention**: Automated hearing catches silent failures (e.g., broken authentication)
- **Investigation Quality**: Correlated hearing + vision evidence produces root causes impossible to find manually

## 16. Success Metrics

- **Console Capture Rate**: 100% of console events captured
- **Network Capture Rate**: 100% of Fetch/XHR requests captured regardless of timing
- **Correlation Accuracy**: > 90% of causally-related events correctly grouped
- **Deterministic Reproducibility**: 100% — same seed = identical interaction sequence
- **Dead Click Detection**: > 95% detection rate on known dead-click test cases

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Playwright CDP event ordering differs from actual timeline | Medium | Medium | Use monotonic timestamps; CDP sequence numbers | Backend Engineer |
| Network event capture misses streaming responses | Medium | Medium | Chunk streaming support; configurable body capture limit | Backend Engineer |
| Human simulation too random; undetectable bugs | Medium | Low | Seeded; all actions logged; reproducible replay | QA Engineer |
| Authentication event definitions differ per framework | Medium | High | Framework-specific State Adapter defines auth event taxonomy | Frontend Engineer |
| Event correlation false-positive groups unrelated events | Medium | Medium | Configurable correlation window; request ID matching as primary | Backend Engineer |

## 18. Technical Questions

- Should Hearing Engine correlation use request IDs from headers (e.g., X-Request-ID) or timing-window-only?
- What is the maximum network response body size to capture in evidence (configurable, but what default)?
- Should Touch Engine action recording use Playwright's built-in record/replay or a custom format?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Correlation primary key | Pending | Request ID preferred; timing window as fallback; decide in BP-VIR-005 |
| Response body capture limit | Pending | Default 1MB; configurable; decide in BP-VIR-005 |
| Action recording format | Pending | Custom JSON format for cross-adapter portability; decide in BP-VIR-005 |

## 20. ADR Detection

- **ADR Required**: No — design follows established patterns
- **Rationale**: Event correlation strategy is an implementation detail, not an architecture decision requiring ADR

## 21. Knowledge Update Impact

- **patterns**: Yes — Event correlation pattern; Browser runtime observation pattern
- **architecture**: Yes — Hearing Engine + Touch Engine architecture
- **modules**: Yes — vir_runtime/engines/hearing/ and vir_runtime/engines/touch/

## 22. Test Strategy Preview

- **Unit Tests**: Each hearing signal type independently tested with stub Browser Adapter; correlation algorithm
- **Integration Tests**: Real browser + Hearing Engine; login flow full event capture
- **Reproducibility Tests**: Touch Engine with seed; run twice; compare action sequences
- **Dead Click Tests**: Disabled button click; stuck overlay click; detection verified

## 23. Extension Impact

- **Extension UI Changes**: Hearing timeline panel in Visualizer VIR view (Phase 8)
- **Affected ViewModels**: Event timeline component

## 24. Complexity Estimation

- **Implementation Complexity**: High (event correlation is the most complex part)
- **Estimated Refactoring Percentage**: 5% existing / 95% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 2 (Sensory)
- **Milestones**: Phase 2: console + network + deterministic touch; Phase 3: correlation + auth + state; Phase 5: human simulation
- **Prerequisites**: FEAT-056 (Event Bus), FEAT-057 (Browser Adapter)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| What does Hearing mean? | Browser/runtime/application event observation (not microphone/audio) |
| Audio testing? | Optional adapter when feature explicitly includes audio |
| Touch modes? | Mode A Deterministic + Mode B Human Simulation (seeded) |
| Speech features? | Out of scope for default core; future optional adapter |

## 27. Requirement Readiness Score

- **Score**: 96/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: Clarification answers Q1 (Hearing), Q3 (Touch); Playwright documentation
- **Existing Architecture Summary**: Browser Adapter wraps Playwright; CDP events available for all required observations

## 29. Existing Modules & Services

| Module | Location | Owner | Reuse % | Mod. % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|
| frontend-visual-debug (console checks) | skills/frontend-visual-debug/ | Skill | 5% | 95% | Low | Replaced by Hearing Engine |
| Browser Adapter | vir_runtime/adapters/browser/ | VIR | 70% | 30% | Low | Hearing uses Browser Adapter |

## 32. Selected Solution

- **Architecture**: Hearing Engine as asyncio coroutine subscribed to Browser Adapter event streams; Touch Engine as command executor using Browser Adapter action APIs; both publish to `vir.evidence.hearing.*` and `vir.evidence.touch.*` event bus topics.

## 33. Risks & Assumptions

- **Risks**: R-01 through R-05 from Section 17.
- **Assumptions**:
  - A-01: Playwright CDP gives access to all required network/console/lifecycle events
  - A-02: Framework State Adapters can observe state transitions in real-time

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Console.error captured with level, message, stack, timestamp evidence
- [ ] AC-02 (FR-03): HTTP 500 API response captured with URL, status, timing, body snippet
- [ ] AC-03 (FR-14): Login flow (network call + auth state + visual) correlated into single Observation Group
- [ ] AC-04 (FR-15): Button click evidence includes target selector, coordinates, pre/post timestamps
- [ ] AC-05 (FR-17): Human simulation with seed 42 produces identical 50-step sequence on two separate runs
- [ ] AC-06 (FR-21): Click on display:none element detected as dead click with evidence

## 35. Final Planning Prompt

### Problem Statement
VIR needs a Hearing Engine monitoring all browser runtime signals and a Touch Engine for deterministic and human-simulated interactions. Both engines publish structured Evidence to the event bus.

### Objectives
Implement full Hearing Engine (console, network, router, auth, state, performance, a11y); Touch Engine Mode A and Mode B; event correlation; dead click detection; optional audio adapter.

### Architectural Details
- `vir_runtime/engines/hearing/hearing_engine.py` — Signal collection orchestration
- `vir_runtime/engines/hearing/correlator.py` — Event correlation by time + request ID
- `vir_runtime/engines/hearing/signals/` — console.py, network.py, router.py, auth.py, state.py, lifecycle.py, performance.py
- `vir_runtime/engines/hearing/adapters/audio_adapter.py` — Optional audio
- `vir_runtime/engines/touch/touch_engine.py` — Interaction orchestration
- `vir_runtime/engines/touch/modes/deterministic.py` — Mode A
- `vir_runtime/engines/touch/modes/human_simulation.py` — Mode B (seeded)
- `vir_runtime/engines/touch/recorder.py` — Action recording

### Verification Checklist
- [ ] docs/plans/FEAT-059_vir_hearing_touch_engines_plan.md generated and approved
- [ ] docs/designs/FEAT-059_vir_hearing_touch_engines_blueprint.md generated and approved
