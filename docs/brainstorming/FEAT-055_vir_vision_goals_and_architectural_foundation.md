<!-- docs/brainstorming/FEAT-055_vir_vision_goals_and_architectural_foundation.md -->

---
feature_id: FEAT-055
feature_name: Visual Intelligence Runtime — Vision, Goals & Architectural Foundation
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-055_vir_foundation_plan.md
---

# Master Requirement Document – Visual Intelligence Runtime: Vision, Goals & Architectural Foundation

## 1. Feature ID & Name
- **Feature ID**: FEAT-055
- **Feature Name**: Visual Intelligence Runtime — Vision, Goals & Architectural Foundation

## 2. Original Idea
Transform the existing `frontend-visual-debug` skill into a Human-Level Visual Intelligence Runtime (VIR) capable of perceiving application state, understanding business flows, evaluating UI/UX quality, and reasoning about visual aesthetics — operating as an independent AI Runtime, not a testing tool.

## 3. Business Problem
- **Problem**: The current `frontend-visual-debug` skill is a procedural browser automation tool. It captures screenshots and checks console errors but has no ability to understand what it sees, reason about contradictions, or learn from history. It cannot detect semantic UI failures, aesthetic regressions, business flow breakdowns, or cross-domain contradictions without human guidance.
- **Why it matters**: As AI-driven development accelerates, the quality verification layer must become intelligent enough to reason like a human engineer. A script-based visual checker cannot scale to complex modern applications.
- **Who is affected**: AI agents in the SDLC pipeline, frontend developers, QA reviewers, the Release Manager agent, and all future agentic workflows that need autonomous UI validation.
- **Expected outcome**: VIR becomes the universal perception and reasoning runtime for the AIWF, serving as the autonomous eye, ear, and reasoning mind of the AI engineering workflow during implementation, debugging, and release phases.

## 4. Requirement Discovery

### Functional Requirements
- FR-01: VIR must be an independent runtime, not a skill. `frontend-visual-debug` becomes a thin client that invokes VIR.
- FR-02: VIR must operate with a perception-first philosophy: Observe → Understand → Reason → Investigate → Learn → Improve.
- FR-03: VIR must maintain a complete internal Digital Twin of the running application covering all state dimensions.
- FR-04: VIR must support four execution modes: Local CLI, IDE/Visualizer integration, CI/CD headless, and Optional Daemon.
- FR-05: VIR must support three adaptive execution profiles: Lightweight, Standard, and Deep Review.
- FR-06: VIR must never be coupled to a single browser, vision, state, storage, or memory technology.
- FR-07: All runtime intelligence must reside inside VIR. No intelligence in the thin client.
- FR-08: VIR must define explicit Agent Contracts for every internal agent.
- FR-09: VIR must support phased delivery: Foundation → Sensory → State → Vision & Design → Cognitive → Multi-Agent → Memory → IDE → CI → Advanced Adapters.
- FR-10: VIR must produce structured, machine-readable reports alongside human-readable reports.

### Non-functional Requirements
- NFR-01: **Latency**: Lightweight profile < 2s per observation; Standard < 10s per page; Deep is quality-first with configurable timeout.
- NFR-02: **Resource**: Default implementation must run without GPU. GPU acceleration optional.
- NFR-03: **Isolation**: Each agent must be independently testable and deployable.
- NFR-04: **Extensibility**: New adapters, agents, and capabilities must be addable without modifying the runtime core.
- NFR-05: **Reproducibility**: All randomness (human simulation) must be seeded and reproducible.
- NFR-06: **Observability**: All agent decisions, evidence, and investigations must be logged and traceable.
- NFR-07: **Safety**: VIR must never perform destructive actions without human confirmation.
- NFR-08: **Persistence**: Investigations must persist across runtime sessions.

### Technical Constraints
- TC-01: VIR runtime core must be implemented in Python, consistent with the project's script-first architecture.
- TC-02: Event bus must use asyncio-based local message passing; no external message broker in MVP.
- TC-03: Storage default: SQLite for structured data, filesystem for binary artifacts, Qdrant for semantic memory.
- TC-04: Browser automation default: Playwright adapter (but abstracted behind Provider interface).
- TC-05: VIR must integrate with the existing AIWF workflow runtime, checkpoint system, and approval gates.
- TC-06: VIR artifacts stored under `.agents/visual-runtime/`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | VIR is independent runtime; thin client only | BP-VIR-001 Runtime Architecture | Integration test: thin client invokes VIR via contract | VIR runs standalone without frontend-visual-debug |
| FR-02 | Must | Perception-first philosophy enforced | BP-VIR-002 Orchestrator | Unit: pipeline stages exist and execute in order | All 6 pipeline stages present in core |
| FR-03 | Must | Digital Twin maintained | BP-VIR-006 Digital Twin | Integration: state consistency check | Twin reflects all 11 state dimensions |
| FR-04 | Must | 4 execution modes | BP-VIR-014 Execution Modes | Smoke test each mode | CLI, IDE, CI, Daemon all invoke same core |
| FR-05 | Must | 3 adaptive profiles | BP-VIR-001 | Profile switching test | Profile selection changes active agent set |
| FR-06 | Must | Provider-agnostic architecture | BP-VIR-003 Adapter Architecture | Swap Playwright for stub adapter | Core works with any conforming adapter |
| FR-07 | Must | Intelligence only in VIR | BP-VIR-001 | Code audit: thin client has no reasoning logic | Thin client < 100 LOC |
| FR-08 | Must | Agent contracts defined | BP-VIR-011 Agent Contracts | Contract schema validation | All agents pass contract validation |
| FR-09 | Should | Phased delivery | Roadmap | Phase 1 delivers Foundation+Sensory | Phase 1 milestone met |
| FR-10 | Should | Machine-readable reports | BP-VIR-013 Reporting | JSON report schema validation | Report passes schema |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| AI Coding Agents (Coder, Reviewer) | Primary/Internal | High | Critical | Autonomous UI validation without human involvement |
| Frontend Developers | Primary | High | High | Accurate, reasoned UI bug reports with root causes |
| QA/Review Agents | Primary/Internal | High | High | Evidence-backed quality gate decisions |
| Release Manager Agent | Secondary/Internal | Medium | High | Confidence score to gate releases |
| AIWF Framework itself | Internal | High | Critical | Universal perception runtime for all future features |
| Future AI Agents | External/Future | High | Medium | Pluggable perception foundation |

## 7. Scope Boundary

### In Scope
- VIR core runtime architecture and lifecycle
- Event-driven multi-agent foundation
- Provider-agnostic adapter contracts
- Digital Twin model definition
- Perception pipeline (Observe → Learn)
- Phased delivery roadmap
- Evidence and Investigation domain objects
- Thinking pipeline definition
- Integration contracts with AIWF workflow runtime

### Out of Scope
- Implementation of individual engine internals (covered by FEAT-056 through FEAT-069)
- Production deployment infrastructure
- Cloud-native distribution
- Remote/distributed execution beyond local daemon

### Deferred Scope
- gRPC/microservice decomposition (Option C, deferred)
- Multi-machine distributed execution
- Public API for third-party integration

### Future Scope
- VIR as universal perception runtime beyond frontend (backend, infrastructure, security)
- LLM-driven planning agents
- Specialized security review agents

## 8. Dependency Graph Preview

- FEAT-055: VIR Foundation (Must)
  - FEAT-056: VIR Runtime Core & Event Bus (Must)
    - FEAT-057: VIR Adapter Architecture (Must)
      - FEAT-058: Vision Engine (Must)
      - FEAT-059: Hearing & Touch Engines (Must)
    - FEAT-060: Digital Twin & Application State (Must)
    - FEAT-061: Evidence & Investigation Domain (Must)
      - FEAT-062: Thinking Pipeline & Cognitive Engines (Must)
        - FEAT-063: Multi-Agent & Consensus Engine (Must)
          - FEAT-064: Memory Architecture & Continuous Learning (Should)
    - FEAT-065: Design Authority & Design Knowledge Base (Should)
    - FEAT-066: Quality Gates & Reporting (Must)
    - FEAT-067: Accessibility, Responsive & Performance Observers (Should)
  - FEAT-068: Runtime Execution Modes (Must)
  - FEAT-069: SDLC Integration & Future AI Capabilities (Should)

## 9. Data Flow Preview

- User/Agent invokes frontend-visual-debug thin client
  └── passes context (Feature ID, URL, Blueprint path) ──> VIR Orchestrator
      └── Orchestrator opens Investigation ──> Event Bus
          └── Event Bus activates agents ──> Sensory Agents (Vision, Hearing, Touch)
              └── Agents produce Evidence ──> Evidence Engine
                  └── Evidence Engine feeds ──> Digital Twin
                      └── Digital Twin inconsistency ──> Contradiction Engine
                          └── Contradiction Engine triggers ──> Self-Doubt Engine
                              └── Self-Doubt Engine drives ──> Thinking Pipeline
                                  └── Thinking Pipeline produces ──> Root Cause
                                      └── Root Cause informs ──> Consensus Engine
                                          └── Consensus Engine outputs ──> Quality Gate
                                              └── Quality Gate generates ──> Report
                                                  └── Report promoted to ──> Memory/Learning

## 10. Existing Asset Analysis

| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-visual-debug SKILL.md | `.agents/skills/frontend-visual-debug/SKILL.md` | Refactor | Becomes thin client wrapper |
| frontend-design SKILL.md | `.agents/skills/frontend-design/SKILL.md` | Extend | Becomes VIR Design Knowledge Base consumer |
| workflow_runtime.py | `.agents/skills/workflow-runtime/scripts/` | Extend | VIR integrates checkpoint/approval system |
| SQLite db.py | `.agents/skills/workflow-runtime/scripts/db.py` | Reuse | SQLite patterns already established |
| Qdrant connector | `.agents/skills/workflow-runtime/scripts/connectors/` | Reuse | Semantic memory infrastructure exists |
| session.py | `.agents/skills/workflow-runtime/scripts/session.py` | Extend | Session management patterns reused |
| Agent multi-agent patterns | FEAT-018, FEAT-020 | Extend | Multi-agent patterns already defined |

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: `frontend-visual-debug` (major refactor to thin client), `frontend-design` (extension to Design Knowledge Base)
- **Affected Modules/Components**: workflow_runtime.py, db.py, session.py, connectors/
- **Affected Runtime**: AIWF Workflow Runtime checkpoint system; approval gates
- **Affected Extension**: Visualizer extension (new VIR status panel)
- **Affected Scripts**: All workflow runtime scripts that integrate visual debug
- **Affected Database**: New VIR SQLite schema; new Qdrant collections
- **Affected Documentation**: FEAT-045 (Knowledge Runtime), FEAT-018 (Multi-Agent), FEAT-020 (Multi-Agent Analysis)
- **Impact Level**: High — this is a foundational new runtime, not a simple feature addition

## 12. Migration Strategy

- **Backward Compatibility**: `frontend-visual-debug` skill interface preserved externally; only internals change to thin-client delegation
- **Adapter Strategy**: Existing Playwright browser calls wrapped in BrowserAdapter interface; zero functional regression during migration
- **Coexistence Period**: Phases 1-3 — old skill and VIR core coexist; VIR incrementally takes over
- **Deprecation Plan**: After Phase 4 (Vision+Design intelligence), old skill internals fully deprecated
- **Migration Phases**: Follow 10-phase delivery roadmap defined in FR-09

## 13. Architecture Principles

- **API First**: All agent-to-agent communication via defined event contracts before implementation
- **Provider First**: Every capability behind an adapter interface; no direct provider imports in core
- **Script First**: Python CLI as primary interface; no GUI required for core operation
- **Memory First**: All agents consult historical evidence and memory before making new observations
- **Incremental Updates**: Each phase delivers working, testable capability
- **Backward Compatibility**: Thin client API stable across VIR versions
- **Replaceable Providers**: Vision, browser, storage providers swappable at configuration level

## 14. Non Goals

- VIR is not a test runner replacement (pytest, Jest, etc.)
- VIR is not a CI/CD system (GitHub Actions, GitLab CI)
- VIR is not a performance load tester (k6, Locust)
- VIR does not manage deployment
- VIR does not replace human design review entirely
- VIR does not directly write production code beyond blueprint-approved scope

## 15. ROI Analysis

- **Estimated Implementation Cost**: High (15 FEAT documents → 15+ blueprints → multi-sprint implementation)
- **Runtime Savings**: Elimination of manual visual QA per feature; automated regression across all features
- **Token Reduction Target**: -40% context tokens used in UI debugging conversations (VIR handles autonomously)
- **API Call Reduction Target**: -60% repeated visual debug API calls (VIR caches and persists findings)
- **Maintenance Impact**: Single intelligent runtime replaces fragile procedural skill
- **Expected Break-Even**: After 3 months of production use across 10+ features
- **Long-Term ROI**: VIR becomes universal AIWF perception layer, eliminating all manual UI review agents

## 16. Success Metrics

- **Latency Target**: Lightweight < 2s, Standard < 10s, Deep configurable
- **Memory Usage Limit**: < 512MB RAM for Lightweight profile; < 2GB for Deep
- **Startup Time Target**: < 1.5s for VIR core initialization
- **Cache Hit Ratio Target**: > 70% for repeated DOM observations on unchanged pages
- **Accuracy Target**: > 95% contradiction detection accuracy vs human expert review
- **Token Reduction Target**: 40% reduction in UI debugging conversation tokens
- **Expected ROI**: Positive after 3 months

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| VIR scope creep exceeds available development capacity | High | High | Strict phase gates; MVP-first delivery; defer advanced adapters | Architect |
| VLM/AI model dependencies create heavy runtime | High | Medium | VLM optional; Lightweight profile default; lazy model loading | Runtime Engineer |
| Event bus design becomes bottleneck at scale | Medium | Low | Start with asyncio local bus; abstract bus interface for future swap | Backend Architect |
| Digital Twin consistency becomes computationally expensive | High | Medium | Twin updates are incremental; full rebuild only on branch change | State Engineer |
| frontend-design knowledge base conflicts with VIR findings | Medium | Low | Design Authority has veto power; clear escalation protocol | Design Agent |
| Playwright API changes break browser adapter | Medium | Medium | Adapter interface isolates Playwright; contract tests on adapter | Infrastructure |
| SQLite concurrent writes from multiple agents | Medium | Medium | WAL mode; single writer pattern per investigation | Database Architect |

## 18. Technical Questions

- Should the VIR event bus support backpressure to prevent fast agents from overwhelming slow ones (e.g., VLM)?
- What is the maximum number of concurrent VIR investigations per project?
- Should the Digital Twin be rebuilt on every new VIR session or incrementally from persisted state?
- How does VIR handle page navigation during an investigation (SPA routing events)?
- What format should the VIR thin client contract use for passing context (JSON, proto, Python dataclass)?

## 19. Open Decision Register

| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Event bus backpressure strategy | Pending | Requires benchmark after Phase 1 prototype |
| Digital Twin serialization format | Pending | JSON vs MessagePack vs SQLite BLOB; decide in BP-VIR-006 |
| VIR thin client contract format | Pending | Python dataclass for v1; JSON schema for cross-language future |
| Max concurrent investigations | Pending | Default 1; configurable; decide in BP-VIR-014 |
| VLM provider default (local vs cloud) | Pending | Local Ollama first; cloud optional adapter |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR for (1) Event-driven vs Monolithic architecture choice; (2) Digital Twin storage strategy; (3) Provider abstraction pattern; (4) Evidence as first-class domain object vs log-only approach

## 21. Knowledge Update Impact

- **project-summary**: Yes — new major subsystem VIR added to project architecture
- **architecture**: Yes — multi-agent event-driven runtime architecture documented
- **modules**: Yes — new VIR module tree added to module registry
- **lessons**: Yes — perception-first vs test-first paradigm shift documented
- **patterns**: Yes — Evidence pattern, Investigation pattern, Digital Twin pattern, Provider-Agnostic Adapter pattern
- **ADR**: Yes — 4 ADRs required
- **SQLite**: Yes — new VIR database schema
- **indexes**: Yes — new vector index collections for visual memory
- **vector metadata**: Yes — visual issue embeddings, UX findings, component patterns

## 22. Test Strategy Preview

- **Unit Tests**: Each adapter contract, each agent lifecycle, event bus publish/subscribe, evidence schema validation
- **Integration Tests**: Orchestrator + 2 agents end-to-end; thin client → VIR invocation
- **Regression Tests**: Baseline screenshot comparison for every supported page
- **Performance Tests**: Latency benchmarks per profile; memory consumption per agent
- **Migration Tests**: Old `frontend-visual-debug` invocation still works after refactor
- **Compatibility Tests**: VIR core runs with stub adapters (no real browser required)

## 23. Extension Impact

- **Extension UI Changes**: New VIR status panel in Visualizer extension; shows active investigation, agent status, evidence timeline, confidence score
- **Affected ViewModels / Watchers**: Runtime state watcher needs VIR investigation state; dashboard needs VIR quality gate status

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 15% (existing skills refactored); 85% net new VIR code

## 25. Roadmap Alignment

- **Roadmap Phase**: New major subsystem — Phase VIR (runs parallel to FEAT-055 through FEAT-069)
- **Milestones**: Phase 1 (Foundation) → Phase 2 (Sensory) → Phase 3 (State+Digital Twin) → Phase 4 (Vision+Design) → Phase 5 (Cognitive) → Phase 6 (Multi-Agent) → Phase 7 (Memory) → Phase 8 (IDE) → Phase 9 (CI) → Phase 10 (Advanced)
- **Prerequisites & Dependencies**: FEAT-045 (Knowledge Runtime), FEAT-018 (Multi-Agent patterns), FEAT-051 (Workflow Locking), FEAT-052 (Permissions)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Is VIR a skill or an independent runtime? | Independent runtime; frontend-visual-debug becomes thin client |
| What technology for browser automation? | Playwright default, abstracted behind BrowserAdapter |
| How does Consensus work? | Weighted authority model with domain veto rights |
| Where are visual artifacts stored? | `.agents/visual-runtime/` filesystem + SQLite + Qdrant |
| What are execution profiles? | Lightweight (<2s), Standard (<10s), Deep (quality-first) |
| Is GPU required? | No; optional acceleration |
| How is randomness handled? | Seeded, reproducible, configurable |
| What is the Thinking Pipeline? | Observe→Interpret→Hypothesize→Collect→Validate→Reject→Re-think→RootCause→Fix→Verify→Learn |
| Does VIR auto-fix code? | Only within blueprint-approved scope; no unilateral refactoring |
| What is Design Authority? | frontend-design skill evolves to Design Knowledge Base with veto power |

## 27. Requirement Readiness Score

- **Score**: 96/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: Project memory + FEAT-018 (multi-agent), FEAT-045 (knowledge runtime), FEAT-020 (multi-agent analysis), FEAT-051 (locking), FEAT-052 (permissions)
- **Existing Architecture Summary**: AIWF uses script-first Python CLI, asyncio event patterns, SQLite for structured state, Qdrant for semantic search, multi-agent orchestration with agent contracts, approval gates for destructive operations

## 29. Existing Modules & Services

| Module/Service | Location | Owner | Public APIs | Est. Reuse % | Est. Mod. % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| frontend-visual-debug | `.agents/skills/frontend-visual-debug/` | Skill | SKILL.md interface | 10% | 90% | Low (interface stable) | Becomes thin client |
| frontend-design | `.agents/skills/frontend-design/` | Skill | SKILL.md interface | 60% | 40% | Low | Design Knowledge Base source |
| workflow_runtime.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | CLI + Python API | 70% | 30% | Low | VIR integrates checkpoint/session |
| db.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | SQLite abstractions | 80% | 20% | Low | VIR database layer |
| connectors/ | `.agents/skills/workflow-runtime/scripts/connectors/` | Runtime | Qdrant connector | 70% | 30% | Low | Semantic memory |
| task_orchestrator.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | Agent orchestration | 50% | 50% | Medium | Base for VIR orchestrator |

## 30. Solution Options Evaluated

### Option A: Monolithic Runtime Core with Plugin Adapters
- **Overview**: Single Python process containing all engines with plugin interface for adapters
- **Architecture**: Shared in-memory state; direct function calls between components
- **Advantages**: Simple, low latency, fast MVP
- **Disadvantages**: Single point of failure; poor agent isolation; not aligned with multi-agent autonomy vision
- **Complexity**: Medium | **Risk**: Medium | **Performance**: Good locally, poor at scale | **Maintainability**: Low | **Compatibility**: High | **Future Scalability**: Low

### Option B: Event-Driven Multi-Agent Architecture (SELECTED)
- **Overview**: asyncio-based local event bus; each agent is an independent coroutine with domain authority; Orchestrator manages lifecycle; Consensus Engine applies weighted authority model
- **Architecture**: Bus + Orchestrator + Agents + Evidence Engine + Digital Twin + Memory
- **Advantages**: Agent isolation; extensible; evidence-driven; natural fit for contradiction/self-doubt patterns; supports adaptive profiles
- **Disadvantages**: More complex initial design; requires event schema from day one
- **Complexity**: High | **Risk**: Low | **Performance**: Good at all scales | **Maintainability**: High | **Compatibility**: High | **Future Scalability**: High

### Option C: gRPC Microservices
- **Overview**: Each engine as a separate gRPC service; daemon orchestrator
- **Architecture**: Multiple processes; proto contracts; service discovery
- **Advantages**: Maximum isolation; language-agnostic; cloud-native future
- **Disadvantages**: Over-engineered for MVP; high infrastructure overhead; not aligned with script-first project architecture
- **Complexity**: Very High | **Risk**: High | **Performance**: Overhead | **Maintainability**: Complex | **Compatibility**: Low | **Future Scalability**: Very High

## 31. Solution Comparison Table

| Criteria | Option A: Monolithic | Option B: Event-Driven (Selected) | Option C: gRPC |
|---|---|---|---|
| Complexity | Medium | High | Very High |
| Risk | Medium | Low | High |
| Performance | Good/Local | Good/Scale | Overhead |
| Maintainability | Low | High | Complex |
| Compatibility | High | High | Low |
| Future Scalability | Low | High | Very High |
| Development Cost | Low | Medium | Very High |

## 32. Selected Solution

- **Choice**: Option B — Event-Driven Multi-Agent Architecture with Local Message Bus
- **Why Selected**: Aligns with existing multi-agent patterns (FEAT-018/020); supports domain authority and veto model naturally through event routing; evidence-driven investigation maps directly to event streams; adaptive profiles achieved by activating/deactivating agent subscriptions; future gRPC migration possible without breaking event contracts
- **Trade-offs Accepted**: More initial design complexity vs. faster MVP of Option A
- **Technical Debt**: Event schema must be designed carefully upfront; asyncio → gRPC migration path is non-breaking if interfaces are properly abstracted
- **Risk Mitigation**: Phase 1 validates architecture with only Orchestrator + Event Bus + 2 agents before full build-out

## 33. Risks & Assumptions

- **Risks**:
  - R-01: Scope creep → Mitigation: Strict phase gates; MVP-first; defer advanced adapters
  - R-02: VLM dependencies add heavy optional weight → Mitigation: Lazy loading; VLM is Layer 4 not Layer 1
  - R-03: Event bus design flaw discovered late → Mitigation: Phase 1 prototype validates bus before full build-out
  - R-04: Digital Twin consistency overhead → Mitigation: Incremental updates; full rebuild only on session start
- **Assumptions**:
  - A-01: Playwright remains the primary browser automation technology for at least 18 months
  - A-02: The project has access to at least one VLM (local Ollama or cloud API) for semantic analysis
  - A-03: asyncio is sufficient for local agent concurrency without external broker
  - A-04: SQLite WAL mode handles concurrent agent writes without data corruption

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): VIR runs as standalone CLI without invoking frontend-visual-debug (Test: `python vir_runtime.py run --url http://localhost:3000`)
- [ ] AC-02 (FR-02): All 6 perception pipeline stages (Observe/Understand/Reason/Investigate/Learn/Improve) are present in Orchestrator lifecycle
- [ ] AC-03 (FR-03): Digital Twin covers all 11 state dimensions and is internally consistent before issuing PASS
- [ ] AC-04 (FR-04): All 4 execution modes (CLI/IDE/CI/Daemon) invoke the same VIR core
- [ ] AC-05 (FR-05): Profile switching changes active agent set without restarting core
- [ ] AC-06 (FR-06): Swapping Playwright adapter for stub adapter does not break core runtime
- [ ] AC-07 (NFR-01): Lightweight profile completes under 2s for DOM-only observation
- [ ] AC-08 (NFR-04): New agent added via plugin interface without modifying core files
- [ ] AC-09 (NFR-07): VIR refuses destructive actions and requests human confirmation

## 35. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill for FEAT-055.

### Problem Statement
The AIWF needs a new independent runtime — Visual Intelligence Runtime (VIR) — that perceives frontend applications like a human, maintaining a Digital Twin of application state, building structured evidence, opening investigations, and reasoning through contradictions. The current `frontend-visual-debug` skill is a procedural tool that cannot achieve this. VIR must become the universal perception and reasoning runtime for all AIWF agentic workflows.

### Objectives & Selected Solution
- Build VIR as a provider-agnostic, event-driven, multi-agent runtime (Option B)
- Implement perception pipeline: Observe → Understand → Reason → Investigate → Learn → Improve
- Refactor `frontend-visual-debug` into a thin client wrapper
- Evolve `frontend-design` into a Design Knowledge Base
- Phase delivery across 10 phases from Foundation to Advanced Adapters

### Functional Requirements
FR-01 through FR-10 as listed in Section 4 above.

### Non-functional Requirements & Constraints
NFR-01 through NFR-08 and TC-01 through TC-06 as listed in Section 4 above.

### Architectural Details
- Core: Python asyncio event bus; Orchestrator; Provider-agnostic adapters
- Storage: `.agents/visual-runtime/` filesystem + SQLite (WAL) + Qdrant
- Evidence: Structured domain objects with ID, Source, Timestamp, Confidence, Entity, Type, Data, Relationship, Severity, Business Flow, Lifecycle
- Investigation: Persisted cross-session objects with Symptoms, Evidence, Contradictions, Hypotheses, Root Cause, Fix, Regression, Confidence, Learning
- Digital Twin: 11 state dimensions maintained by Orchestrator with consistency rules

### Risks & Assumptions
R-01 through R-04 and A-01 through A-04 as listed in Section 33 above.

### Verification Checklist
- [ ] docs/plans/FEAT-055_vir_foundation_plan.md generated and approved
- [ ] docs/designs/FEAT-055_vir_foundation_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks

---

> ⚠ The next Skill is `brainstorming-to-plan`.
> It must be invoked **manually** by the user.
> This Skill does NOT invoke it automatically.
