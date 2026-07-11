<!-- docs/brainstorming/FEAT-065_vir_design_authority_and_design_knowledge_base.md -->

---
feature_id: FEAT-065
feature_name: Visual Intelligence Runtime — Design Authority & Design Knowledge Base
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-064_vir_memory_architecture_and_continuous_learning.md
next_artifact: ../plans/FEAT-065_vir_design_authority_plan.md
---

# Master Requirement Document – VIR Design Authority & Design Knowledge Base

## 1. Feature ID & Name
- **Feature ID**: FEAT-065
- **Feature Name**: Visual Intelligence Runtime — Design Authority & Design Knowledge Base

## 2. Original Idea
Evolve the existing `frontend-design` skill into an independent Design Knowledge Base that VIR consumes through a well-defined authority interface. Define the Design Authority Agent as the VIR agent with veto power over all visual and UX quality decisions, backed by structured design rules, design tokens, component standards, and pattern libraries.

## 3. Business Problem
- **Problem**: The current `frontend-design` skill contains valuable design knowledge but it is expressed as free-text instructions in a SKILL.md file. VIR cannot programmatically query design rules, validate typography decisions, or apply token compliance checks from unstructured text. The Design Knowledge Base must become a structured, queryable authority.
- **Why it matters**: Design quality cannot be delegated to general-purpose vision agents. A dedicated Design Authority with structured knowledge ensures VIR enforces design consistency without hard-coding design decisions in runtime code.
- **Who is affected**: Design Authority Agent, Vision Engine (Layer 4 VLM evaluation criteria), Quality Gate, Reporting System, frontend developers receiving design feedback.
- **Expected outcome**: A structured Design Knowledge Base storing all design rules, tokens, standards, and patterns — queryable by VIR agents at runtime — with the Design Authority Agent having veto power over all design-domain decisions.

## 4. Requirement Discovery

### Functional Requirements

#### Design Knowledge Base
- FR-01: Design Knowledge Base must store and expose: Design Rules, Design Tokens, Spacing Rules, Typography Standards, Color Systems, Component Standards, Accessibility Rules (design-related), UX Rules, Pattern Library, Best Practices.
- FR-02: Design Knowledge Base must be queryable by entity type: component, page, interaction pattern, color, typography, spacing, layout.
- FR-03: Design rules must be versioned; each project can pin to a specific design system version.
- FR-04: Design tokens stored as structured JSON/YAML: color palette, spacing scale, typography scale, border radius, shadow levels, z-index scale, animation timing.
- FR-05: Pattern Library must contain: positive patterns (correct usage examples), anti-patterns (incorrect usage examples), with visual examples stored as reference screenshots.
- FR-06: Design Knowledge Base must expose a REST-like Python API for VIR agents to query rules.
- FR-07: VIR must never hardcode design decisions; all design validation must reference Design Knowledge Base rules.
- FR-08: Design Knowledge Base must be extensible: projects can add custom rules without modifying core rules.

#### Design Authority Agent
- FR-09: Design Authority Agent implements full Agent Contract with domain=`design` and veto_topics covering: visual_hierarchy, design_system_compliance, typography, spacing, component_consistency, theme_quality, ux_design_compliance, responsive_design_quality.
- FR-10: Design Authority Agent evaluates Vision Engine Layer 4 (VLM) findings against Design Knowledge Base rules.
- FR-11: Design Authority Agent uses VLM output as input, not as a decision. VLM provides semantic analysis; Design Authority Agent validates against formal rules.
- FR-12: Design Authority Agent must issue structured DesignFinding objects: rule_id, component, violation_type, severity, expected_value, actual_value, evidence_id, recommendation.
- FR-13: Design Authority Agent may issue VETO when: design system compliance fails for a MUST rule; contrast ratio below WCAG threshold; typography scale violated; critical spacing rule broken.
- FR-14: Design Authority Agent must not issue VETO for SHOULD or COULD rule violations (advisory only).
- FR-15: Design Authority Agent must propose improvements to `frontend-design` skill rules when a new pattern not in the library is discovered and validated. Human confirmation required before writing.

### Non-functional Requirements
- NFR-01: Design Knowledge Base query < 100ms per rule lookup.
- NFR-02: Design token validation < 200ms for full page token audit.
- NFR-03: Design Authority Agent must not block other agents; runs concurrently.
- NFR-04: New design rules addable without VIR core restart.
- NFR-05: Design rule violations logged with rule ID for traceability.

### Technical Constraints
- TC-01: Design Knowledge Base stored as structured YAML in `.agents/visual-runtime/design-kb/`.
- TC-02: Design Authority Agent is a standard VIR agent registered in the Agent Registry.
- TC-03: frontend-design SKILL.md is the canonical human-readable source; Design Knowledge Base is the machine-readable derived form.
- TC-04: DesignFinding objects are subtype of Evidence domain objects.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Design KB structure | BP-VIR-013 | Query all 10 knowledge types | All return valid structured data |
| FR-04 | Must | Design tokens stored | BP-VIR-013 | Query primary color token | Returns hex value + usage rules |
| FR-07 | Must | No hardcoded decisions | BP-VIR-013 | Code audit: grep for hardcoded hex/px in agents | Zero hardcoded design values |
| FR-09 | Must | Design Authority Agent contract | BP-VIR-013 | Agent registration | Contract validated; domain=design |
| FR-13 | Must | VETO on MUST violations | BP-VIR-013 | Inject contrast ratio violation | VETO issued; PASS blocked |
| FR-14 | Must | No VETO on SHOULD | BP-VIR-013 | Inject SHOULD violation | DesignFinding advisory; no VETO |
| FR-15 | Should | Rule improvement proposal | BP-VIR-013 | New pattern discovered | Human confirmation requested before writing |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Vision Engine | Internal | High | High | Layer 4 VLM evaluation context |
| Consensus Engine | Internal | High | High | Design Authority veto power |
| Frontend Developers | Primary | High | High | Structured design feedback with rule references |
| Design System Owners | External | High | High | Design rules enforced automatically |
| Frontend-design Skill | Internal | High | High | Evolves into queryable Knowledge Base |

## 7. Scope Boundary

### In Scope
- Design Knowledge Base structure, storage, and query API
- Design token schema
- Pattern Library (positive + anti-patterns)
- Design Authority Agent contract and implementation
- DesignFinding domain object
- VETO/advisory distinction (MUST vs SHOULD rules)
- Rule improvement proposal workflow

### Out of Scope
- Accessibility Engine logic (FEAT-067)
- VLM implementation (FEAT-057 adapter + FEAT-058 Layer 4)
- Report formatting (FEAT-066)

### Deferred Scope
- Cross-project design system inheritance
- Real-time design token sync from Figma/design tools

### Future Scope
- Figma/design-tool connector for token sync
- Automated design system documentation generation

## 8. Dependency Graph Preview

- FEAT-065: Design Authority & Knowledge Base (Should)
  - FEAT-058: Vision Engine Layer 4 (VLM provides input to Design Authority)
  - FEAT-063: Multi-Agent (Design Authority registered as agent with veto)
  - FEAT-066: Quality Gates (receives Design Authority verdict)

## 9. Data Flow Preview

- Vision Engine Layer 4 (VLM) → `VLMFinding: poor visual hierarchy on product grid`
  └── Design Authority Agent receives finding
      └── Queries Design KB: `layout.grid.hierarchy` → rule: `grid items must have clear visual weight hierarchy`
          └── Compares VLM finding to rule → VIOLATION of MUST rule
              └── DesignFinding created: {rule_id: LAYOUT-042, severity: ERROR, violation: hierarchy_absent}
                  └── Evidence published → Consensus Engine
                      └── Design Authority issues VETO on `visual_hierarchy` topic
                          └── Consensus: VETO active → PASS blocked → verdict = FAIL

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-design SKILL.md | `.agents/skills/frontend-design/SKILL.md` | Extend | Source of design knowledge; KB derived from this |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: High — Design Authority is the sole design quality enforcer

## 12. Migration Strategy

- **Backward Compatibility**: frontend-design skill external interface preserved; internal knowledge migrated to KB
- **Migration Phases**: Phase 4 builds Design KB from frontend-design content; Phase 6 activates Design Authority Agent

## 13. Architecture Principles

- **Memory First**: Design Authority consults past design violations before issuing new findings
- **Provider First**: Design KB queryable via standard API; not hardcoded in agents
- **API First**: Design Knowledge Base API defined before Design Authority Agent built

## 14. Non Goals

- Design Authority does not redesign features
- Does not replace human design review for strategic design decisions
- Does not silently rewrite frontend-design skill

## 15. ROI Analysis

- **Value**: Automated design compliance enforcement catches design debt before it becomes technical debt
- **Consistency**: Every page evaluated against the same design rules every time
- **Long-Term**: Design Knowledge Base grows with each project; new rules discovered automatically

## 16. Success Metrics

- **Rule Coverage**: 100% of frontend-design SKILL.md principles mapped to formal rules in KB
- **VETO Accuracy**: > 95% agreement with human design expert on VETO decisions
- **Token Validation**: 100% of design tokens validated against KB on each run
- **Query Latency**: < 100ms per rule lookup

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Design rules too strict → excessive false vetoes | High | Medium | MUST/SHOULD/COULD classification; SHOULD rules advisory only | Design Architect |
| frontend-design content not fully formalized | Medium | High | Phased migration; human review of each rule formalization | Design Engineer |
| VLM findings misaligned with formal rules | Medium | Medium | VLM as input only; Design Authority makes final judgment | AI Engineer |

## 18. Technical Questions

- Should design rules use a custom YAML DSL or standard JSON Schema?
- How are MUST/SHOULD/COULD rules distinguished in the schema?
- Can projects override global design rules with project-specific rules?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Rule format: YAML DSL vs JSON Schema | Pending | YAML recommended for readability; decide in BP-VIR-013 |
| Rule priority inheritance | Pending | Global → Project → Feature override chain; decide in BP-VIR-013 |

## 20. ADR Detection

- **ADR Required**: Yes
- **Rationale & Focus**: ADR-VIR-010: Design Knowledge Base as external structured data vs embedded in agent code

## 21. Knowledge Update Impact

- **patterns**: Yes — Design Authority pattern; Structured Design Rule pattern
- **architecture**: Yes — Design Authority Agent + Design KB architecture
- **ADR**: Yes — ADR-VIR-010

## 22. Test Strategy Preview

- **Unit Tests**: Design KB query for each entity type; token validation; MUST vs SHOULD veto distinction
- **Integration Tests**: Vision Layer 4 finding → Design Authority → VETO → Consensus
- **Knowledge Base Tests**: All frontend-design principles mapped; no orphaned rules

## 23. Extension Impact

- **Extension UI Changes**: Design findings panel in Visualizer; rule reference links
- **Affected ViewModels**: Design compliance score; rule violation list

## 24. Complexity Estimation

- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 30% existing (frontend-design formalization) / 70% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 4 (Vision & Design Intelligence)
- **Prerequisites**: FEAT-058 (Vision Layer 4), FEAT-063 (Agent contract for Design Authority)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| What is Design Authority's role? | VIR agent with veto power over all design/UX decisions |
| Can it silently rewrite frontend-design? | No — proposes changes; human confirmation required |
| Source of design rules? | frontend-design SKILL.md formalized into structured Design KB |
| VLM role vs Design Authority? | VLM provides semantic analysis input; Design Authority makes formal judgment |

## 27. Requirement Readiness Score

- **Score**: 93/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): All 10 knowledge types queryable; all return structured data
- [ ] AC-02 (FR-07): Zero hardcoded design values in agent code (linter enforced)
- [ ] AC-03 (FR-13): Contrast ratio violation (MUST rule) triggers VETO; PASS blocked
- [ ] AC-04 (FR-14): Spacing SHOULD rule violation → DesignFinding advisory; no VETO; PASS not blocked
- [ ] AC-05 (FR-15): New pattern discovered → human confirmation requested before writing to KB

## 35. Final Planning Prompt

### Problem Statement
VIR needs a Design Knowledge Base (structured from frontend-design) and a Design Authority Agent with veto power over visual/UX quality. Design rules must be formal, versioned, and queryable.

### Architectural Details
- `.agents/visual-runtime/design-kb/` — YAML design rule storage
- `vir_runtime/agents/design/design_authority_agent.py` — Agent implementation
- `vir_runtime/agents/design/design_kb_client.py` — KB query interface
- `vir_runtime/domain/design_finding.py` — DesignFinding evidence subtype
- `config/design_rules/` — MUST/SHOULD/COULD rule files

### Verification Checklist
- [ ] docs/plans/FEAT-065_vir_design_authority_plan.md generated and approved
- [ ] docs/designs/FEAT-065_vir_design_authority_blueprint.md generated and approved
