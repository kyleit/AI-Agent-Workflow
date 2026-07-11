<!-- docs/brainstorming/FEAT-068_vir_runtime_execution_modes.md -->

---
feature_id: FEAT-068
feature_name: Visual Intelligence Runtime — Runtime Execution Modes (CLI / IDE / CI / Daemon)
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-067_vir_accessibility_responsive_and_performance_observers.md
next_artifact: ../plans/FEAT-068_vir_execution_modes_plan.md
---

# Master Requirement Document – VIR Runtime Execution Modes

## 1. Feature ID & Name
- **Feature ID**: FEAT-068
- **Feature Name**: Visual Intelligence Runtime — Runtime Execution Modes (CLI / IDE / CI / Daemon)

## 2. Original Idea
Design and implement the four execution modes through which VIR is invoked: Local CLI (developer), IDE Integration (Visualizer extension), CI/CD Headless mode, and Optional Background Daemon mode. Each mode presents a different interface and configuration while running the same VIR core.

## 3. Business Problem
- **Problem**: VIR must serve radically different contexts: a developer running it locally wants real-time visual feedback; a CI pipeline needs silent execution with exit codes; the IDE extension needs live status events; a background daemon needs scheduled execution. Without proper mode support, VIR is useful only in one context.
- **Why it matters**: Adoption of VIR across the SDLC requires all four modes. CI integration is how VIR becomes a release gate. IDE integration is how VIR becomes part of the development loop.
- **Who is affected**: Developers, CI/CD systems, the Visualizer extension, the Release Manager Agent.
- **Expected outcome**: Four execution modes using the same VIR core, with mode-appropriate output, configuration, and integration.

## 4. Requirement Discovery

### Functional Requirements

#### Mode 1: Local CLI
- FR-01: CLI entry point: `python -m vir_runtime run --feature FEAT-XXX --url http://localhost:3000 --profile standard`.
- FR-02: CLI must display: live progress per investigation stage, real-time evidence count, active agents list, current stage, elapsed time.
- FR-03: CLI output must be human-readable with color coding (using ANSI codes; configurable).
- FR-04: CLI must produce final summary table: verdict, confidence, evidence count, finding count, report path.
- FR-05: CLI must support `--profile lightweight|standard|deep` option.
- FR-06: CLI must support `--headless` flag for local headless runs.
- FR-07: CLI must support `--watch` mode: continuous monitoring loop until stopped.

#### Mode 2: IDE / Visualizer Integration
- FR-08: IDE mode activated when Orchestrator detects IDE context or `--mode ide` flag.
- FR-09: Orchestrator emits structured JSON events on stdout/IPC channel for IDE extension to consume.
- FR-10: IDE events must include: stage_change, evidence_added, agent_status, twin_update, investigation_opened, verdict_issued, report_ready.
- FR-11: IDE extension must display: VIR status panel, agent health grid, investigation timeline, confidence gauge, screenshot viewer, evidence list.
- FR-12: IDE extension must show annotated screenshots for detected issues inline.
- FR-13: IDE integration must not require any browser extension — all data via VIR IPC events.

#### Mode 3: CI/CD Headless
- FR-14: CI mode activated via `--mode ci` flag or when no interactive terminal detected.
- FR-15: CI mode produces: minimal console output (progress dots only), final JSON report to configurable output path, exit code (0=PASS, 1=FAIL, 2=BLOCKED, 3=PARTIAL).
- FR-16: CI mode must complete within configurable maximum runtime (default: 10 minutes per feature).
- FR-17: CI mode uses Standard profile by default; configurable to Lightweight (fast) or Deep (thorough).
- FR-18: CI mode must not require any interactive input; any human escalation automatically produces BLOCKED result with explanation.
- FR-19: CI mode must produce a machine-readable summary for use in PR comment or notification.

#### Mode 4: Background Daemon (Optional)
- FR-20: Daemon mode: `python -m vir_runtime daemon --watch-feature FEAT-XXX --interval 60s`.
- FR-21: Daemon must poll for application changes (DOM fingerprint change) and trigger Lightweight observation.
- FR-22: Daemon must publish findings to event bus for IDE extension to consume.
- FR-23: Daemon must be stoppable via `python -m vir_runtime daemon stop`.
- FR-24: Daemon is optional; not required for Phase 1-8 delivery.

#### thin client (frontend-visual-debug) Integration
- FR-25: `frontend-visual-debug` skill invokes VIR via CLI with feature context; receives report; presents results.
- FR-26: Thin client provides: feature ID, blueprint path, application URL, profile preference, observation scope.
- FR-27: Thin client has < 100 LOC of logic (all intelligence in VIR).

### Non-functional Requirements
- NFR-01: CLI startup < 1.5s.
- NFR-02: IDE event latency < 100ms from VIR internal event to IDE display update.
- NFR-03: CI mode must not write to stdout anything except configured output (no debug noise).
- NFR-04: Daemon must use < 200MB RAM during idle monitoring.
- NFR-05: All modes must invoke exactly the same VIR core; no mode-specific investigation logic.

### Technical Constraints
- TC-01: Mode selection via CLI flag `--mode cli|ide|ci|daemon`.
- TC-02: IDE IPC: stdout JSON events (line-delimited JSON / ndjson format).
- TC-03: CI exit codes: 0=PASS, 1=FAIL, 2=BLOCKED, 3=PARTIAL.
- TC-04: Daemon uses Python schedule or asyncio task loop.
- TC-05: Thin client: `.agents/skills/frontend-visual-debug/SKILL.md` updated to invoke `python -m vir_runtime run`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | CLI entry point | BP-VIR-014 | Run CLI with known URL | VIR starts; investigation begins |
| FR-02 | Must | CLI live progress | BP-VIR-014 | Run CLI Standard profile | Stage progress visible in terminal |
| FR-15 | Must | CI exit code | BP-VIR-014 | Known FAIL scenario in CI mode | Exit code 1 returned |
| FR-18 | Must | CI no interactive input | BP-VIR-014 | Escalation needed in CI | BLOCKED result with explanation |
| FR-25 | Must | Thin client integration | BP-VIR-014 | frontend-visual-debug invokes VIR | VIR runs; report returned to thin client |
| FR-27 | Must | Thin client < 100 LOC | BP-VIR-014 | Line count check | frontend-visual-debug/SKILL.md logic < 100 LOC |
| FR-09 | Should | IDE IPC events | BP-VIR-014 | IDE extension receives stage_change event | Event parsed; UI updated |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Frontend Developers | Primary | High | High | CLI mode for local feedback during development |
| CI/CD Pipeline | Primary | Critical | Critical | Exit codes + headless mode |
| Release Manager Agent | Primary | High | High | CI gate verdict |
| Visualizer Extension | Secondary | High | High | IDE mode for live investigation status |
| frontend-visual-debug | Internal | High | High | Thin client integration |

## 7. Scope Boundary

### In Scope
- CLI mode with live progress
- CI/CD headless mode with exit codes
- IDE IPC event protocol
- Daemon mode (optional; Phase 8+)
- Thin client integration
- frontend-visual-debug refactor to thin client

### Out of Scope
- Visualizer extension UI implementation (Extension Engineering task, separate from VIR)
- CI/CD pipeline YAML configuration (DevOps task)

### Deferred Scope
- Daemon mode (optional)
- Web-based report viewer

### Future Scope
- VS Code language server protocol integration
- Remote VIR execution (cloud-hosted VIR for CI)

## 8. Dependency Graph Preview

- FEAT-068: Execution Modes (Must)
  - FEAT-056: VIR Core + Orchestrator (prerequisite)
  - FEAT-066: Quality Gates + Reports (provides exit codes and reports)
  - Extension Visualizer (consumer of IDE IPC events)

## 9. Data Flow Preview

**CI Mode Flow:**
```
CI Pipeline: pytest/npm test → calls python -m vir_runtime run --mode ci --feature FEAT-055 --url http://staging:3000
VIR starts → headless investigation → Gate evaluates → FAIL
Stdout: {"verdict": "FAIL", "confidence": 0.91, "report": "...path"}
Exit code: 1
CI pipeline: marks build as failed; attaches JSON report to PR
```

**IDE Mode Flow:**
```
Developer edits code → saves → IDE extension triggers VIR
VIR starts → publishes ndjson to stdout: {"event":"stage_change","stage":"observe","timestamp":"..."}
IDE extension parses → updates VIR status panel → shows active stage
VIR concludes → {"event":"verdict_issued","verdict":"PASS","confidence":0.94}
IDE extension: shows green checkmark in status bar
```

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-visual-debug SKILL.md | `.agents/skills/frontend-visual-debug/` | Refactor | Becomes thin client; invokes VIR CLI |
| Visualizer extension | `extensions/visualizer/` | Extend | New VIR status panel consuming IPC events |
| workflow_runtime.py CLI patterns | scripts/ | Reuse | CLI entry point patterns |

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: frontend-visual-debug (major refactor)
- **Affected Extension**: Visualizer extension (new VIR panel)
- **Impact Level**: High — defines the external interface of VIR

## 12. Migration Strategy

- **Backward Compatibility**: frontend-visual-debug external invocation interface preserved; only internals change
- **Migration Phases**: Phase 8 delivers CLI + CI modes; Phase 8 also delivers IDE mode events

## 13. Architecture Principles

- **Script First**: CLI is primary interface
- **API First**: IDE IPC event schema published before Visualizer extension implements consumer
- **Backward Compatibility**: Thin client API stable; VIR version upgrades transparent to skill callers

## 14. Non Goals

- Execution modes do not change VIR investigation logic
- CLI does not expose all internal VIR settings (only user-facing configuration)
- IDE mode does not run a separate VIR process per IDE event (runs shared VIR session)

## 15. ROI Analysis

- **CI Value**: Automated gate enforcement in every PR pipeline
- **Developer Value**: Real-time local feedback eliminates "works on my machine" visual bugs
- **Adoption**: Multi-mode support removes friction for every team member to use VIR

## 16. Success Metrics

- **CLI Startup**: < 1.5s to first progress output
- **CI Exit Code**: 100% accurate on all test scenarios
- **IDE Event Latency**: < 100ms from VIR event to IDE display
- **Thin Client LOC**: < 100 LOC in frontend-visual-debug after refactor

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| CI timeout on complex investigations | High | High | Configurable max runtime; BLOCKED result if exceeded | Infrastructure |
| IDE IPC event flood overwhelms extension | Medium | Medium | Event throttling; configurable event verbosity | Extension Engineer |
| Thin client breaking change during VIR upgrade | High | Low | Thin client API versioned; VIR publishes migration guide | Backend Engineer |

## 18. Technical Questions

- Should IDE IPC use stdout ndjson or a named pipe / socket for lower latency?
- What is the configurable maximum CI runtime default?
- Should Daemon mode support multiple features simultaneously?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| IDE IPC: stdout vs socket | Pending | stdout ndjson for simplicity; socket for Phase 9 latency optimization |
| CI max runtime default | Pending | 10 minutes per feature; configurable |
| Daemon multi-feature | Pending | Single feature per daemon instance in Phase 8; multiple features Phase 10 |

## 20. ADR Detection

- **ADR Required**: No — execution mode design follows AIWF CLI-first convention

## 21. Knowledge Update Impact

- **architecture**: Yes — VIR execution mode architecture
- **patterns**: Yes — ndjson IPC pattern; thin client pattern

## 22. Test Strategy Preview

- **Unit Tests**: CLI argument parsing; exit code mapping; ndjson serialization
- **Integration Tests**: Full VIR run in each mode on test scenarios
- **CI Tests**: GitHub Actions / GitLab CI YAML that invokes VIR; exit code gate
- **IDE Tests**: IDE extension receives and parses all 8 IPC event types

## 23. Extension Impact

- **Extension UI Changes**: VIR status panel (significant); stage indicator; screenshot viewer; verdict badge
- **Affected ViewModels**: VIR panel state machine; IPC event handler; screenshot loader

## 24. Complexity Estimation

- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 20% existing (thin client refactor) / 80% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 8 (IDE Integration) + Phase 9 (CI/CD)
- **Prerequisites**: FEAT-066 (reports/exit codes), FEAT-056 (core runtime)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Execution modes? | CLI, IDE, CI/CD, Daemon (optional) |
| Same VIR core for all modes? | Yes — modes only change input/output interface |
| CI exit codes? | 0=PASS, 1=FAIL, 2=BLOCKED, 3=PARTIAL |
| thin client responsibilities? | Context preparation + VIR invocation + result presentation |

## 27. Requirement Readiness Score

- **Score**: 94/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): CLI run with valid URL and feature ID → VIR starts within 1.5s
- [ ] AC-02 (FR-15): CI mode FAIL scenario → exit code 1; JSON report at configured path
- [ ] AC-03 (FR-18): Human escalation needed in CI → BLOCKED result; no interactive prompt
- [ ] AC-04 (FR-25): frontend-visual-debug invokes VIR CLI; receives report; presents to user
- [ ] AC-05 (FR-27): frontend-visual-debug logic < 100 LOC after refactor

## 35. Final Planning Prompt

### Problem Statement
VIR needs 4 execution modes (CLI, IDE, CI, Daemon) using the same core runtime. frontend-visual-debug becomes a thin client. Visualizer extension consumes IDE IPC events.

### Architectural Details
- `vir_runtime/__main__.py` — CLI entry point
- `vir_runtime/cli/cli.py` — Argument parsing; mode selection
- `vir_runtime/modes/cli_mode.py` — Rich terminal output
- `vir_runtime/modes/ci_mode.py` — Silent + exit code
- `vir_runtime/modes/ide_mode.py` — ndjson IPC events
- `vir_runtime/modes/daemon_mode.py` — Background polling (optional)
- `.agents/skills/frontend-visual-debug/SKILL.md` — Refactored thin client (< 100 LOC)

### Verification Checklist
- [ ] docs/plans/FEAT-068_vir_execution_modes_plan.md generated and approved
- [ ] docs/designs/FEAT-068_vir_execution_modes_blueprint.md generated and approved
