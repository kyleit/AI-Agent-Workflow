<!-- docs/brainstorming/FEAT-063_vir_multi_agent_orchestration_and_consensus_engine.md -->

---
feature_id: FEAT-063
feature_name: Visual Intelligence Runtime — Multi-Agent Architecture & Consensus Engine
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-062_vir_thinking_pipeline_and_cognitive_engines.md
next_artifact: ../plans/FEAT-063_vir_multi_agent_consensus_plan.md
---

# Master Requirement Document – VIR Multi-Agent Architecture & Consensus Engine

## 1. Feature ID & Name
- **Feature ID**: FEAT-063
- **Feature Name**: Visual Intelligence Runtime — Multi-Agent Architecture & Consensus Engine

## 2. Original Idea
Design VIR's complete multi-agent architecture: Agent Contracts, Agent Memory Model (5 memory types per agent), Agent Communication Protocol, and the Consensus Engine using a weighted authority model with domain-specific veto rights. Consensus replaces simple majority voting with expertise-weighted, veto-capable decision-making.

## 3. Business Problem
- **Problem**: In a multi-agent system with agents observing different aspects of an application (visual, network, state, design, accessibility), reaching a final verdict requires more than aggregating individual opinions. Different agents have different expertise. A Design Authority Agent's opinion on visual hierarchy carries more weight than a general state agent's opinion on the same topic. Simple majority voting would create incorrect verdicts where the less expert agents outvote the domain expert.
- **Why it matters**: The Consensus Engine is what gives VIR its final pass/fail authority. Getting it wrong means false PASSes (bugs escape) or false FAILs (developer frustration). Weighted authority + domain veto = accurate, trustworthy verdicts.
- **Who is affected**: All VIR agents, Quality Gate, Reporting System, Verification Agent, frontend engineers receiving reports.
- **Expected outcome**: A multi-agent system with explicit authority domains, memory models, communication protocols, and a Consensus Engine that produces accurate, evidence-backed quality gate verdicts.

## 4. Requirement Discovery

### Functional Requirements

#### Agent Architecture
- FR-01: Every VIR agent must implement the Agent Contract interface: name, version, domain, authority_level, veto_topics, memory_config, subscriptions, publications, capabilities.
- FR-02: Every VIR agent must maintain 5 memory types:
  - **Short-term Memory**: Current execution context only; cleared between runs.
  - **Working Memory**: Current active investigation context; cleared when investigation closes.
  - **Long-term Memory**: Historical patterns, past bugs, past fixes; persisted in SQLite.
  - **Shared Memory**: Evidence shared through the event bus; accessible to all agents.
  - **Knowledge Memory**: Lessons promoted to Knowledge Runtime or Design Knowledge Base.
- FR-03: Agents must communicate exclusively through the event bus (no direct method calls between agents).
- FR-04: Agent registration must validate: all required contract fields, topic subscriptions valid, authority level in range [0.0–1.0].
- FR-05: Agent lifecycle: DORMANT → REGISTERED → ACTIVE → PAUSED → TERMINATED.

#### Consensus Engine
- FR-06: Consensus Engine must implement weighted authority model; not simple majority voting.
- FR-07: Authority weights must be domain-specific:
  - Business Flow Observer: primary authority over business-process correctness
  - Application State Observer: primary authority over runtime-state conclusions
  - Network Observer: primary authority over API transport behavior
  - Frontend Design Review Agent: veto power over visual hierarchy, design-system compliance, typography, spacing, component consistency, theme quality, UX design compliance, responsive design quality
  - Accessibility Agent: veto power over critical accessibility failures
  - Security Agent: any critical security finding blocks PASS
  - Regression Agent: blocks PASS when confirmed regression exists
  - Verification Agent: aggregates evidence; does not independently invent conclusions
- FR-08: Consensus Engine must support veto activation: any agent with veto rights can issue VETO on their domain topics.
- FR-09: Veto must be supported by evidence (minimum 1 evidence object). Unsupported veto treated as ADVISORY.
- FR-10: PASS verdict requires: all critical domains pass + no active veto + no unresolved critical contradiction + confidence ≥ configured threshold.
- FR-11: Consensus Engine must produce a ConsensusRecord: verdict, verdict_confidence, contributing_agents, evidence_weights, active_vetoes, resolved_vetoes, unresolved_contradictions, domain_scores.
- FR-12: Consensus Engine must support configurable confidence thresholds per verdict type (PASS/PARTIAL/FAIL/BLOCKED).
- FR-13: Consensus Engine publishes verdict to `vir.consensus.verdict` topic.

#### Communication Protocol
- FR-14: All inter-agent messages must include: message_id, sender_agent, recipient_topic, timestamp, message_type, payload, correlation_id (investigation_id).
- FR-15: Message types: EVIDENCE, QUERY, QUERY_RESPONSE, VETO, VETO_WITHDRAW, DIRECTIVE, VERDICT, HEARTBEAT.
- FR-16: Agents must not process messages with timestamps older than configurable staleness threshold.

### Non-functional Requirements
- NFR-01: Agent registration < 100ms per agent.
- NFR-02: Consensus calculation < 500ms for up to 20 contributing agents.
- NFR-03: Agent memory load from SQLite < 200ms at startup.
- NFR-04: Veto must be processed before PASS verdict issued; no race condition.
- NFR-05: All agent communication logged with message IDs for complete audit trail.

### Technical Constraints
- TC-01: Agent contracts implemented as Python Protocol + dataclass.
- TC-02: Agent memory backed by: asyncio dict (short-term/working), SQLite (long-term), event bus (shared), Knowledge Runtime API (knowledge memory).
- TC-03: Consensus Engine is a specialized agent registered in the Agent Registry.
- TC-04: Veto register maintained in active investigation state.
- TC-05: Authority weights configurable in `vir_agents.yaml`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Agent Contract interface | BP-VIR-011 | Register agent missing required field | Registration fails with clear error |
| FR-02 | Must | 5 memory types per agent | BP-VIR-012 | Agent stores in all 5 memory types | All 5 types persist and retrieve correctly |
| FR-06 | Must | Weighted authority | BP-VIR-010 | 3 agents agree (low weight) vs 1 Design Agent veto | Design Agent veto wins |
| FR-09 | Must | Evidence-backed veto | BP-VIR-010 | Veto without evidence | Treated as ADVISORY, not blocking PASS |
| FR-10 | Must | PASS conditions | BP-VIR-010 | All conditions met | PASS issued |
| FR-10 | Must | PASS blocked by active veto | BP-VIR-010 | Design veto active | PASS blocked; verdict = FAIL |
| FR-12 | Must | Configurable thresholds | BP-VIR-010 | Set PASS threshold to 0.9; score=0.85 | PARTIAL verdict issued |
| FR-14 | Must | Message protocol | BP-VIR-011 | All inter-agent messages inspected | All required fields present |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| All VIR Agents | Internal | Critical | Critical | Standard contract and communication interface |
| Quality Gate | Internal | High | High | Authoritative Consensus verdict |
| Reporting System | Internal | High | High | ConsensusRecord for report narrative |
| Design Authority Agent | Primary | High | High | Enforced design veto power |
| Accessibility Agent | Primary | High | High | Enforced accessibility veto power |
| Human Engineer | Primary | Medium | Medium | Trustworthy pass/fail verdicts with evidence |

## 7. Scope Boundary

### In Scope
- Agent Contract interface definition
- 5-memory-type model per agent
- Agent lifecycle management
- Agent Registry integration
- Consensus Engine with weighted authority
- Veto mechanism
- Communication protocol
- ConsensusRecord schema

### Out of Scope
- Individual agent implementations beyond contracts (covered in respective FEAT documents)
- Report narrative generation (FEAT-066)
- Memory persistence details (FEAT-064)

### Deferred Scope
- Agent-to-agent direct negotiation (beyond bus communication)
- Distributed agent deployment

### Future Scope
- Dynamic authority weight adjustment based on historical accuracy
- LLM-based agent for specialized reasoning

## 8. Dependency Graph Preview

- FEAT-063: Multi-Agent & Consensus Engine (Must)
  - FEAT-061: Evidence Domain (consensus uses evidence weights)
  - FEAT-062: Thinking Pipeline (cognitive conclusions feed consensus)
  - FEAT-064: Memory Engine (long-term + knowledge memory backend)
  - FEAT-066: Quality Gates (consumer of consensus verdict)

## 9. Data Flow Preview

- All agents complete domain analysis → publish domain conclusions to `vir.domain.*`
  └── Consensus Engine subscribes to all domain conclusion topics
      └── For each domain: apply authority weight × evidence confidence = domain_score
          └── Check veto register: Design Agent has VETO on typography spacing
              └── VETO has evidence (ev-045: typography violation confirmed)
                  └── VETO is evidence-backed → BLOCKING
                      └── Consensus: domain_scores OK but VETO active → verdict = FAIL
                          └── ConsensusRecord produced: verdict=FAIL, active_vetoes=[design/typography]
                              └── Published to `vir.consensus.verdict`
                                  └── Quality Gate receives → formats report → presents to user

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| FEAT-018 multi-agent patterns | docs/brainstorming/ | Reference | Existing multi-agent architecture decisions |
| FEAT-020 multi-agent analysis | docs/brainstorming/ | Reference | Agent analysis patterns |
| task_orchestrator.py | scripts/ | Extend | Agent lifecycle management base |
| approval_gate.py | scripts/ | Reuse | Human escalation; adapted for veto escalation |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: Critical — Consensus is the final decision authority for all VIR verdicts

## 12. Migration Strategy

- **Backward Compatibility**: New architecture; no migration
- **Migration Phases**: Phase 6 implements full multi-agent + consensus; Phase 3-5 use simplified voting as interim

## 13. Architecture Principles

- **API First**: All agent contracts and consensus protocol defined before agent implementations
- **Domain Expertise**: Authority weighted by domain knowledge, not voting count
- **Evidence First**: No veto or vote valid without supporting evidence

## 14. Non Goals

- Consensus Engine does not perform investigation (Cognitive Engines do)
- Does not use simple 50%/51% majority voting

## 15. ROI Analysis

- **Value**: Accurate verdicts reduce false positives (wasted engineer time) and false negatives (escaped bugs)
- **Trust**: Evidence-backed verdicts are trustworthy and auditable
- **Specialization**: Domain veto means each agent is deeply expert rather than generically mediocre

## 16. Success Metrics

- **Verdict Accuracy**: > 95% agreement with expert human review on test scenarios
- **Veto Enforcement**: 100% — evidence-backed veto always blocks PASS
- **Consensus Speed**: < 500ms for full consensus calculation
- **False Positive Rate**: < 5% FAIL verdicts on known-good pages

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Authority weights incorrectly configured produce biased verdicts | High | Medium | Default weights validated on test suite; override requires explicit config change | Architect |
| Veto deadlock (two agents veto each other's domain) | Medium | Low | Veto only applies to own domain; cross-domain veto impossible by design | Architect |
| Consensus Engine slow on many agents | Medium | Low | Parallel domain score calculation; consensus aggregation O(n) | Backend Engineer |
| Agent contract too strict prevents valid agents | Medium | Low | Optional fields clearly marked in contract; fail fast with descriptive error | Architect |

## 18. Technical Questions

- How should authority weights be initially calibrated (empirical testing vs expert assignment)?
- Should veto withdrawal require evidence update or simply be time-based?
- How does Consensus Engine handle an agent that is DORMANT during verdict calculation?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Authority weight calibration | Pending | Start with expert assignment; empirical tuning after 10 real runs |
| Veto withdrawal mechanism | Pending | Evidence update required; decide in BP-VIR-010 |
| DORMANT agent handling | Pending | DORMANT agent excluded from consensus; minimum quorum check; decide in BP-VIR-010 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-008: Weighted authority model vs majority voting

## 21. Knowledge Update Impact

- **patterns**: Yes — Weighted Consensus pattern; Veto-based Authority pattern; Agent Memory Model pattern
- **architecture**: Yes — Multi-agent consensus architecture
- **ADR**: Yes — ADR-VIR-008

## 22. Test Strategy Preview

- **Unit Tests**: Authority weight calculation; veto activation/withdrawal; PASS condition enforcement; message protocol validation
- **Integration Tests**: 5 agents → consensus on known test scenarios; veto blocks PASS
- **Edge Case Tests**: Agent dormant during verdict; evidence-less veto treated as advisory
- **Calibration Tests**: Authority weights produce correct verdicts on 20 labeled test scenarios

## 23. Extension Impact

- **Extension UI Changes**: Agent status panel in Visualizer; veto indicator; consensus verdict display
- **Affected ViewModels**: Agent health grid; verdict confidence gauge; veto list

## 24. Complexity Estimation

- **Implementation Complexity**: Very High
- **Estimated Refactoring Percentage**: 10% existing patterns / 90% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 6 (Multi-Agent Orchestration & Consensus)
- **Prerequisites**: FEAT-061 (Evidence), FEAT-062 (Cognitive), FEAT-064 (Memory for agent long-term memory)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Consensus model? | Weighted authority — not majority voting |
| Design Authority veto? | Yes — veto power on visual/design/UX/responsive |
| Accessibility veto? | Yes — veto on critical accessibility failures |
| Security findings? | Block PASS unconditionally |
| Agent memory types? | 5 types: Short-term, Working, Long-term, Shared, Knowledge |

## 27. Requirement Readiness Score

- **Score**: 95/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): Agent without required contract field fails registration with descriptive error
- [ ] AC-02 (FR-02): Agent stores and retrieves from all 5 memory types without error
- [ ] AC-03 (FR-06): Design Agent veto overrides 3 agreeing lower-authority agents; PASS blocked
- [ ] AC-04 (FR-09): Veto without evidence treated as ADVISORY; PASS not blocked
- [ ] AC-05 (FR-10): All PASS conditions met → PASS verdict within 500ms
- [ ] AC-06 (FR-11): ConsensusRecord contains all required fields including evidence_weights

## 35. Final Planning Prompt

### Problem Statement
VIR needs a complete multi-agent architecture with Agent Contracts, 5 memory types per agent, communication protocol, and a weighted-authority Consensus Engine with domain veto rights.

### Architectural Details
- `vir_runtime/agents/base/agent_contract.py` — Protocol interface
- `vir_runtime/agents/base/agent_memory.py` — 5 memory types
- `vir_runtime/agents/communication/message.py` — Message protocol
- `vir_runtime/engines/consensus/consensus_engine.py` — Weighted authority engine
- `vir_runtime/engines/consensus/veto_register.py` — Veto management
- `vir_runtime/engines/consensus/authority_weights.py` — Weight configuration
- `config/vir_agents.yaml` — Agent authority configuration

### Verification Checklist
- [ ] docs/plans/FEAT-063_vir_multi_agent_consensus_plan.md generated and approved
- [ ] docs/designs/FEAT-063_vir_multi_agent_consensus_blueprint.md generated and approved
