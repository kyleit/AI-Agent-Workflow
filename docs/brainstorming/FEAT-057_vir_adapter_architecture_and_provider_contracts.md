<!-- docs/brainstorming/FEAT-057_vir_adapter_architecture_and_provider_contracts.md -->

---
feature_id: FEAT-057
feature_name: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-056_vir_runtime_core_and_event_bus.md
next_artifact: ../plans/FEAT-057_vir_adapter_architecture_plan.md
---

# Master Requirement Document – VIR Adapter Architecture & Provider Contracts

## 1. Feature ID & Name
- **Feature ID**: FEAT-057
- **Feature Name**: Visual Intelligence Runtime — Adapter Architecture & Provider Contracts

## 2. Original Idea
Design the complete provider-agnostic adapter layer for VIR. Every VIR capability — browser automation, vision analysis, application state inspection, storage, and memory — must be accessed through a defined adapter interface. No VIR core component may import a concrete provider directly.

## 3. Business Problem
- **Problem**: Tightly coupling VIR to Playwright, Pixelmatch, or any specific framework would create an unmaintainable system that breaks every time a provider updates its API, or when a new browser technology becomes dominant. The adapter layer is what makes VIR future-proof and extensible.
- **Why it matters**: The 12 additional architectural directives explicitly require provider-agnosticism as a hard constraint. Every adapter interface is a stability guarantee for the entire VIR system.
- **Who is affected**: All VIR engineers, all agents that consume provider capabilities, future teams adding new providers.
- **Expected outcome**: A clean adapter registry with provider contracts for Browser, Vision, State, Storage, and Memory capabilities — all swappable at configuration level.

## 4. Requirement Discovery

### Functional Requirements
- FR-01: Every VIR capability must be accessed through a named adapter interface. No direct provider imports in VIR core.
- FR-02: Browser Adapter must abstract: page navigation, DOM inspection, screenshot capture, console log collection, network monitoring, event injection, viewport resize, device emulation.
- FR-03: Vision Adapter must support layered analysis: DOM inspection, pixel diff, OCR, VLM semantic analysis, optional CV model.
- FR-04: State Adapter must extract framework-specific application state: React DevTools state, Vue reactive state, Svelte store state, Angular state.
- FR-05: Storage Adapter must support: filesystem binary storage, SQLite structured storage, optional Redis cache.
- FR-06: Memory Adapter must support: local files, SQLite, Qdrant (semantic), Knowledge Runtime, optional Obsidian.
- FR-07: VIR must implement an Adapter Registry: named adapters registered, discovered, and validated at startup.
- FR-08: All adapter implementations must satisfy their interface contract (Python Protocol) or fail at registration.
- FR-09: Adapters must be selectable via VIR configuration (YAML or JSON config file).
- FR-10: Adapters must support capability declaration: an adapter declares which optional capabilities it supports.
- FR-11: VIR must degrade gracefully when an optional adapter capability is unavailable (e.g., no VLM available → skip Layer 4 vision).
- FR-12: Browser Adapter must support both headed (local development) and headless (CI/CD) modes.
- FR-13: Plugin Discovery & Registration: Dynamically scan `.agents/visual-runtime/plugins/` for custom third-party adapters at runtime, validation is required.
- FR-14: Plugin Capability & Dependency Declaration: Each plugin must declare supported capabilities (e.g. `take_screenshot`, `execute_js`) and explicit dependencies on libraries/other adapters.
- FR-15: Compatibility & Trust Levels: Enforce compatibility checks (VIR version match). Support trust level classification: standard plugins are isolated, trusted plugins have broad access.
- FR-16: Lifecycle management for plugins: Support dynamic initialization, health checks, runtime disable/unload, and runtime fallback to built-in adapters.
- FR-17: Runtime API & SDK Contracts: Expose public Python API bindings (`import vir_runtime`) with stable method structures, complete error structures, cancellation support (via async tasks), and streamable progress hooks.

### Non-functional Requirements
- NFR-01: Adapter initialization overhead < 500ms per adapter.
- NFR-02: Adapter interface must be stable across VIR minor versions.
- NFR-03: Adding a new adapter implementation must require zero changes to VIR core.
- NFR-04: All adapters must be independently testable with mock/stub implementations.
- NFR-05: Adapter configuration must be validated at startup; invalid config fails fast with clear error message.

### Technical Constraints
- TC-01: Adapter interfaces defined using Python Protocol (PEP 544) for structural subtyping.
- TC-02: Playwright is the default browser adapter implementation.
- TC-03: Pixelmatch (via subprocess or Python wrapper) is the default pixel diff implementation.
- TC-04: Adapter configuration file: `.agents/visual-runtime/config/adapters.yaml`.
- TC-05: Adapter Registry is part of the VIR core (not a separate service).

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | No direct provider imports in core | BP-VIR-003 | Import audit: grep for provider names in core | Zero direct provider imports in vir_runtime/core/ |
| FR-02 | Must | Browser Adapter interface | BP-VIR-003 | Stub adapter passes all interface tests | Stub replaces Playwright without core changes |
| FR-03 | Must | Vision Adapter layered analysis | BP-VIR-004 | Each layer independently callable | Layer 1 works without Layer 4 available |
| FR-04 | Must | State Adapter per framework | BP-VIR-003 | React state extracted; Vue state extracted | Framework state matches DevTools output |
| FR-07 | Must | Adapter Registry | BP-VIR-003 | Register, discover, validate adapters | Invalid adapter fails registration |
| FR-10 | Must | Capability declaration | BP-VIR-003 | Adapter with no VLM declares capability=False | VIR skips VLM layer; no error |
| FR-11 | Must | Graceful degradation | BP-VIR-003 | Run with no OCR adapter | System runs; OCR steps skipped with warning |
| FR-12 | Must | Headed/headless browser mode | BP-VIR-003 | CI run uses headless; dev uses headed | Same adapter; mode set in config |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Vision Engine | Internal | Critical | Critical | VLM, Pixelmatch, OCR via clean adapter interface |
| Hearing Engine | Internal | High | High | Browser console/network via Browser Adapter |
| Touch Engine | Internal | High | High | User interactions via Browser Adapter |
| State Observer | Internal | High | High | Framework state via State Adapter |
| Memory Engine | Internal | High | High | Persistence via Storage + Memory Adapters |
| Future Engineers | Future | High | Medium | Add new providers without touching core |

## 7. Scope Boundary

### In Scope
- All adapter interface definitions (Protocol classes)
- Adapter Registry and validation
- Adapter configuration system
- Default adapter implementations: Playwright browser, Pixelmatch pixel diff, filesystem storage, SQLite storage, Qdrant memory
- Capability declaration mechanism
- Graceful degradation behavior

### Out of Scope
- Individual engine internal implementations (FEAT-058, FEAT-059, FEAT-060)
- OCR and VLM model implementations (FEAT-058)
- Optional adapters: Selenium, Puppeteer, PostgreSQL, Redis (deferred)

### Deferred Scope
- Selenium and Puppeteer browser adapters
- PostgreSQL and Redis storage adapters
- Voice/audio specialized adapters
- Remote desktop / screen capture adapters

### Future Scope
- gRPC-based remote adapter execution
- Cloud-hosted VLM adapter (OpenAI Vision, Claude Vision, Gemini Vision)

## 8. Dependency Graph Preview

- FEAT-057: Adapter Architecture (Must — prerequisite for all sensors)
  └── FEAT-058: Vision Engine (consumes Vision Adapter)
  └── FEAT-059: Hearing & Touch (consumes Browser Adapter)
  └── FEAT-060: Digital Twin (consumes State Adapter)
  └── FEAT-064: Memory (consumes Storage + Memory Adapters)

## 9. Data Flow Preview

- VIR config loaded → Adapter Registry initialized
  └── Registry reads adapters.yaml → validates each adapter class
      └── For each adapter: instantiate → call capability_check() → store in registry
          └── Vision Engine requests vision adapter
              └── Registry returns configured adapter (e.g., PixelmatchAdapter)
                  └── PixelmatchAdapter.compare(baseline, current) → DiffResult
                      └── DiffResult published as evidence event

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Qdrant connector | `.agents/skills/workflow-runtime/scripts/connectors/` | Extend | Implement as MemoryAdapter concrete class |
| db.py SQLite | `.agents/skills/workflow-runtime/scripts/` | Extend | Implement as StorageAdapter concrete class |
| Playwright (external) | pip: playwright | Wrap | BrowserAdapter implementation |

## 11. Dependency & Blast Radius Analysis

- **Affected Components**: All VIR engines (Vision, Hearing, Touch, State, Memory)
- **Affected Configuration**: New `adapters.yaml` configuration file
- **Impact Level**: High — all VIR engines consume adapters

## 12. Migration Strategy

- **Backward Compatibility**: Adapter interfaces are new; no migration needed
- **Coexistence Period**: Stub adapters allow development without real providers
- **Deprecation Plan**: N/A
- **Migration Phases**: Phase 1 — define all interfaces; Phase 2 — implement default adapters; Phase 3 — validate with real providers

## 13. Architecture Principles

- **API First**: All adapter interfaces defined before any implementation
- **Provider First**: Core never imports concrete adapter; only interface
- **Replaceable Providers**: Any adapter implementation swappable via config
- **Incremental Updates**: Adapters added incrementally; existing ones stable

## 14. Non Goals

- Adapter layer is not a general integration platform for AIWF
- Does not manage external service lifecycle (Playwright browser server managed by BrowserAdapter)

## 15. ROI Analysis

- **Estimated Implementation Cost**: Medium (2 sprints for all interface definitions + default implementations)
- **Runtime Savings**: Future adapter additions cost near-zero due to clean interface
- **Maintenance Impact**: Single adapter interface = stable contract; provider changes isolated to adapter class
- **Long-Term ROI**: Very high — every new capability (new VLM, new browser, new DB) requires only a new adapter class

## 16. Success Metrics

- **Provider Independence**: Zero direct provider imports in VIR core (verified by linter rule)
- **Degradation**: System operates in Lightweight profile when only Browser Adapter available
- **Extension**: New adapter added in < 1 hour by following Protocol interface
- **Config Validation**: Invalid adapter config fails in < 100ms with actionable error

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Adapter interface too rigid for diverse providers | High | Medium | Use capability declaration; optional methods clearly marked | Architect |
| Provider API change breaks adapter | Medium | High | Adapter tests run on provider update; version pinning | Infrastructure |
| VLM provider unavailable in CI | Medium | High | Graceful degradation; CI uses Standard profile by default | Infrastructure |
| State adapter framework detection incorrect | Medium | Medium | Explicit framework config option; auto-detection as fallback | Frontend Engineer |

## 18. Technical Questions

- Should State Adapters use browser devtools protocol directly or inject JavaScript helpers?
- How should the Vision Adapter handle the Layer 1→2→3→4 pipeline internally (sequential or concurrent)?
- Should adapter configuration support hot-reload during a VIR session?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| State Adapter: DevTools vs injected JS | Pending | Playwright DevTools preferred; fallback to injected JS; decide in BP-VIR-003 |
| Vision pipeline: sequential vs concurrent | Pending | Sequential by default (cheaper); concurrent in Deep profile; decide in BP-VIR-004 |
| Adapter hot-reload | Pending | Deferred; Phase 3 enhancement |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-003: Provider-agnostic adapter pattern vs direct provider usage

## 21. Knowledge Update Impact

- **patterns**: Yes — Provider Adapter pattern documented
- **architecture**: Yes — VIR adapter layer architecture
- **ADR**: Yes — ADR-VIR-003
- **modules**: Yes — vir_runtime/adapters/ module tree

## 22. Test Strategy Preview

- **Unit Tests**: Each adapter interface contract (Protocol compliance); capability declaration; config validation
- **Integration Tests**: Real Playwright adapter with live browser; Real Pixelmatch with sample images
- **Stub/Mock Tests**: All VIR engines tested with stub adapters (no real browser required)
- **Degradation Tests**: Run VIR with minimal adapters; verify graceful operation

## 23. Extension Impact

- **Extension UI Changes**: None directly; adapter status visible in VIR status panel (FEAT-068)
- **Affected ViewModels**: None

## 24. Complexity Estimation

- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 0% existing / 100% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 1 (Foundation) + Phase 2 (Sensory)
- **Milestones**: All adapter interfaces defined before any engine implementation begins
- **Prerequisites**: FEAT-056 (Event Bus + Orchestrator)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Default browser automation? | Playwright; abstracted behind BrowserAdapter |
| Framework state extraction method? | DevTools protocol preferred; injected JS as fallback |
| Vision layers concurrent or sequential? | Sequential default; concurrent in Deep profile |
| VLM required for MVP? | No; optional Layer 4; system degrades gracefully |

## 27. Requirement Readiness Score

- **Score**: 94/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: FEAT-045 (Knowledge Runtime provider patterns); existing Qdrant connector in connectors/
- **Existing Architecture Summary**: Provider pattern already used in knowledge-runtime (FEAT-045); adapter concept familiar to AIWF architecture

## 29. Existing Modules & Services

| Module | Location | Owner | Public APIs | Est. Reuse % | Est. Mod. % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| connectors/qdrant.py | `.agents/skills/workflow-runtime/scripts/connectors/` | Runtime | query(), upsert() | 70% | 30% | Low | MemoryAdapter base |
| db.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | execute(), query() | 60% | 40% | Low | StorageAdapter base |

## 30. Solution Options Evaluated

### Option A: Abstract Base Classes (ABC)
- **Overview**: Use Python ABC for all adapter interfaces; concrete classes inherit
- **Advantages**: Familiar OOP pattern; strong inheritance guarantees
- **Disadvantages**: Rigid inheritance hierarchy; cannot use duck typing; verbose

### Option B: Python Protocol (PEP 544) + Runtime Validation (SELECTED)
- **Overview**: Use Protocol for structural subtyping; runtime validation on registration
- **Advantages**: Duck typing; no inheritance required; clean; modern Python; allows third-party adapters without subclassing
- **Disadvantages**: Static analysis requires mypy; runtime validation needed as safety net

### Option C: Plugin Registry with Dynamic Loading
- **Overview**: Adapters as entry_points plugins; loaded dynamically by name
- **Advantages**: True plugin ecosystem; zero code change to add provider
- **Disadvantages**: Overkill for MVP; setup.py/pyproject.toml overhead; complex debugging

## 31. Solution Comparison Table

| Criteria | A: ABC | B: Protocol + Runtime (Selected) | C: Plugin Registry |
|---|---|---|---|
| Complexity | Low | Medium | High |
| Flexibility | Low | High | Very High |
| Static Type Safety | High | High (with mypy) | Medium |
| MVP Speed | Medium | High | Low |
| Third-party extension | Hard | Easy | Very Easy |

## 32. Selected Solution

- **Choice**: Option B — Python Protocol + Runtime Validation
- **Why**: Protocol allows any class to satisfy the interface without inheritance; supports third-party adapters naturally; runtime validation catches missing methods at startup not at usage time; aligns with modern Python practices
- **Trade-offs Accepted**: Requires mypy for static analysis; runtime check adds ~10ms per adapter
- **Technical Debt**: If adapters proliferate, plugin registry (Option C) may be added as Phase 5 enhancement

## 33. Risks & Assumptions

- **Risks**:
  - R-01: Protocol methods incompletely implemented → Mitigation: Runtime validator checks all required methods
  - R-02: VLM API rate limits in Deep profile → Mitigation: VLM calls rate-limited; queued; timeout per call
- **Assumptions**:
  - A-01: Playwright stable API for at least 12 months
  - A-02: Python Protocol sufficient for all adapter patterns needed in MVP

## 34. Acceptance Criteria

- [ ] AC-01: Import audit confirms zero direct provider imports in vir_runtime/core/
- [ ] AC-02: Stub BrowserAdapter passes all interface tests; Playwright adapter passes same tests
- [ ] AC-03: Invalid adapter config rejected at startup with actionable error in < 100ms
- [ ] AC-04: VIR runs full Lightweight profile with only BrowserAdapter + SQLiteStorageAdapter
- [ ] AC-05: New adapter class added; registered in config; used by VIR without any core file changes

## 35. Final Planning Prompt

### Problem Statement
VIR needs a complete provider-agnostic adapter layer. All capabilities (browser, vision, state, storage, memory) must be accessed through Protocol interfaces. No concrete provider imported in core.

### Objectives & Selected Solution
Python Protocol interfaces for all adapter types; Adapter Registry with startup validation; graceful degradation when adapters unavailable; default implementations: Playwright, Pixelmatch, SQLite, Qdrant.

### Architectural Details
- `vir_runtime/adapters/base/` — Protocol interface definitions
- `vir_runtime/adapters/browser/playwright_adapter.py`
- `vir_runtime/adapters/vision/pixelmatch_adapter.py`
- `vir_runtime/adapters/vision/ocr_adapter.py`
- `vir_runtime/adapters/vision/vlm_adapter.py`
- `vir_runtime/adapters/state/react_adapter.py`, `vue_adapter.py`, `svelte_adapter.py`, `angular_adapter.py`
- `vir_runtime/adapters/storage/sqlite_adapter.py`, `filesystem_adapter.py`
- `vir_runtime/adapters/memory/qdrant_adapter.py`, `knowledge_runtime_adapter.py`
- `vir_runtime/adapters/registry.py` — Adapter Registry

### Verification Checklist
- [ ] docs/plans/FEAT-057_vir_adapter_architecture_plan.md generated and approved
- [ ] docs/designs/FEAT-057_vir_adapter_architecture_blueprint.md generated and approved
