<!-- docs/brainstorming/FEAT-061_vir_evidence_domain_and_investigation_objects.md -->

---
feature_id: FEAT-061
feature_name: Visual Intelligence Runtime — Evidence Domain & Investigation Objects
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-060_vir_digital_twin_and_application_state_model.md
next_artifact: ../plans/FEAT-061_vir_evidence_investigation_plan.md
---

# Master Requirement Document – VIR Evidence Domain & Investigation Objects

## 1. Feature ID & Name
- **Feature ID**: FEAT-061
- **Feature Name**: Visual Intelligence Runtime — Evidence Domain & Investigation Objects

## 2. Original Idea
Define and implement Evidence and Investigation as first-class domain objects in VIR. Every observation produced by every agent becomes a structured Evidence object. Evidence objects are linked into Investigations. Investigations persist across sessions and contain the complete reasoning history from symptom to root cause to fix.

## 3. Business Problem
- **Problem**: Log messages and ad-hoc observation strings are insufficient for reasoning about complex, contradictory application states. Without structured evidence, the Contradiction Engine cannot compare observations, the Consensus Engine cannot weigh credibility, and investigations are lost between sessions.
- **Why it matters**: Evidence-driven reasoning is the core of VIR's intelligence. The architecture only works if every observation is a typed, structured, linkable domain object — not a log string.
- **Who is affected**: All VIR agents (all produce Evidence), Contradiction Engine, Cognitive Investigation Engine, Consensus Engine, Reporting System, Memory Engine.
- **Expected outcome**: A comprehensive Evidence domain model and Investigation lifecycle that enables structured reasoning, cross-session persistence, and evidence-backed final decisions.

## 4. Requirement Discovery

### Functional Requirements

#### Evidence Domain Object
- FR-01: Every evidence object must contain: ID (UUID), source_agent, timestamp (ISO-8601 + monotonic ns), confidence (0.0–1.0), observed_entity, observation_type, supporting_data, relationship (to other evidence IDs), severity (INFO/WARN/ERROR/CRITICAL), affected_business_flow, lifecycle (ACTIVE/STALE/SUPERSEDED/ARCHIVED).
- FR-02: Evidence must be classified by type: VISUAL, RUNTIME, NETWORK, STATE, INTERACTION, ACCESSIBILITY, PERFORMANCE, DESIGN, CONTRADICTION, HYPOTHESIS.
- FR-03: Evidence objects must be immutable after creation (append-only model). Updates create new Evidence linked to the original.
- FR-04: Evidence objects must support multi-link relationships: SUPPORTS, CONTRADICTS, EXPLAINS, SUPERSEDES, DEPENDS_ON.
- FR-05: Evidence lifecycle must auto-transition: ACTIVE → STALE after configurable window without corroboration; STALE → ARCHIVED after investigation closes.
- FR-06: Evidence must be queryable by: type, source_agent, entity, business_flow, severity, confidence_range, time_range, investigation_id, relationship_type.
- FR-07: Evidence Engine must aggregate incoming evidence events from the bus and create Evidence domain objects.
- FR-08: Evidence Engine must detect and publish `evidence.contradiction` when two active evidence objects have contradictory facts about the same entity.
- FR-09: Evidence Engine must link evidence produced within a correlation time window about the same entity into Observation Groups.

#### Investigation Domain Object
- FR-10: Every Investigation must contain: ID, feature_id, session_id, created_at, status (OPEN/INVESTIGATING/CONCLUDED/BLOCKED), symptoms, evidence_ids, contradictions, hypotheses, rejected_hypotheses, verified_hypothesis, root_cause, fix_applied, regression_status, confidence, learning_outcome.
- FR-11: Investigations must persist across VIR runtime sessions (SQLite).
- FR-12: Investigations must have a lifecycle: OPEN → INVESTIGATING → (CONCLUDED | BLOCKED).
- FR-13: An Investigation may generate child Investigations for decomposed sub-problems.
- FR-14: Investigation confidence must be calculated from the confidence of its linked evidence.
- FR-15: Hypothesis objects within an Investigation must track: hypothesis_text, evidence_for, evidence_against, tested, rejected, rejection_reason.
- FR-16: Root cause must be supported by at least 2 independent evidence objects to be validated.
- FR-17: Investigation reports must reference all contributing evidence by ID.
- FR-18: Learning outcomes from closed Investigations must be exportable to the Memory Engine.
- FR-19: Evidence Timeline Generation: Automatically generate a chronological event timeline of all collected Evidence objects within a session, including timestamps and source agents.
- FR-20: Investigation Timeline Tracking: Aggregate all key lifecycle changes of an Investigation (Opened, Hypothesis proposed, Hypothesis tested, Contradiction logged, Closed) into an auditable timeline.
- FR-21: Error Correlation & Diagnostics: Explicitly link console warning/error logs, network transaction anomalies, and state exceptions directly to the corresponding visual node evidence object.

### Non-functional Requirements
- NFR-01: Evidence object creation < 5ms per event.
- NFR-02: Evidence query response < 100ms for up to 10,000 evidence objects per session.
- NFR-03: Investigation persistence: < 200ms write; < 100ms read.
- NFR-04: Evidence IDs globally unique (UUID4) and collision-free.
- NFR-05: Evidence schema must be versioned; old evidence remains readable after schema updates.

### Technical Constraints
- TC-01: Evidence objects stored in SQLite (`vir_evidence` table) and in-memory LRU cache for active session.
- TC-02: Investigation objects stored in SQLite (`vir_investigations` table).
- TC-03: Evidence published to event bus topic `vir.evidence.*` by all agents.
- TC-04: Evidence Engine subscribes to all `vir.evidence.*` topics.
- TC-05: Evidence object schema defined as Python dataclass with JSON serialization.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Evidence object structure | BP-VIR-007 | Create evidence; validate all fields present | Schema validation passes |
| FR-03 | Must | Immutability | BP-VIR-007 | Attempt to mutate evidence; verify rejected | Mutation raises ImmutableEvidenceError |
| FR-04 | Must | Multi-link relationships | BP-VIR-007 | Link two evidence objects as CONTRADICTS | Relationship queryable from both directions |
| FR-08 | Must | Contradiction detection | BP-VIR-007 | Inject contradicting evidence | `evidence.contradiction` published within 50ms |
| FR-10 | Must | Investigation structure | BP-VIR-007 | Create investigation; verify all fields present | All required fields present |
| FR-11 | Must | Investigation persistence | BP-VIR-007 | Close session; reopen; query investigation | Investigation state preserved |
| FR-15 | Must | Hypothesis tracking | BP-VIR-007 | Add hypothesis; reject with reason | Rejected hypothesis preserved with reason |
| FR-16 | Must | Root cause validation | BP-VIR-007 | Single-evidence root cause rejected | System requires 2 independent evidence |
| FR-18 | Should | Learning outcome export | BP-VIR-007 | Close investigation with learning | Learning event published to Memory Engine |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Contradiction Engine | Internal | Critical | Critical | Structured evidence to compare and contradict |
| Cognitive Investigation Engine | Internal | Critical | Critical | Investigation lifecycle management |
| Consensus Engine | Internal | High | High | Evidence confidence for weighted voting |
| Memory Engine | Internal | High | High | Learning outcomes from investigations |
| Reporting System | Internal | High | High | Evidence-backed report generation |
| All Sensory Agents | Internal | High | High | Standard evidence publication interface |

## 7. Scope Boundary

### In Scope
- Evidence domain object model + schema
- Investigation domain object model + schema
- Evidence Engine (aggregation, contradiction detection, grouping)
- Evidence query interface
- Investigation lifecycle management
- Hypothesis tracking
- Root cause validation
- Learning outcome export interface
- SQLite persistence schemas

### Out of Scope
- Cognitive reasoning logic (FEAT-062)
- Reporting output format (FEAT-066)
- Memory Engine storage details (FEAT-064)

### Deferred Scope
- Evidence graph visualization
- Cross-investigation evidence linking (across multiple features)

### Future Scope
- Evidence embedding for semantic similarity search (detect similar past issues)
- Evidence timeline replay

## 8. Dependency Graph Preview

- FEAT-061: Evidence & Investigation Domain (Must)
  - FEAT-056: Event Bus (prerequisite — evidence published to bus)
  - FEAT-058: Vision Engine (produces VISUAL evidence)
  - FEAT-059: Hearing + Touch Engines (produce RUNTIME + INTERACTION evidence)
  - FEAT-060: Digital Twin (produces CONTRADICTION events → evidence)
  - FEAT-062: Cognitive Engines (consume investigations; add hypotheses)
  - FEAT-064: Memory Engine (receives learning outcomes)
  - FEAT-066: Reporting (consumes evidence + investigations for reports)

## 9. Data Flow Preview

- VisionAgent publishes: `{type:VISUAL, entity:login_button, observation:invisible, confidence:0.92}`
  └── Evidence Engine receives → creates EvidenceObject(ID=ev-001)
- HearingAgent publishes: `{type:NETWORK, entity:auth_api, observation:200_success, confidence:1.0}`
  └── Evidence Engine receives → creates EvidenceObject(ID=ev-002)
- EvidenceObject(ev-001) + EvidenceObject(ev-002) → same entity (login_flow) → correlation group
  └── Consistency check: login success (ev-002) contradicts login button invisible (ev-001) → CONTRADICTION
      └── `evidence.contradiction` published: evidence_ids=[ev-001, ev-002], severity=HIGH
          └── Contradiction Engine receives → opens Investigation(ID=inv-001)
              └── Investigation.symptoms = [ev-001, ev-002]
              └── Investigation.hypotheses = [H1: UI not updated after auth success]
                  └── CognitiveEngine tests H1 → new evidence ev-003 (React store not triggered)
                      └── Investigation.evidence_ids.append(ev-003)
                      └── Investigation.verified_hypothesis = H1
                      └── Investigation.root_cause = "Authentication event not dispatched to UI store"
                          └── Investigation.status = CONCLUDED
                              └── Learning outcome exported to Memory Engine

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| db.py SQLite | `.agents/skills/workflow-runtime/scripts/` | Extend | Evidence and Investigation persistence |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: Critical — Evidence domain is the foundation of all VIR reasoning

## 12. Migration Strategy

- **Backward Compatibility**: Evidence domain is new; no migration
- **Migration Phases**: Phase 3 implements Evidence domain; Phase 5 implements Investigation lifecycle

## 13. Architecture Principles

- **API First**: Evidence schema published as specification before any agent creates Evidence
- **Memory First**: Previous evidence from similar entities consulted before creating new Evidence
- **Incremental Updates**: Evidence never mutated; new evidence created to supersede

## 14. Non Goals

- Evidence Engine does not perform reasoning (Cognitive Engine does)
- Evidence Engine does not format reports (Reporting System does)

## 15. ROI Analysis

- **Value**: Every agent decision backed by traceable evidence → eliminates false positives
- **Investigation Persistence**: Cross-session investigations eliminate repeated diagnosis of recurring bugs
- **Learning**: Closed investigations feed Memory Engine → VIR gets smarter over time

## 16. Success Metrics

- **Evidence Creation Speed**: < 5ms per evidence object
- **Contradiction Detection**: < 50ms after two contradicting evidence objects created
- **Investigation Persistence**: Round-trip save/load < 300ms
- **Query Performance**: 10,000 evidence objects queried in < 100ms
- **Root Cause Validation**: 100% enforcement of 2-independent-evidence rule

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Evidence volume overload (high-frequency pages) | High | Medium | LRU cache + configurable retention window | Database Engineer |
| False contradiction detection (timing artifacts) | High | Medium | Correlation time window + staleness detection | Backend Engineer |
| Investigation scope creep (too many sub-investigations) | Medium | Medium | Max child investigation depth configurable | Runtime Engineer |
| Evidence schema migration breaks old data | High | Low | Schema versioning from day one; migration scripts | Database Engineer |

## 18. Technical Questions

- Should Evidence use UUID4 or a structured ID (e.g., `ev-FEAT-058-0001`) for human readability?
- What is the evidence retention policy (how long are ARCHIVED evidence objects kept)?
- Should contradictions require same `observed_entity` or allow cross-entity contradictions?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Evidence ID format | Pending | UUID4 for global uniqueness; short readable alias for display |
| Retention policy | Pending | Session evidence: 90 days; archived: 180 days; decide in BP-VIR-007 |
| Cross-entity contradictions | Pending | Allow with lower default confidence weight; decide in BP-VIR-007 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-006: Evidence immutability and append-only model

## 21. Knowledge Update Impact

- **patterns**: Yes — Evidence pattern; Investigation pattern; Hypothesis-testing pattern
- **architecture**: Yes — Evidence and Investigation domain
- **ADR**: Yes — ADR-VIR-006
- **SQLite**: Yes — vir_evidence and vir_investigations schemas

## 22. Test Strategy Preview

- **Unit Tests**: Evidence creation; immutability enforcement; relationship linking; lifecycle transitions
- **Integration Tests**: Full pipeline: agent → evidence → contradiction → investigation
- **Persistence Tests**: Save/load Evidence and Investigation across session restarts
- **Performance Tests**: 10,000 evidence object creation; query performance benchmarks

## 23. Extension Impact

- **Extension UI Changes**: Evidence timeline viewer in Visualizer (Phase 8)
- **Affected ViewModels**: Evidence list; Investigation detail panel

## 24. Complexity Estimation

- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 0% existing / 100% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 3 (State + Evidence)
- **Prerequisites**: FEAT-056 (Event Bus), sensory engines for evidence production

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Evidence as log messages? | No — first-class domain objects with structure |
| Investigation persistence? | Yes — across sessions in SQLite |
| Root cause validation? | Requires 2 independent evidence objects |
| Learning from investigations? | Yes — exported to Memory Engine |

## 27. Requirement Readiness Score

- **Score**: 96/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Evidence object created; all 11 required fields present and valid
- [ ] AC-02 (FR-03): Mutation attempt raises ImmutableEvidenceError
- [ ] AC-03 (FR-08): Two contradicting evidence objects → `evidence.contradiction` within 50ms
- [ ] AC-04 (FR-11): Investigation saved; session restarted; investigation loaded with all fields intact
- [ ] AC-05 (FR-16): Root cause with single evidence → rejected; system requires 2 independent evidence
- [ ] AC-06 (FR-18): Closed investigation → learning_outcome event published to Memory Engine

## 35. Final Planning Prompt

### Problem Statement
VIR needs Evidence and Investigation as first-class domain objects. Evidence is immutable, structured, linkable. Investigations persist across sessions and track the full reasoning from symptom to root cause.

### Architectural Details
- `vir_runtime/domain/evidence.py` — EvidenceObject dataclass, EvidenceType, Severity, Lifecycle, Relationship
- `vir_runtime/domain/investigation.py` — InvestigationObject, Hypothesis, RootCause, LearningOutcome
- `vir_runtime/engines/evidence_engine.py` — Aggregation, contradiction detection, grouping
- `vir_runtime/db/evidence_schema.sql` — SQLite schema
- `vir_runtime/db/investigation_schema.sql` — SQLite schema

### Verification Checklist
- [ ] docs/plans/FEAT-061_vir_evidence_investigation_plan.md generated and approved
- [ ] docs/designs/FEAT-061_vir_evidence_investigation_blueprint.md generated and approved
