<!-- docs/brainstorming/FEAT-069_vir_sdlc_integration_and_future_ai_capabilities.md -->

---
feature_id: FEAT-069
feature_name: Visual Intelligence Runtime — SDLC Integration & Future AI Capabilities Roadmap
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-068_vir_runtime_execution_modes.md
next_artifact: ../plans/FEAT-069_vir_sdlc_integration_plan.md
---

# Master Requirement Document – VIR SDLC Integration & Future AI Capabilities Roadmap

## 1. Feature ID & Name
- **Feature ID**: FEAT-069
- **Feature Name**: Visual Intelligence Runtime — SDLC Integration & Future AI Capabilities Roadmap

## 2. Original Idea
Define VIR's complete integration strategy with the AIWF Software Development Lifecycle (SDLC), map AIWF agent interactions with VIR, and document the architectural roadmap for adding future AI capabilities — local vision models, cloud VLMs, LLM-based planning agents, and specialized agents (security, accessibility, performance) — without changing the runtime core.

## 3. Business Problem
- **Problem**: VIR must fit into the existing AIWF workflow without breaking existing approval gates, workflow runtime, and agent interactions. Future AI capabilities must be addable as adapters/agents without re-engineering VIR's architecture. Without a clear SDLC integration map and future-proof extension plan, VIR risks becoming a standalone tool disconnected from the workflow.
- **Why it matters**: VIR's long-term value depends on deep AIWF integration. An isolated quality checker has limited ROI; a fully integrated perception runtime that participates in every SDLC phase is transformative.
- **Who is affected**: All AIWF agents (Coder, Reviewer, Release Manager, Planner, Architect), CI/CD pipeline, future AI capability developers.
- **Expected outcome**: A complete SDLC integration map showing when/how VIR is invoked at each workflow phase, and a formal extension architecture enabling any new AI capability to be added as a VIR adapter or agent.

## 4. Requirement Discovery

### Functional Requirements

#### SDLC Integration
- FR-01: VIR must integrate at 4 SDLC checkpoints:
  1. **Implementation Checkpoint**: After Coder Agent completes implementation, VIR runs Standard profile verification.
  2. **Debug Checkpoint**: When `implementation-to-debug` skill is invoked, VIR provides visual evidence for investigation.
  3. **Review Checkpoint**: Before `debug-to-verify` approval gate, VIR runs Deep profile comprehensive audit.
  4. **Release Checkpoint**: `implementation-to-release` gate invokes VIR CI mode; FAIL blocks release.
- FR-02: VIR must integrate with the AIWF Approval Gate system: VIR FAIL result blocks relevant approval gates.
- FR-03: VIR must update the AIWF workflow checkpoint state: VIR PASS updates workflow to appropriate next checkpoint.
- FR-04: VIR reports stored in `docs/verification/FEAT-XXX_vir_report.md` (matching existing verification convention).
- FR-05: VIR must read feature context from: blueprint path, feature ID, approved implementation scope.
- FR-06: VIR must never authorize code changes outside the blueprint-approved scope.
- FR-07: VIR must produce artifacts that satisfy the AIWF Artifact Policy (structured, versioned, linked to feature ID).

#### AIWF Agent Interactions
- FR-08: **Coder Agent** → invokes VIR Standard profile after each implementation milestone.
- FR-09: **Reviewer Agent** → invokes VIR Deep profile; uses VIR report as evidence for review verdict.
- FR-10: **Planner Agent** → receives VIR historical data for regression risk estimation in future plans.
- FR-11: **Architect Agent** → consults VIR Digital Twin data for architecture validation.
- FR-12: **Release Manager Agent** → invokes VIR CI mode as mandatory gate before publish.
- FR-13: **Debug Skill** → invokes VIR Lightweight profile to gather initial visual evidence before manual investigation.

#### Future AI Capabilities Architecture
- FR-14: Any new AI capability must be addable as either: (a) a new Adapter, or (b) a new Agent registered in Agent Registry.
- FR-15: Adding a new capability must NOT require changes to: VIR core runtime, Orchestrator, Event Bus, existing agents, Quality Gate logic, Consensus Engine core.
- FR-16: Local Vision Models (e.g., future local LLaVA v2, MiniCPM-V) must be addable as a Vision Adapter replacing or supplementing Layer 4.
- FR-17: Cloud Vision Models (e.g., OpenAI GPT-4V, Claude Vision, Gemini Vision) must be addable as a Vision Adapter with API key configuration.
- FR-18: LLM-based Planning Agents must be addable as Agent implementations with Agent Contract, subscribing to relevant topics.
- FR-19: Specialized QA Agents (performance QA, load testing correlation, browser compatibility) must be addable as domain agents with optional authority/veto.
- FR-20: Security Review Agents must be addable with veto power over security-related topics.
- FR-21: All future AI adapters/agents must declare their: provider, version, capabilities, fallback_behavior, cost_tier, privacy_level.
- FR-22: Privacy-sensitive agents (cloud VLM sending screenshots to external API) must require explicit user consent configuration.

### Non-functional Requirements
- NFR-01: Adding a new adapter must require < 4 hours of engineering time.
- NFR-02: Adding a new agent must require < 8 hours of engineering time (including tests).
- NFR-03: SDLC integration must not increase existing workflow phase duration by > 20%.
- NFR-04: VIR SDLC events must not break existing AIWF workflow checkpoint compatibility.
- NFR-05: Future AI capabilities must be opt-in; default profile must not require any AI API keys.

### Technical Constraints
- TC-01: SDLC integration via AIWF workflow runtime CLI calls and checkpoint state updates.
- TC-02: New agents satisfy Python Protocol interface (Agent Contract).
- TC-03: New adapters satisfy Python Protocol interface (Adapter Contract for their type).
- TC-04: Privacy-sensitive adapters require `consent: true` in adapters.yaml.
- TC-05: Cost-tier declaration enables VIR to warn users before invoking expensive cloud APIs.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | 4 SDLC checkpoints | BP-VIR-017 | Invoke VIR at each checkpoint | VIR runs; correct profile; result feeds gate |
| FR-02 | Must | Approval gate integration | BP-VIR-017 | VIR FAIL → approval gate blocked | Gate cannot be bypassed without VIR PASS |
| FR-04 | Must | Report in docs/verification/ | BP-VIR-017 | Run VIR | Report at correct path |
| FR-15 | Must | No core changes for new capability | BP-VIR-017 | Add new agent; verify core files unchanged | Zero core file modifications |
| FR-22 | Must | Cloud VLM consent | BP-VIR-017 | Enable cloud VLM without consent | Startup error: consent required |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| All AIWF Agents | Primary/Internal | Critical | Critical | VIR integrated into their workflow phases |
| Future Capability Developers | Future | High | High | Clear extension points without core changes |
| Security Architect | Future | High | High | Security Agent pluggable with veto power |
| Product Teams | External | Medium | Medium | VIR becomes universal quality layer |

## 7. Scope Boundary

### In Scope
- 4 SDLC checkpoint integration points
- AIWF Agent interaction mapping
- VIR extension architecture (adapter + agent patterns)
- Future AI capability registry design
- Privacy consent framework for cloud AI adapters
- Cost tier declaration

### Out of Scope
- Implementation of future AI capabilities (roadmap only)
- CI/CD pipeline YAML files (DevOps task)
- Cloud VLM provider accounts and API keys

### Deferred Scope
- Distributed VIR for multi-machine CI
- Cross-project shared VIR memory

### Future Scope
- VIR as AIWF's universal perception runtime beyond frontend (backend API, infrastructure, security scanning)
- VIR as autonomous agent participating in multi-agent planning

## 8. Dependency Graph Preview

- FEAT-069: SDLC Integration (Should — cross-cutting)
  - FEAT-055: VIR Foundation (all concepts reference)
  - FEAT-056: VIR Core (checkpoint integration)
  - FEAT-057: Adapter Architecture (extension point)
  - FEAT-063: Multi-Agent (agent extension point)
  - FEAT-066: Quality Gates (SDLC gate integration)
  - AIWF Workflow Runtime (external dependency)

## 9. Data Flow Preview

**Release Checkpoint:**
```
Release Manager Agent invokes approval gate
→ Gate requires VIR PASS as prerequisite
→ VIR invoked: python -m vir_runtime run --mode ci --feature FEAT-055 --profile standard
→ VIR runs full investigation → Gate = PASS → exit code 0
→ Approval gate proceeds → Release Manager publishes release
→ VIR report linked in release notes as verification artifact
```

**New Agent Addition:**
```
Engineer creates SecurityReviewAgent(AgentContract)
→ Declares: domain=security, veto_topics=[security.*], authority_level=0.95
→ Adds to vir_agents.yaml: security_review_agent: SecurityReviewAgent
→ VIR Adapter Registry loads on next startup
→ SecurityReviewAgent begins receiving relevant events
→ Zero changes to: orchestrator.py, consensus_engine.py, quality_gate.py
```

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| workflow_runtime.py | scripts/ | Extend | SDLC checkpoint integration; VIR called by workflow |
| approval_gate.py | scripts/ | Extend | VIR FAIL blocks approval gates |
| checkpoint.py | scripts/ | Extend | VIR PASS updates checkpoint state |
| AIWF SDLC Skills | `.agents/skills/` | Integrate | VIR invocation added to implementation/debug/review/release skills |

## 11. Dependency & Blast Radius Analysis

- **Affected Skills**: implementation-to-debug, debug-to-verify, implementation-to-release (all need VIR invocation added)
- **Affected Runtime**: workflow_runtime.py checkpoint state; approval_gate.py
- **Impact Level**: High — cross-cutting integration; touches all SDLC phases

## 12. Migration Strategy

- **Backward Compatibility**: Skills extended; existing invocation paths unchanged until VIR Phase 8+ complete
- **Migration Phases**: Phase 8 adds VIR to debug skill; Phase 9 adds CI gate; Phase 10 adds full SDLC integration

## 13. Architecture Principles

- **API First**: All SDLC integration points published as contracts before implementation
- **Backward Compatibility**: Existing skills continue working without VIR; VIR is additive
- **Incremental Updates**: SDLC checkpoints added one by one starting with debug

## 14. Non Goals

- VIR does not replace the AIWF workflow runtime
- VIR does not manage Git operations
- VIR does not execute deployment

## 15. ROI Analysis

- **Workflow Value**: VIR becomes a quality signal at every SDLC phase → fewer bugs in production
- **Future-Proof Value**: New AI capabilities (GPT-4V, specialized agents) addable in hours not sprints
- **Universal Perception**: VIR grows from "frontend QA tool" to "universal AIWF perception runtime"

## 16. Success Metrics

- **SDLC Coverage**: VIR active at 4/4 checkpoint types
- **Extension Speed**: New adapter added in < 4 hours; new agent in < 8 hours
- **Zero Core Changes**: Adding new capability → zero modifications to core files (verified by diff)
- **Privacy Compliance**: Cloud VLM without consent → startup error 100% of the time

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| VIR SDLC integration increases workflow duration excessively | High | Medium | Lightweight profile for fast checkpoints; async report generation | Performance Engineer |
| Future agent breaks existing consensus logic | High | Low | Agent Protocol enforced; integration tests on each new agent | QA Engineer |
| Cloud VLM costs exceed budget | Medium | Medium | Cost tier declaration + user warning; cloud VLM off by default | Finance/Architecture |
| Privacy violation from screenshots sent to cloud API | High | Low | Explicit consent required; local-only default | Security |

## 18. Technical Questions

- Should VIR SDLC integration be automatic (skill triggers VIR) or explicit (agent must request VIR run)?
- How does VIR handle a feature that spans multiple pages/flows — should investigation scope be configurable?
- When VIR BLOCKS (inconclusive), should the approval gate also block or allow human override?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Automatic vs explicit VIR invocation | Pending | Explicit for Phase 8; automatic opt-in for Phase 9+ |
| Multi-page investigation scope | Pending | Configurable scope file per feature; decide in BP-VIR-017 |
| BLOCKED gate override | Pending | Human override required; logged; decide in BP-VIR-017 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-011: VIR as SDLC integration point vs standalone tool; ADR-VIR-012: Privacy consent framework for cloud AI adapters

## 21. Knowledge Update Impact

- **architecture**: Yes — VIR SDLC integration map; extension architecture
- **patterns**: Yes — SDLC checkpoint integration pattern; pluggable AI adapter pattern
- **ADR**: Yes — ADR-VIR-011, ADR-VIR-012
- **lessons**: Yes — Perception-first SDLC principle documented

## 22. Test Strategy Preview

- **Unit Tests**: Checkpoint state update; approval gate VIR integration; cost tier warning
- **Integration Tests**: VIR invoked at each SDLC checkpoint; correct profile used; report produced
- **Extension Tests**: New agent added; zero core file changes; integration test passes
- **Privacy Tests**: Cloud VLM without consent → startup error

## 23. Extension Impact

- **Extension UI Changes**: SDLC phase indicator in Visualizer showing VIR status per checkpoint
- **Affected ViewModels**: Workflow phase VIR status badge

## 24. Complexity Estimation

- **Implementation Complexity**: Medium-High
- **Estimated Refactoring Percentage**: 15% existing (skill integration) / 85% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 9 (CI/CD Integration) + Phase 10 (Advanced Adapters + SDLC Full)
- **Prerequisites**: All prior FEAT-055 through FEAT-068

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| VIR relationship to SDLC? | Integrated at 4 checkpoints; not standalone |
| Future AI capabilities? | Adapter/Agent plugins; no core changes |
| Privacy for cloud VLMs? | Explicit consent required in config |
| VIR scope beyond frontend? | Future roadmap; universal perception runtime |

## 27. Requirement Readiness Score

- **Score**: 92/100
- **Status**: Ready ≥ 85

## 28. Existing Project Context

- **Memory Source**: All prior FEAT documents + AIWF AGENTS.md + AI_RULES.md for SDLC phase definitions
- **Existing Architecture Summary**: AIWF has formal approval gates, checkpoint system, skill invocation, workflow runtime. VIR SDLC integration extends these without replacing them.

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): VIR invoked at Implementation checkpoint; Standard profile report generated
- [ ] AC-02 (FR-02): VIR FAIL result blocks release approval gate; cannot bypass without human override
- [ ] AC-03 (FR-15): New agent added; grep confirms zero core file changes
- [ ] AC-04 (FR-22): Cloud VLM enabled without consent → startup error with actionable message

## 35. Final Planning Prompt

### Problem Statement
VIR needs SDLC integration at 4 checkpoints and a formal extension architecture enabling new AI capabilities as adapters/agents without core changes. Privacy consent framework for cloud AI.

### Objectives
4 checkpoint integrations; AIWF approval gate VIR dependency; pluggable adapter/agent extension pattern; cost tier and privacy declarations; future AI capability roadmap.

### Architectural Details
- `vir_runtime/sdlc/checkpoint_integration.py` — SDLC checkpoint hooks
- `vir_runtime/sdlc/gate_integration.py` — Approval gate VIR dependency
- `vir_runtime/extensions/capability_registry.py` — Future capability registration
- `vir_runtime/extensions/privacy_consent.py` — Cloud AI consent check
- Updates to: `.agents/skills/implementation-to-debug/SKILL.md`
- Updates to: `.agents/skills/debug-to-verify/SKILL.md`
- Updates to: `.agents/skills/implementation-to-release/SKILL.md`

### Future AI Capability Roadmap
| Phase | Capability | Type | Notes |
|---|---|---|---|
| Phase 10 | Local Vision Model (LLaVA v2) | Vision Adapter | GPU optional |
| Phase 11 | Cloud VLM (GPT-4V) | Vision Adapter | Consent required |
| Phase 11 | Cloud VLM (Claude Vision) | Vision Adapter | Consent required |
| Phase 12 | LLM Planning Agent | Agent | Hypothesis generation assistant |
| Phase 12 | Security Review Agent | Agent | OWASP checks + CSP validation |
| Phase 13 | Browser Compatibility Agent | Agent | Cross-browser diff detection |
| Phase 14 | Accessibility Specialist Agent | Agent | Advanced WCAG AAA + AT testing |
| Phase 15 | VIR for Backend APIs | Scope Extension | Perception beyond frontend |

### Verification Checklist
- [ ] docs/plans/FEAT-069_vir_sdlc_integration_plan.md generated and approved
- [ ] docs/designs/FEAT-069_vir_sdlc_integration_blueprint.md generated and approved
