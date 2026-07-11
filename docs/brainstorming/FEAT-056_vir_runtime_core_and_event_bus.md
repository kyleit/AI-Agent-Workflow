<!-- docs/brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md -->

---
feature_id: FEAT-056
feature_name: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-055_vir_vision_goals_and_architectural_foundation.md
next_artifact: ../plans/FEAT-056_vir_runtime_core_plan.md
---

# Master Requirement Document – VIR Runtime Core & Event Bus Architecture

## 1. Feature ID & Name
- **Feature ID**: FEAT-056
- **Feature Name**: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture

## 2. Original Idea
Design and implement the core infrastructure of the Visual Intelligence Runtime: the asynchronous event bus, the Orchestrator lifecycle manager, the Agent registry, the execution profile selector, and the VIR session management system. This is the nervous system that all other VIR components plug into.

## 3. Business Problem
- **Problem**: Without a robust, well-designed core runtime, all higher-level VIR capabilities (Vision, Hearing, Cognitive engines) cannot be integrated or extended reliably. A monolithic design would create tight coupling, making it impossible to add new agents, swap providers, or maintain independent failure isolation.
- **Why it matters**: The core event bus and orchestrator determine the scalability, extensibility, and reliability of the entire VIR system. A bad core design propagates throughout all 15 FEAT documents.
- **Who is affected**: All VIR internal agents, all adapter providers, the thin client (frontend-visual-debug), the Visualizer extension, CI/CD integrations.
- **Expected outcome**: A clean, stable, asyncio-based event bus and Orchestrator that serves as the universal runtime foundation for all VIR capabilities.

## 4. Requirement Discovery

### Functional Requirements
- FR-01: VIR must have a central asyncio-based event bus supporting publish/subscribe with topic routing.
- FR-02: The Orchestrator must manage the full VIR session lifecycle: Initialize → Observe → Investigate → Conclude → Report → Learn.
- FR-03: The Orchestrator must support an Agent Registry for dynamic agent registration, activation, and deactivation.
- FR-04: The Agent Registry must enforce Agent Contracts: every agent must declare its topics, authority domain, veto rights, and memory requirements.
- FR-05: The Orchestrator must implement execution profile selection: Lightweight, Standard, Deep Review.
- FR-06: Profile selection must activate/deactivate agent subscriptions dynamically without restarting the core.
- FR-07: The event bus must support priority-based message delivery for critical evidence (e.g., security findings, contradictions).
- FR-08: The Orchestrator must manage per-investigation state and carry it across agent hand-offs.
- FR-09: VIR must support a configurable per-stage timeout system (not a single global timeout).
- FR-10: The Orchestrator must emit heartbeat events to the IDE extension and any connected listeners.
- FR-11: The event bus must support back-pressure: slow consumers (e.g., VLM) must not block fast producers (e.g., DOM inspector).
- FR-12: VIR must implement a loop-prevention system: configurable maximum for observation retries, hypothesis changes, fix attempts, and browser reloads.
- FR-13: Event Schema Envelope & Protocol Versioning: Every message on the Event Bus must follow a standard envelope containing: event_id (UUID), correlation_id, causation_id, investigation_id, agent_id, target_id, timestamp (monotonic + UTC), schema_version, payload_type, payload.
- FR-14: Event Delivery Semantics: Enforce at-least-once delivery with idempotency filters at agent boundaries. Supports retry-on-failure with exponential backoff and a dead-letter queue (DLQ) for dead events.
- FR-15: Schema Registry & Evolution: Implement runtime schema validation. Changes to schemas must follow a backward-compatible evolution policy.
- FR-16: Configuration Precedence & Profile Loading: Configuration must load with clear precedence: Default Config → Project Config (`vir.yaml`) → Environment Variables → CLI Overrides.
- FR-17: Configurable Profiling parameters: Enforce profile definitions mapping active adapters, timeouts, retry budgets, browser configurations, VLM limits, and storage paths.
- FR-18: Observability - Structured Logging & Metrics: Emits JSON logs to standard output/files. Track performance metrics (CPU, RAM, API latencies) and system metrics (queue depth, message processing latency).
- FR-19: Observability - Timelines & Tracing: Maintain live, correlated timelines (Evidence timeline, Investigation timeline, Performance timeline, Browser timeline) queryable through CLI or Visualizer API.
- FR-20: Secret Handling: Securely inject and mask API tokens, keys, and credentials without logging them or exposing them in reports.

### Non-functional Requirements
- NFR-01: Core runtime startup time < 1.5 seconds.
- NFR-02: Event bus overhead < 5ms per message for local asyncio delivery.
- NFR-03: Event bus must handle up to 10,000 events per investigation session without memory leak.
- NFR-04: Orchestrator must gracefully shut down all agents and persist state on KeyboardInterrupt or SIGTERM.
- NFR-05: All inter-agent communication must be serializable to JSON for debug replay and logging.
- NFR-06: VIR core must run in Python 3.11+.

### Technical Constraints
- TC-01: asyncio event loop is the concurrency model. No threading (except for CPU-bound adapter work in executors).
- TC-02: No external message broker (Redis, RabbitMQ, Kafka) in MVP. Bus is in-process asyncio.
- TC-03: Bus interface must be abstract enough to allow future swap to external broker without agent code changes.
- TC-04: VIR session state persisted in `.agents/visual-runtime/state/session.json` and SQLite.
- TC-05: Agent contracts defined as Python dataclasses and validated at registration time.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | asyncio pub/sub event bus | BP-VIR-002 | Pub 100 messages; verify all received | All 100 messages delivered in order |
| FR-02 | Must | Orchestrator session lifecycle | BP-VIR-002 | Run full lifecycle with stub agents | All 6 phases complete without error |
| FR-03 | Must | Agent Registry | BP-VIR-002 | Register/deactivate agent at runtime | Agent removed from subscription list |
| FR-04 | Must | Agent Contract enforcement | BP-VIR-011 | Register agent without required field | Registration fails with clear error |
| FR-05 | Must | Execution profile selection | BP-VIR-002 | Switch profile mid-session | Agent set changes; prior data preserved |
| FR-07 | Must | Priority message delivery | BP-VIR-002 | Publish low+high priority; verify order | High priority delivered first |
| FR-09 | Must | Per-stage timeouts | BP-VIR-002 | Force timeout in DOM stage | Timeout produces investigation event not crash |
| FR-11 | Should | Back-pressure handling | BP-VIR-002 | Publish faster than VLM can consume | Queue bounded; slow agent not blocking others |
| FR-12 | Must | Loop prevention | BP-VIR-002 | Trigger 10 retries | System stops at limit; produces BLOCKED report |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| All VIR Agents | Internal | Critical | Critical | Reliable message delivery and lifecycle management |
| VIR Adapters | Internal | High | High | Stable interface for publishing observations |
| Orchestrator | Internal | Critical | Critical | Complete investigation lifecycle control |
| Frontend-visual-debug thin client | Primary | High | High | Simple invocation API hiding all complexity |
| Visualizer Extension | Secondary | Medium | Medium | Heartbeat events for live status display |

## 7. Scope Boundary

### In Scope
- asyncio-based event bus implementation
- Orchestrator and session lifecycle
- Agent Registry with contract validation
- Execution profile system
- Per-stage timeout system
- Loop prevention system
- VIR session state persistence
- Heartbeat event emission
- Back-pressure implementation

### Out of Scope
- Individual agent implementations (FEAT-057 through FEAT-069)
- Report generation (FEAT-066)
- IDE extension integration details (FEAT-068)

### Deferred Scope
- External message broker (Redis/RabbitMQ) migration
- Distributed multi-machine event routing

### Future Scope
- gRPC transport layer over the abstracted bus interface

## 8. Dependency Graph Preview

- FEAT-056: Runtime Core & Event Bus (Must — foundation for all)
  └── FEAT-057: Adapter Architecture (Must — first consumers of bus)
      └── FEAT-058: Vision Engine (Must)
      └── FEAT-059: Hearing & Touch (Must)
  └── FEAT-060: Digital Twin (Must)
  └── FEAT-061: Evidence & Investigation (Must)
  └── FEAT-062: Cognitive Engines (Must)
  └── FEAT-063: Multi-Agent & Consensus (Must)

## 9. Data Flow Preview

- Orchestrator starts VIR session
  └── publishes `session.started` event to bus
      └── Agent Registry activates agents per profile
          └── Agents subscribe to relevant topic channels
              └── Sensory agents publish `evidence.*` events
                  └── Evidence Engine aggregates to Evidence Domain Objects
                      └── Cognitive agents subscribe to `evidence.*`
                          └── Contradiction Engine publishes `contradiction.detected`
                              └── Orchestrator receives contradiction → triggers Self-Doubt
                                  └── Investigation updated with new evidence
                                      └── Consensus Engine subscribes to `investigation.concluded`
                                          └── Quality Gate evaluates → `quality.gate.result`
                                              └── Orchestrator publishes `session.ended`

## 10. Existing Asset Analysis

| Asset / Component | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| task_orchestrator.py | `.agents/skills/workflow-runtime/scripts/` | Reuse/Extend | Existing agent orchestration patterns |
| session.py | `.agents/skills/workflow-runtime/scripts/` | Extend | Session state management |
| db.py | `.agents/skills/workflow-runtime/scripts/` | Extend | SQLite session persistence |
| Python asyncio | stdlib | Use | Native async concurrency; no external dep |

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: All VIR skills (depend on this core)
- **Affected Modules**: All VIR agents, adapters, and reporters
- **Affected Runtime**: AIWF workflow runtime (VIR registers as a managed session)
- **Affected Extension**: Visualizer extension heartbeat consumer
- **Impact Level**: Critical — all other FEAT documents depend on this design being correct

## 12. Migration Strategy

- **Backward Compatibility**: VIR core is new code; no migration from old system at this layer
- **Adapter Strategy**: asyncio bus abstracted behind `EventBus` interface from day one
- **Coexistence Period**: None needed; this is a greenfield component
- **Deprecation Plan**: N/A
- **Migration Phases**: Phase 1 delivers Event Bus + Orchestrator stub; Phase 2 adds first real agents

## 13. Architecture Principles

- **API First**: Event schema defined before any agent implements publish/subscribe
- **Provider First**: EventBus is an abstract interface; asyncio is the first implementation
- **Script First**: Orchestrator exposed as Python CLI entry point
- **Memory First**: Session state loaded from SQLite before starting new session
- **Incremental Updates**: Profile system allows adding agents without core changes
- **Backward Compatibility**: Event schema versioned; old events remain readable
- **Replaceable Providers**: EventBus implementation swappable at configuration

## 14. Non Goals

- Event bus is not a general-purpose message broker for the whole AIWF
- Orchestrator does not execute code fixes (that is the Coder agent's job)
- Session state does not replace the AIWF workflow runtime session

## 15. ROI Analysis

- **Estimated Implementation Cost**: Medium (2–3 sprints for core infrastructure)
- **Runtime Savings**: All future VIR capabilities built on stable foundation; no rework
- **Token Reduction Target**: N/A (infrastructure component)
- **Maintenance Impact**: Well-designed core reduces maintenance cost of all dependent agents
- **Expected Break-Even**: Immediate — all VIR phases depend on this
- **Long-Term ROI**: Core never needs replacement if abstraction is correct

## 16. Success Metrics

- **Startup Time**: < 1.5s
- **Event Throughput**: > 1,000 events/second (local asyncio)
- **Message Latency**: < 5ms per event (local)
- **Back-pressure**: Queue bounded at 10,000 events; slow consumer never blocks others
- **Loop Prevention**: System halts at configured retry limit 100% of the time
- **Graceful Shutdown**: All agents shut down cleanly in < 3s on SIGTERM

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| asyncio event loop blocking on CPU-intensive agent | High | Medium | Run heavy agents in ThreadPoolExecutor | Backend Architect |
| Event schema becomes rigid preventing agent evolution | High | Medium | Schema versioning from day one; forward-compatible design | Architect |
| Back-pressure causes dropped events | Medium | Low | Bounded queue with dead-letter mechanism | Backend Architect |
| Agent contract violation not caught at registration | High | Low | Strict contract validator; unit tests for all contract fields | Test Developer |
| Session state corruption on ungraceful shutdown | Medium | Medium | WAL mode SQLite; atomic writes | Database Architect |

## 18. Technical Questions

- Should the event bus implement topics as Python asyncio.Queue per topic or a single shared queue with topic filtering?
- What is the maximum bounded queue size before back-pressure kicks in?
- Should Agent Contracts be runtime-validated or compile-time enforced (Protocol/ABC)?
- How should the Orchestrator handle an agent that crashes mid-investigation?
- Should the event bus serialize all events to SQLite for replay capability?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Queue-per-topic vs single-queue-with-filter | Pending | Queue-per-topic recommended; benchmark in Phase 1 |
| Agent crash recovery strategy | Pending | Restart agent vs mark investigation as DEGRADED; decide in BP-VIR-002 |
| Event replay from SQLite | Pending | Valuable for debugging; implement in Phase 3 |
| Contract enforcement: Protocol vs ABC vs runtime check | Pending | Use Python Protocol for static typing + runtime check on register() |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-001: asyncio vs external message broker; ADR-VIR-002: queue-per-topic vs single-queue event routing

## 21. Knowledge Update Impact

- **architecture**: Yes — event bus architecture pattern documented
- **patterns**: Yes — asyncio pub/sub pattern; Agent Registry pattern
- **ADR**: Yes — 2 ADRs
- **SQLite**: Yes — VIR session schema
- **modules**: Yes — new vir_runtime/core/ module

## 22. Test Strategy Preview

- **Unit Tests**: EventBus publish/subscribe; priority ordering; back-pressure; Agent Registry contract validation; profile activation/deactivation
- **Integration Tests**: Orchestrator + 2 stub agents full lifecycle; session state persistence and recovery
- **Performance Tests**: 10,000 events throughput; startup latency; memory leak detection over 1-hour session
- **Regression Tests**: Session recovery after ungraceful shutdown

## 23. Extension Impact

- **Extension UI Changes**: Heartbeat event consumer in Visualizer extension
- **Affected ViewModels**: VIR session status watcher in extension

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 5% existing / 95% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 1 (Foundation)
- **Milestones**: Phase 1 complete = Event Bus + Orchestrator stub + Agent Registry + Profile selection working
- **Prerequisites**: FEAT-055 approved; Python 3.11+ environment

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Concurrency model? | asyncio; CPU-bound tasks in ThreadPoolExecutor |
| External broker in MVP? | No; asyncio local bus |
| Agent crash behavior? | Mark investigation DEGRADED; log evidence; continue if other agents healthy |
| Back-pressure mechanism? | Bounded asyncio.Queue; slow consumer receives back-pressure signal |

## 27. Requirement Readiness Score

- **Score**: 95/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: FEAT-018 multi-agent orchestration; FEAT-020 analysis agent patterns; task_orchestrator.py existing code
- **Existing Architecture Summary**: AIWF already uses asyncio patterns in workflow runtime; db.py provides SQLite WAL; session.py manages lifecycle state

## 29. Existing Modules & Services

| Module/Service | Location | Owner | Public APIs | Est. Reuse % | Est. Mod. % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| task_orchestrator.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | orchestrate(), dispatch() | 40% | 60% | Medium | Base orchestration patterns |
| session.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | load/save session | 50% | 50% | Low | Session lifecycle |
| db.py | `.agents/skills/workflow-runtime/scripts/` | Runtime | SQLite CRUD | 70% | 30% | Low | Persistence |

## 30. Solution Options Evaluated

### Option A: Single asyncio.Queue with Topic Filter
- **Overview**: One global queue; consumers filter by topic prefix
- **Advantages**: Simple; low memory; easy to implement
- **Disadvantages**: All consumers process every message header; filtering overhead; no true isolation
- **Complexity**: Low | **Risk**: Medium | **Performance**: Overhead at scale | **Maintainability**: Medium

### Option B: Queue-per-Topic (SELECTED)
- **Overview**: Each topic has a dedicated asyncio.Queue; agents subscribe to named topics
- **Advantages**: True isolation; clean back-pressure per topic; easy priority per queue; no shared state
- **Disadvantages**: More queue objects; memory scales with topic count
- **Complexity**: Medium | **Risk**: Low | **Performance**: Excellent | **Maintainability**: High

### Option C: asyncio EventEmitter Pattern
- **Overview**: Python equivalent of Node.js EventEmitter; callbacks registered for events
- **Advantages**: Familiar pattern; very lightweight
- **Disadvantages**: No queue; no back-pressure; callback hell at scale; not serializable
- **Complexity**: Low | **Risk**: High | **Performance**: Best for simple cases | **Maintainability**: Low

## 31. Solution Comparison Table

| Criteria | A: Single Queue | B: Queue-per-Topic (Selected) | C: EventEmitter |
|---|---|---|---|
| Complexity | Low | Medium | Low |
| Risk | Medium | Low | High |
| Back-pressure | Limited | Per-topic | None |
| Isolation | Poor | Excellent | None |
| Scalability | Medium | High | Low |
| Debuggability | Medium | High | Low |

## 32. Selected Solution

- **Choice**: Option B — Queue-per-Topic
- **Why**: True topic isolation enables per-topic back-pressure (critical for VLM agent); agents subscribe only to relevant topics; easy to add new topics without affecting existing subscriptions; clean serialization for debug replay
- **Trade-offs Accepted**: Slightly more memory than single queue; acceptable given bounded queue sizes
- **Technical Debt**: Topic naming convention must be standardized from day one
- **Risk Mitigation**: Phase 1 prototype with 3 topics validates design before full expansion

## 33. Risks & Assumptions

- **Risks**:
  - R-01: Topic proliferation → Mitigation: Hierarchical topic naming (e.g., `vir.evidence.vision.*`); topic registry
  - R-02: Agent blocks event loop → Mitigation: All agents use `async def`; CPU work in executor
  - R-03: Queue memory growth → Mitigation: Hard queue size limit; back-pressure signal
- **Assumptions**:
  - A-01: asyncio is sufficient for VIR's concurrency needs in local mode
  - A-02: Topic count stays below 50 in MVP
  - A-03: Python 3.11+ asyncio performance is adequate for 10,000 events/session

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Publish 1,000 events to 5 topics; all received by correct subscribers without loss
- [ ] AC-02 (FR-02): Full Orchestrator lifecycle completes with 2 stub agents
- [ ] AC-03 (FR-03): Agent registered, activated, and deactivated dynamically at runtime
- [ ] AC-04 (FR-04): Agent without required contract field fails registration with descriptive error
- [ ] AC-05 (FR-05): Profile switch from Standard to Lightweight deactivates VLM agent subscription
- [ ] AC-06 (FR-09): Per-stage timeout fires; investigation continues with TIMEOUT evidence record
- [ ] AC-07 (FR-11): VLM agent receives back-pressure signal when queue reaches 80% capacity
- [ ] AC-08 (FR-12): System halts after 10 retry limit; produces BLOCKED investigation report

## 35. Final Planning Prompt

### Problem Statement
VIR needs a production-grade asyncio event bus and Orchestrator as its runtime foundation. This is Phase 1 of VIR delivery.

### Objectives & Selected Solution
Queue-per-topic asyncio event bus; Orchestrator session lifecycle; Agent Registry with contract validation; Execution profile system; Per-stage timeouts; Loop prevention; SQLite session persistence.

### Functional Requirements
FR-01 through FR-12 as listed in Section 4.

### Non-functional Requirements
NFR-01 through NFR-06 and TC-01 through TC-05.

### Architectural Details
- `vir_runtime/core/bus.py` — EventBus, Topic, Queue management
- `vir_runtime/core/orchestrator.py` — Session lifecycle, agent activation
- `vir_runtime/core/registry.py` — Agent Registry, Contract validator
- `vir_runtime/core/profiles.py` — Profile definitions, agent set mappings
- `vir_runtime/core/session.py` — VIR session state, SQLite persistence

### Verification Checklist
- [ ] docs/plans/FEAT-056_vir_runtime_core_plan.md generated and approved
- [ ] docs/designs/FEAT-056_vir_runtime_core_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks
