<!-- docs/brainstorming/FEAT-060_vir_digital_twin_and_application_state_model.md -->

---
feature_id: FEAT-060
feature_name: Visual Intelligence Runtime — Digital Twin & Application State Model
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-059_vir_hearing_engine_and_touch_engine.md
next_artifact: ../plans/FEAT-060_vir_digital_twin_plan.md
---

# Master Requirement Document – VIR Digital Twin & Application State Model

## 1. Feature ID & Name
- **Feature ID**: FEAT-060
- **Feature Name**: Visual Intelligence Runtime — Digital Twin & Application State Model

## 2. Original Idea
Design and implement VIR's internal Digital Twin — a continuously maintained, multi-dimensional model of the running application's complete state. VIR may only conclude that an application is healthy when the Digital Twin is internally consistent across all 11 state dimensions.

## 3. Business Problem
- **Problem**: Current testing approaches check individual dimensions in isolation (visual OR network OR state), missing cross-dimension inconsistencies. A login that visually shows the dashboard but has no auth token in storage is a bug invisible to any single-dimension checker. The Digital Twin aggregates all dimensions and detects cross-cutting inconsistencies that single-layer inspection cannot find.
- **Why it matters**: Real-world bugs often manifest as cross-dimension inconsistencies. The Digital Twin is VIR's model of "ground truth" and the primary source for the Contradiction Engine.
- **Who is affected**: Contradiction Engine, Self-Doubt Engine, Consensus Engine, Evidence Engine, Business Intelligence Engine, all Cognitive agents.
- **Expected outcome**: An always-consistent, multi-dimensional internal model of the application that serves as the authoritative reference for all VIR reasoning.

## 4. Requirement Discovery

### Functional Requirements
- FR-01: Digital Twin must maintain 11 state dimensions simultaneously:
  1. **Visual State**: Current rendered layout, element positions, component tree, visibility map
  2. **Application State**: Framework store state (Redux/Pinia/Svelte stores/Angular state)
  3. **Business State**: Current step in business flows (checkout, registration, onboarding, etc.)
  4. **Navigation State**: Current route, breadcrumb, history stack, back/forward capability
  5. **Authentication State**: Login status, user identity, roles, permissions, session validity
  6. **Permission State**: Feature flags, access control, role-based visibility
  7. **Data State**: Key data entities loaded (user profile, cart contents, form values, lists)
  8. **Interaction State**: Last user action, pending actions, form dirty state, modal open/close
  9. **Performance State**: Current LCP, FCP, CLS, layout shift score, memory usage
  10. **Accessibility State**: ARIA tree, focus position, live region announcements, contrast map
  11. **Responsive State**: Current viewport, active breakpoint, media query matches
- FR-02: Digital Twin updates must be triggered by Evidence events from all sensory agents.
- FR-03: Digital Twin must implement an internal consistency checker: detect when two dimensions report contradictory facts.
- FR-04: When inconsistency detected, Digital Twin must publish `twin.inconsistency.detected` event with affected dimensions, contradicting observations, and severity.
- FR-05: Digital Twin must maintain an update history (last N updates per dimension) for temporal reasoning.
- FR-06: Digital Twin must compute an overall Application Health Score (0.0–1.0) based on dimension consistency.
- FR-07: Digital Twin state must be persisted to SQLite at configurable intervals and on investigation close.
- FR-08: Digital Twin must support partial updates: receiving evidence for one dimension must not invalidate others.
- FR-09: Digital Twin must expose a query interface for other agents to read specific dimensions.
- FR-10: Digital Twin must detect stale state: dimensions not updated within configurable staleness window trigger `twin.dimension.stale` event.

### Non-functional Requirements
- NFR-01: Digital Twin update latency < 50ms per evidence event received.
- NFR-02: Digital Twin must handle concurrent evidence updates without state corruption (asyncio task safety).
- NFR-03: Digital Twin consistency check must run < 100ms per update cycle.
- NFR-04: Digital Twin persisted state loadable within 500ms at session resume.
- NFR-05: Digital Twin must not block event bus producers; updates processed asynchronously.

### Technical Constraints
- TC-01: Digital Twin implemented as a single asyncio-managed state object (thread-safe via asyncio lock).
- TC-02: State update strategy: last-write-wins per dimension sub-field with evidence timestamp ordering.
- TC-03: Inconsistency detection uses declarative consistency rules defined in configuration.
- TC-04: SQLite persistence: `vir_digital_twin` table with session ID, dimension, timestamp, state JSON, evidence ID.
- TC-05: History buffer: last 50 updates per dimension (configurable).

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | All 11 dimensions maintained | BP-VIR-006 | Populate all 11 dimensions; query each | All dimensions return valid data |
| FR-03 | Must | Consistency checker | BP-VIR-006 | Inject contradictory auth state + visual state | Inconsistency event published within 100ms |
| FR-04 | Must | Inconsistency event | BP-VIR-006 | Contradiction Engine subscribed; receives event | Event includes dimensions, evidence refs, severity |
| FR-05 | Must | Update history | BP-VIR-006 | 60 updates to one dimension | Last 50 preserved; oldest dropped |
| FR-06 | Must | Health Score | BP-VIR-006 | Full consistent state → 1.0 score; 3 contradictions → < 0.5 | Score reflects inconsistency count |
| FR-07 | Must | SQLite persistence | BP-VIR-006 | Close session; reopen; load twin | State matches pre-close state |
| FR-09 | Must | Query interface | BP-VIR-006 | Agent queries `auth.is_authenticated` | Returns current auth state value |
| FR-10 | Must | Stale state detection | BP-VIR-006 | Stop auth events; wait 30s | `twin.dimension.stale` event published |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Contradiction Engine | Internal | Critical | Critical | Inconsistency events to trigger investigation |
| Business Intelligence Engine | Internal | High | High | Business State dimension for flow validation |
| Consensus Engine | Internal | High | High | Application Health Score as quality gate input |
| Cognitive Investigation Engine | Internal | High | High | Multi-dimension query for root cause analysis |
| Self-Doubt Engine | Internal | High | High | Stale state detection for hypothesis revision |
| Reporting System | Internal | Medium | Medium | Current twin state in final report |

## 7. Scope Boundary

### In Scope
- All 11 state dimensions
- Consistency rules and checker
- Inconsistency event publication
- Update history
- Application Health Score
- SQLite persistence
- Stale state detection
- Query interface

### Out of Scope
- State extraction from browser (handled by Vision, Hearing, State Adapter agents)
- Contradiction investigation logic (FEAT-062)
- Business flow definition (FEAT-066 Quality Gates + Business Intelligence)

### Deferred Scope
- Cross-session Digital Twin comparison (regression between releases)
- Cloud-synchronized twin for team collaboration

### Future Scope
- Predictive state modeling (what state will be after next action)
- Automated business flow mapping from observed state transitions

## 8. Dependency Graph Preview

- FEAT-060: Digital Twin (Must)
  - FEAT-056: Event Bus (prerequisite — receives evidence events)
  - FEAT-058: Vision Engine (feeds Visual State dimension)
  - FEAT-059: Hearing Engine (feeds Auth, Nav, Performance, A11y, App State dimensions)
  - FEAT-057: State Adapters (feeds Application State dimension)
  - FEAT-061: Evidence Domain (twin updates trigger evidence records)
  - FEAT-062: Contradiction Engine (consumer of `twin.inconsistency.detected`)

## 9. Data Flow Preview

- Vision Engine publishes visual evidence
  └── Digital Twin receives → updates Visual State dimension
- Hearing Engine publishes auth evidence (login success)
  └── Digital Twin receives → updates Authentication State (is_authenticated=True)
- Vision Engine publishes visual evidence (login screen visible)
  └── Digital Twin receives → updates Visual State (current_page=login)
- Consistency Checker runs: Auth=authenticated + Visual=login_page → INCONSISTENCY
  └── `twin.inconsistency.detected` published with: auth_dimension × visual_dimension, severity=HIGH
      └── Contradiction Engine receives inconsistency → opens investigation
          └── Self-Doubt Engine challenges current conclusion → triggers re-observation

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| session.py state model | `.agents/skills/workflow-runtime/scripts/` | Reuse patterns | State management patterns |
| db.py SQLite | `.agents/skills/workflow-runtime/scripts/` | Extend | Digital Twin persistence schema |

## 11. Dependency & Blast Radius Analysis

- **Affected Agents**: All cognitive agents depend on Digital Twin query interface
- **Impact Level**: Critical — Digital Twin is the authoritative application model

## 12. Migration Strategy

- **Backward Compatibility**: Digital Twin is new; no migration needed
- **Migration Phases**: Phase 3 implements core twin; all dimensions; Phase 5+ adds business state mapping

## 13. Architecture Principles

- **Memory First**: Digital Twin consulted before making any observation-based conclusion
- **API First**: Twin query interface defined before any agent queries it
- **Incremental Updates**: Dimension updates are partial and non-destructive

## 14. Non Goals

- Digital Twin does not make decisions — it is a model, not a reasoner
- Digital Twin does not extract state itself — it only receives Evidence

## 15. ROI Analysis

- **Value**: Enables detection of impossible application states; foundation for all cross-dimension reasoning
- **Investigation Quality**: Every contradiction detected by twin eliminates hours of manual debugging
- **Long-Term ROI**: Twin becomes the universal application model for all AIWF verification work

## 16. Success Metrics

- **Consistency Check Latency**: < 100ms per update cycle
- **Contradiction Detection Rate**: > 99% on known contradictory state pairs
- **State Persistence**: Twin loadable from SQLite within 500ms after session restart
- **Query Interface**: 100% of agent dimension queries return within 10ms

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| asyncio lock contention on high-frequency updates | Medium | Medium | Lock-free dimension slots; batch update window | Backend Engineer |
| Stale state false positives (expected delay) | Medium | Medium | Configurable staleness window per dimension type | Runtime Engineer |
| Consistency rules become overly complex | High | Medium | Rules defined declaratively in YAML; versioned | Architect |
| Twin state grows unbounded over long sessions | Medium | Low | History buffer limit; dimension compaction | Database Engineer |

## 18. Technical Questions

- Should consistency rules be expressed as Python predicates or a DSL?
- What is the default staleness window for each dimension type?
- Should Digital Twin state be serialized incrementally (event sourcing) or as snapshots?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Consistency rule format | Pending | YAML predicate format recommended; decide in BP-VIR-006 |
| Staleness window defaults | Pending | Auth: 30s; Visual: 5s; Network: 10s; decide in BP-VIR-006 |
| Serialization: event-sourcing vs snapshot | Pending | Snapshot preferred for simplicity; incremental event log for deep replay |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-005: Snapshot vs event-sourcing for Digital Twin persistence

## 21. Knowledge Update Impact

- **patterns**: Yes — Digital Twin pattern; Multi-dimension consistency checker pattern
- **architecture**: Yes — Digital Twin architecture
- **ADR**: Yes — ADR-VIR-005
- **SQLite**: Yes — vir_digital_twin schema

## 22. Test Strategy Preview

- **Unit Tests**: Dimension update; consistency checker; Health Score calculation; stale detection
- **Integration Tests**: Full evidence pipeline → twin update → contradiction event
- **State Persistence Tests**: Session save/load; dimension integrity verification
- **Concurrency Tests**: 100 concurrent dimension updates; no lock contention; no corruption

## 23. Extension Impact

- **Extension UI Changes**: Digital Twin visualization panel in Visualizer (Phase 8) — dimension status grid
- **Affected ViewModels**: Twin health score gauge; dimension status indicators

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 0% existing / 100% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 3 (State + Digital Twin)
- **Milestones**: Phase 3 complete = all 11 dimensions updating + consistency checker working
- **Prerequisites**: FEAT-056, FEAT-058, FEAT-059 (sensory engines feeding twin)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| When can VIR declare application healthy? | Only when Digital Twin is internally consistent |
| What dimensions must be consistent? | All 11 listed in FR-01 |
| How are contradictions detected? | Cross-dimension consistency rules |
| Where is twin persisted? | SQLite with session-scoped records |

## 27. Requirement Readiness Score

- **Score**: 93/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): All 11 dimensions populated after full-page observation; no null values
- [ ] AC-02 (FR-03): Login state contradiction (API=authenticated, Visual=login page) detected within 100ms
- [ ] AC-03 (FR-06): Health Score = 1.0 on fully consistent state; drops below 0.5 on 3 active contradictions
- [ ] AC-04 (FR-07): Twin state persisted to SQLite; loaded correctly after session restart
- [ ] AC-05 (FR-10): Auth dimension not updated for 30s → `twin.dimension.stale` event published

## 35. Final Planning Prompt

### Problem Statement
VIR needs a Digital Twin maintaining 11 application state dimensions simultaneously, detecting cross-dimension inconsistencies, and publishing contradiction events.

### Objectives
All 11 dimensions; consistency checker; Health Score; SQLite persistence; stale detection; agent query interface.

### Architectural Details
- `vir_runtime/twin/digital_twin.py` — Main twin state manager
- `vir_runtime/twin/dimensions/` — 11 dimension handlers
- `vir_runtime/twin/consistency/` — Rule engine + checker
- `vir_runtime/twin/persistence/twin_db.py` — SQLite persistence

### Verification Checklist
- [ ] docs/plans/FEAT-060_vir_digital_twin_plan.md generated and approved
- [ ] docs/designs/FEAT-060_vir_digital_twin_blueprint.md generated and approved
