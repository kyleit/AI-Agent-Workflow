<!-- docs/brainstorming/FEAT-062_vir_thinking_pipeline_and_cognitive_engines.md -->

---
feature_id: FEAT-062
feature_name: Visual Intelligence Runtime — Thinking Pipeline & Cognitive Engines
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-061_vir_evidence_domain_and_investigation_objects.md
next_artifact: ../plans/FEAT-062_vir_cognitive_engines_plan.md
---

# Master Requirement Document – VIR Thinking Pipeline & Cognitive Engines

## 1. Feature ID & Name
- **Feature ID**: FEAT-062
- **Feature Name**: Visual Intelligence Runtime — Thinking Pipeline & Cognitive Engines

## 2. Original Idea
Design and implement the core cognitive architecture of VIR: the Thinking Pipeline (Observe → Interpret → Generate Hypotheses → Collect Evidence → Validate → Reject → Re-think → Root Cause → Fix → Verify → Learn), the Cognitive Investigation Engine, the Contradiction Detection Engine, the Self-Doubt Engine, and the Root Cause Analysis Engine.

## 3. Business Problem
- **Problem**: Detecting that something is wrong is not enough. VIR must reason about why it is wrong. Without a structured thinking pipeline, VIR would either give up at the first contradiction or loop forever retrying the same observation. The Cognitive Engines implement the reasoning discipline that transforms raw evidence into validated root causes and actionable fixes.
- **Why it matters**: The Thinking Pipeline is the most differentiated architectural element of VIR. It is what separates a "smart frontend tester" from a "Visual Intelligence Runtime." Without it, VIR is a sophisticated screenshot tool.
- **Who is affected**: All cognitive agents; Consensus Engine (receives reasoned conclusions); Reporting System (reports root causes); Memory Engine (learns from concluded investigations).
- **Expected outcome**: A disciplined, bounded thinking pipeline that reasons through UI/UX issues systematically, challenges its own conclusions, investigates contradictions, identifies root causes with evidence, and avoids infinite loops.

## 4. Requirement Discovery

### Functional Requirements

#### Thinking Pipeline
- FR-01: Implement the Thinking Pipeline as the ordered execution framework for all VIR investigations:
  1. **Observe**: Activate sensory agents; collect initial Evidence
  2. **Interpret**: Classify evidence; update Digital Twin; identify anomalies
  3. **Generate Hypotheses**: Create 1–N Hypothesis objects for each anomaly
  4. **Collect Evidence**: Execute targeted observations to test each hypothesis
  5. **Validate**: Score hypothesis evidence; mark as SUPPORTED or CONTRADICTED
  6. **Reject**: Formally reject unsupported hypotheses; preserve rejection reason
  7. **Re-think**: If no hypothesis validated → generate new hypotheses from remaining evidence
  8. **Root Cause**: Declare root cause when hypothesis supported by ≥2 independent evidence
  9. **Fix**: Generate or apply fix within approved scope
  10. **Verify**: Re-run observation to confirm fix resolved root cause
  11. **Learn**: Export learning outcome to Memory Engine; close Investigation
- FR-02: Pipeline stages must be bounded by configurable per-stage timeout.
- FR-03: Pipeline must have configurable maximum iteration limits (Re-think cycles, Hypothesis count).
- FR-04: When limits reached without resolution → transition to BLOCKED status; produce unresolved investigation report.
- FR-05: Pipeline must support parallel hypothesis testing when hypotheses are independent.
- FR-06: Each pipeline stage must publish stage-transition events to the event bus.

#### Contradiction Detection Engine
- FR-07: Contradiction Engine subscribes to `evidence.contradiction` and `twin.inconsistency.detected` events.
- FR-08: For each contradiction, Contradiction Engine creates a ContradictionRecord:
  - observation_a (evidence_id, agent, fact)
  - observation_b (evidence_id, agent, fact)
  - source_agents
  - timestamp
  - confidence_scores
  - expected_relationship
  - severity
  - affected_business_flow
- FR-09: ContradictionRecord is injected into the active Investigation as a symptom.
- FR-10: Contradiction Engine must classify contradiction severity: POSSIBLE (timing artifact), PROBABLE (repeated across observations), CONFIRMED (same fact reported inconsistently by independent agents).

#### Self-Doubt Engine
- FR-11: Self-Doubt Engine triggered by: confirmed contradiction, single-source evidence driving a conclusion, stale evidence, hypothesis rejection exceeds threshold.
- FR-12: Self-Doubt Engine must challenge the current conclusion by asking:
  - Is conclusion based on single signal? → Weight reduced.
  - Could observation be stale? → Re-observe.
  - Could UI be out of sync with application state? → Check Digital Twin.
  - Could timing/async cause the mismatch? → Apply async wait strategy.
  - Could the observer itself be wrong? → Switch to alternative observation strategy.
  - Could the browser display an outdated frame? → Force refresh + re-observe.
  - Could the application be in an intermediate state? → Wait for state stabilization.
- FR-13: Self-Doubt Engine must execute bounded re-observation strategy (configurable max retries).
- FR-14: Self-Doubt Engine must change investigation strategy if contradiction persists after retry.
- FR-15: Strategy change options: inspect reactive bindings, inspect subscription lifecycle, inspect router guards, inspect state hydration, inspect stale closures, inspect race conditions, inspect cache invalidation, inspect event listeners, inspect derived state, inspect error boundaries.
- FR-16: Self-Doubt Engine escalates to human confirmation only when: destructive action required, multiple root causes equally plausible, required credentials missing, expected behavior undefined in blueprint, retry/confidence limit reached.

#### Root Cause Analysis Engine
- FR-17: Root Cause Analysis (RCA) Engine receives validated hypothesis from Thinking Pipeline.
- FR-18: RCA Engine must require ≥2 independent evidence objects before declaring root cause.
- FR-19: RCA Engine must classify root cause by category: TIMING, STATE_SYNC, ROUTING, RENDERING, NETWORK, AUTHENTICATION, PERMISSION, FRAMEWORK_REACTIVITY, CSS_SPECIFICITY, ASYNC_LIFECYCLE, DATA_INTEGRITY, SCOPE_PROTECTION_VIOLATION.
- FR-20: RCA Engine must generate a structured RootCause object: category, description, evidence_ids, confidence, affected_components, recommended_fix, fix_scope_valid (bool based on blueprint).
- FR-21: RCA Engine must verify fix scope is within blueprint-approved implementation scope before authorizing any code change.

### Non-functional Requirements
- NFR-01: Thinking Pipeline stage transitions < 100ms overhead per transition.
- NFR-02: Contradiction Detection < 50ms per contradiction event.
- NFR-03: Self-Doubt Engine re-observation bounded by configurable timeout (default: 3 retries × 5s each).
- NFR-04: Pipeline must never run forever — hard limit enforced at all times.
- NFR-05: All thinking steps logged with evidence references for complete audit trail.

### Technical Constraints
- TC-01: Thinking Pipeline implemented as asyncio state machine.
- TC-02: Maximum Re-think cycles: configurable, default 3.
- TC-03: Maximum Hypothesis count per investigation: configurable, default 10.
- TC-04: Maximum fix attempts: configurable, default 3.
- TC-05: All cognitive agents communicate via event bus; no direct function calls between engines.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | 11-stage Thinking Pipeline | BP-VIR-008 | Run pipeline with stub agents on known bug | All 11 stages execute in order |
| FR-03 | Must | Max iteration limits | BP-VIR-008 | Exceed rethink limit | Pipeline transitions to BLOCKED |
| FR-07 | Must | Contradiction Engine subscriptions | BP-VIR-008 | Publish contradiction event | ContradictionRecord created |
| FR-10 | Must | Contradiction severity | BP-VIR-008 | Single observation → POSSIBLE; repeated → CONFIRMED | Severity escalates correctly |
| FR-12 | Must | Self-Doubt challenges | BP-VIR-008 | Single-evidence conclusion | Self-Doubt reduces weight + triggers re-observe |
| FR-16 | Must | Escalation conditions | BP-VIR-008 | Destructive action needed | Human confirmation requested |
| FR-18 | Must | RCA 2-evidence requirement | BP-VIR-008 | Single-evidence root cause | RCA Engine rejects; returns INSUFFICIENT_EVIDENCE |
| FR-21 | Must | Fix scope validation | BP-VIR-008 | Fix outside blueprint scope | Fix blocked; SCOPE_VIOLATION evidence published |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Consensus Engine | Internal | High | High | Reasoned conclusions from Thinking Pipeline |
| Memory Engine | Internal | High | High | Learning outcomes from RCA |
| Reporting System | Internal | High | High | Root cause + evidence chain for reports |
| Quality Gate | Internal | High | High | Validated investigation results |
| Human Engineer | Primary | High | Medium | Escalation with complete evidence context |

## 7. Scope Boundary

### In Scope
- 11-stage Thinking Pipeline state machine
- Contradiction Detection Engine + ContradictionRecord
- Self-Doubt Engine + bounded retry/strategy-change
- Root Cause Analysis Engine + RootCause object
- Loop prevention system
- Pipeline audit log
- Escalation protocol

### Out of Scope
- Multi-Agent Consensus Engine (FEAT-063)
- Memory storage of learning outcomes (FEAT-064)
- Code fix execution (Coder Agent responsibility)
- Reporting output (FEAT-066)

### Deferred Scope
- Parallel hypothesis testing (Phase 6 enhancement)
- RCA category ML classification (Phase 10)

### Future Scope
- LLM-assisted hypothesis generation
- Causal graph-based root cause tracing

## 8. Dependency Graph Preview

- FEAT-062: Thinking Pipeline & Cognitive Engines (Must)
  - FEAT-061: Evidence & Investigation Domain (prerequisite)
  - FEAT-060: Digital Twin (prerequisite — cross-dimension contradiction input)
  - FEAT-063: Multi-Agent Consensus Engine (consumer of pipeline conclusions)
  - FEAT-064: Memory Engine (receives learning outcomes)

## 9. Data Flow Preview

- Investigation opened (from contradiction)
  └── Thinking Pipeline: Stage 1 OBSERVE → sensory agents activated
      └── Stage 2 INTERPRET → evidence classified; Digital Twin checked
          └── Stage 3 HYPOTHESIZE → H1: "state not dispatched", H2: "router guard blocking"
              └── Stage 4 COLLECT → targeted observations for H1 and H2
                  └── Stage 5 VALIDATE → H1: 3 supporting evidence, H2: 0 supporting
                      └── Stage 6 REJECT → H2 formally rejected with reason
                          └── Stage 7 (skip — H1 validated)
                              └── Stage 8 ROOT CAUSE → RCA(H1, 3 evidence) → root_cause declared
                                  └── Stage 9 FIX → scope check passes → fix generated
                                      └── Stage 10 VERIFY → Vision+Hearing re-run → login screen gone
                                          └── Stage 11 LEARN → LearningOutcome → Memory Engine
                                              └── Investigation CONCLUDED

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| task_orchestrator.py | scripts/ | Reuse patterns | State machine patterns; stage orchestration |
| approval_gate.py | scripts/ | Reuse | Human escalation mechanism |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: Critical — Thinking Pipeline is the reasoning core of VIR

## 12. Migration Strategy

- **Backward Compatibility**: Cognitive engines are new components
- **Migration Phases**: Phase 5 implements Contradiction + Self-Doubt; Phase 5 also implements RCA; Pipeline state machine built incrementally

## 13. Architecture Principles

- **Memory First**: Previous similar investigations consulted before generating hypotheses
- **API First**: ContradictionRecord schema + RootCause schema defined before implementations
- **Incremental Updates**: Pipeline stages independently testable; stages added one by one

## 14. Non Goals

- Cognitive engines do not perform browser interactions (Touch Engine does)
- Do not loop forever
- Do not make fix decisions outside approved scope

## 15. ROI Analysis

- **Value**: Transforms "there is a bug" to "the root cause is X because of evidence Y and Z"
- **Investigation Efficiency**: Systematic pipeline eliminates ad-hoc debugging
- **Self-Healing Potential**: Root cause + fix + verify pipeline enables autonomous bug resolution within scope

## 16. Success Metrics

- **Pipeline Completion Rate**: > 80% of investigations reach CONCLUDED (not BLOCKED) on known test cases
- **RCA Accuracy**: > 90% root cause identification accuracy vs expert human analysis on test suite
- **False Self-Doubt Rate**: < 10% unnecessary Self-Doubt triggers on stable, correct pages
- **Loop Prevention**: 100% enforcement — no investigation runs beyond configured limits

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Hypothesis generation produces irrelevant hypotheses | High | Medium | Hypothesis generator uses evidence type + Digital Twin state as context | Cognitive Engineer |
| Self-Doubt triggers endlessly on flaky pages | High | Medium | Configurable re-think limit; exponential backoff | Runtime Engineer |
| RCA declares wrong root cause | High | Low | 2-evidence requirement + corroboration + confidence threshold | QA Engineer |
| Pipeline blocks on async state (race condition) | Medium | Medium | Async wait strategy; timeout with STALE evidence | Backend Engineer |
| Fix scope validation too restrictive | Medium | Low | Blueprint integration; configurable override with human approval | Architect |

## 18. Technical Questions

- Should hypothesis generation be rule-based, ML-based, or LLM-assisted?
- What constitutes "independent" evidence (different source agents? different observation types? different timestamps)?
- How does Self-Doubt Engine avoid the livelock problem where every re-observation triggers another doubt cycle?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Hypothesis generation: rule-based vs LLM | Pending | Rule-based for MVP; LLM-assisted as Phase 10 adapter |
| Independence definition for evidence | Pending | Different source agents AND different observation_type; decide in BP-VIR-008 |
| Self-Doubt livelock prevention | Pending | Max consecutive self-doubt cycles = 2; then escalate |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-007: Rule-based hypothesis generation vs LLM-assisted

## 21. Knowledge Update Impact

- **patterns**: Yes — Thinking Pipeline pattern; Self-Doubt pattern; Root Cause Analysis pattern
- **architecture**: Yes — Cognitive Engine architecture
- **ADR**: Yes — ADR-VIR-007
- **lessons**: Yes — Key lessons from contradiction investigation approach

## 22. Test Strategy Preview

- **Unit Tests**: Each pipeline stage; contradiction severity escalation; Self-Doubt triggers; RCA 2-evidence rule
- **Integration Tests**: Full pipeline on known bug scenarios (login contradiction, layout regression)
- **Stress Tests**: Max iterations reached; pipeline transitions to BLOCKED correctly
- **Human Escalation Tests**: Destructive action detected; human confirmation requested

## 23. Extension Impact

- **Extension UI Changes**: Investigation stage indicator in Visualizer (Phase 8)
- **Affected ViewModels**: Thinking Pipeline stage progress bar; hypothesis list; contradiction viewer

## 24. Complexity Estimation

- **Implementation Complexity**: Very High
- **Estimated Refactoring Percentage**: 0% existing / 100% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 5 (Cognitive Reasoning)
- **Milestones**: Phase 5 complete = Contradiction + Self-Doubt + RCA + full Pipeline working on test scenarios
- **Prerequisites**: FEAT-061 (Evidence & Investigation), FEAT-060 (Digital Twin)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Self-Doubt escalation triggers? | Per clarification Q4: only when destructive, multiple equally plausible causes, credentials missing, blueprint undefined, limit reached |
| Fix scope enforcement? | Only within blueprint-approved scope; human confirmation for out-of-scope |
| Pipeline is Observe→Fix→Done? | No — Observe→Interpret→Hypothesize→Collect→Validate→Reject→Re-think→RootCause→Fix→Verify→Learn |

## 27. Requirement Readiness Score

- **Score**: 94/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Full 11-stage pipeline executes in order on known test bug scenario
- [ ] AC-02 (FR-03): After 3 Re-think cycles, pipeline transitions to BLOCKED and produces unresolved report
- [ ] AC-03 (FR-10): Same contradiction observed 3 times → severity escalates to CONFIRMED
- [ ] AC-04 (FR-12): Single-signal conclusion triggers Self-Doubt; weight reduced; re-observation executed
- [ ] AC-05 (FR-18): Single-evidence root cause rejected with INSUFFICIENT_EVIDENCE status
- [ ] AC-06 (FR-21): Fix targeting file outside blueprint scope → SCOPE_VIOLATION; fix blocked

## 35. Final Planning Prompt

### Problem Statement
VIR needs a disciplined Thinking Pipeline (11 stages) and three Cognitive Engines: Contradiction Detection, Self-Doubt, and Root Cause Analysis. These are the reasoning core of VIR.

### Architectural Details
- `vir_runtime/pipeline/thinking_pipeline.py` — 11-stage asyncio state machine
- `vir_runtime/pipeline/stages/` — one file per stage
- `vir_runtime/engines/cognitive/contradiction_engine.py` — ContradictionRecord
- `vir_runtime/engines/cognitive/self_doubt_engine.py` — Bounded retry + strategy change
- `vir_runtime/engines/cognitive/rca_engine.py` — Root cause validation + classification
- `vir_runtime/engines/cognitive/hypothesis_engine.py` — Hypothesis generation + rejection

### Verification Checklist
- [ ] docs/plans/FEAT-062_vir_cognitive_engines_plan.md generated and approved
- [ ] docs/designs/FEAT-062_vir_cognitive_engines_blueprint.md generated and approved
