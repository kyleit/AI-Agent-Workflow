<!-- docs/brainstorming/FEAT-066_vir_quality_gates_and_reporting_system.md -->

---
feature_id: FEAT-066
feature_name: Visual Intelligence Runtime — Quality Gates & Reporting System
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-065_vir_design_authority_and_design_knowledge_base.md
next_artifact: ../plans/FEAT-066_vir_quality_gates_reporting_plan.md
---

# Master Requirement Document – VIR Quality Gates & Reporting System

## 1. Feature ID & Name
- **Feature ID**: FEAT-066
- **Feature Name**: Visual Intelligence Runtime — Quality Gates & Reporting System

## 2. Original Idea
Design and implement VIR's Quality Gate system — the final decision layer that evaluates Consensus Engine verdicts against configurable thresholds — and the Reporting System that produces human-readable and machine-readable investigation reports.

## 3. Business Problem
- **Problem**: Without a formal Quality Gate, VIR cannot enforce pass/fail criteria in CI/CD pipelines or communicate findings clearly to human engineers. Reports that lack structure, root cause references, and evidence chains are useless for debugging.
- **Why it matters**: Quality Gates are how VIR integrates with the SDLC — blocking bad code before release. Reporting is how VIR communicates its intelligence to humans. Both are essential for VIR to have real-world impact.
- **Who is affected**: CI/CD pipeline, Release Manager Agent, frontend developers, Visualizer extension, SDLC Integration layer.
- **Expected outcome**: Configurable quality gates that enforce verdicts in CI/CD and a reporting system producing rich, structured, evidence-backed reports in multiple formats.

## 4. Requirement Discovery

### Functional Requirements

#### Quality Gate
- FR-01: Quality Gate evaluates the ConsensusRecord from Consensus Engine to produce a final Gate Result: PASS, PARTIAL, FAIL, BLOCKED.
- FR-02: Gate thresholds configurable per project and per gate type: visual_regression_threshold, accessibility_compliance_threshold, design_compliance_threshold, performance_threshold, confidence_minimum.
- FR-03: PASS condition: all critical domains pass + no active veto + no unresolved critical contradiction + confidence ≥ minimum + no security finding.
- FR-04: PARTIAL condition: non-critical issues only; critical domains pass; SHOULD-rule violations only.
- FR-05: FAIL condition: any of — critical contradiction unresolved, evidence-backed veto active, accessibility MUST rule violated, security finding present, visual regression CRITICAL_REGRESSION classification.
- FR-06: BLOCKED condition: Thinking Pipeline reached iteration limit without resolution; investigation inconclusive.
- FR-07: Quality Gate must produce machine-readable gate result for CI/CD: exit code 0 (PASS/PARTIAL), 1 (FAIL), 2 (BLOCKED).
- FR-08: Quality Gate must log all gate evaluation steps for audit trail.
- FR-09: Quality Gate must support gate override with human confirmation and override reason logged.

#### Reporting System
- FR-10: Report must be generated in at least two formats: Markdown (human-readable) and JSON (machine-readable).
- FR-11: Report must contain: investigation_id, feature_id, gate_result, confidence, execution_profile, execution_duration, timestamp, git_commit, browser, viewport, evidence_summary, contradiction_list, root_causes, design_findings, accessibility_findings, performance_findings, regression_status, fixes_applied, remaining_issues, recommendations, learning_outcomes.
- FR-12: Report must reference all evidence by ID with links to stored artifacts (screenshots, HAR files, traces).
- FR-13: Report path: `docs/verification/FEAT-XXX_vir_report.md` and `.agents/visual-runtime/reports/FEAT-XXX_TIMESTAMP.json`.
- FR-14: Report generation must be non-blocking (async); does not delay Quality Gate result.
- FR-15: Reports must include executive summary (2–3 sentences) suitable for dashboard display.
- FR-16: Report must include investigation timeline: key events with timestamps in chronological order.
- FR-17: Report must include confidence breakdown by domain (visual: 0.92, network: 1.0, design: 0.78, etc.).
- FR-18: Performance Telemetry in Reports: Include system resource footprints (peak CPU, peak RAM), network latencies, database run statistics, and execution timing metrics in reports.
- FR-19: Visual Timeline Diagrams: Render HTML/SVG timeline charts inside Markdown reports mapping out jank, layout shift timestamps, and critical visual errors chronologically.
- FR-20: CI Artifact Packaging: Compile the JSON/MD reports, captured screenshots, HTML pages, HAR logs, and browser tracing buffers into a standard zip archive suitable for CI pipeline artifacts storage.

### Non-functional Requirements
- NFR-01: Report generation < 3 seconds per investigation (excludes artifact upload).
- NFR-02: Quality Gate evaluation < 500ms.
- NFR-03: JSON report must be valid against published JSON Schema.
- NFR-04: Reports must be readable without network connection (all artifact paths relative to `.agents/visual-runtime/`).
- NFR-05: Report storage: retain 90 days by default (configurable).

### Technical Constraints
- TC-01: Quality Gate is the last step before Orchestrator ends session.
- TC-02: Report generation uses templates stored in `.agents/visual-runtime/templates/`.
- TC-03: Machine-readable report JSON Schema published alongside VIR.
- TC-04: Report path follows existing AIWF convention: `docs/verification/FEAT-XXX_*.md`.
- TC-05: Exit codes: 0=PASS, 1=FAIL, 2=BLOCKED, 3=PARTIAL (configurable override).

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Gate evaluates ConsensusRecord | BP-VIR-015 | Inject PASS/FAIL/BLOCKED ConsensusRecord | Correct gate result for each case |
| FR-03 | Must | PASS conditions | BP-VIR-015 | All conditions met | Gate returns PASS |
| FR-05 | Must | FAIL conditions | BP-VIR-015 | Active evidence-backed veto | Gate returns FAIL |
| FR-07 | Must | Machine-readable exit code | BP-VIR-015 | CI run with known FAIL scenario | Exit code 1 returned |
| FR-09 | Must | Override with confirmation | BP-VIR-015 | Human overrides FAIL gate | Override logged with reason |
| FR-10 | Must | Two report formats | BP-VIR-015 | Generate report for sample investigation | MD and JSON files created |
| FR-11 | Must | Report completeness | BP-VIR-015 | JSON report validated against schema | All required fields present |
| FR-12 | Must | Evidence references | BP-VIR-015 | Report links to screenshot | Screenshot path valid |
| FR-16 | Should | Investigation timeline | BP-VIR-015 | Timeline has ≥5 key events | Events in chronological order |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| CI/CD Pipeline | Primary | Critical | Critical | Machine-readable gate result + exit code |
| Release Manager Agent | Primary | High | High | Gate result for release decision |
| Frontend Developers | Primary | High | High | Detailed root cause reports |
| Visualizer Extension | Secondary | High | High | Report data for dashboard display |
| Quality Reviewers | Primary | Medium | Medium | Evidence-backed audit trail |

## 7. Scope Boundary

### In Scope
- Quality Gate evaluation logic and thresholds
- Gate result types (PASS/PARTIAL/FAIL/BLOCKED)
- Machine-readable exit codes for CI
- Override mechanism
- Markdown and JSON report generation
- Report schema
- Report path conventions

### Out of Scope
- CI/CD pipeline configuration (FEAT-068)
- IDE extension visualization (FEAT-068)
- Memory storage of reports (FEAT-064)

### Deferred Scope
- HTML report format
- Report email/Slack notification
- Report diff between runs

### Future Scope
- Interactive web-based report viewer
- Report trend analytics dashboard

## 8. Dependency Graph Preview

- FEAT-066: Quality Gates & Reporting (Must)
  - FEAT-063: Consensus Engine (input: ConsensusRecord)
  - FEAT-061: Evidence Domain (report references evidence)
  - FEAT-062: Thinking Pipeline (investigation conclusions in report)
  - FEAT-065: Design Authority (design findings in report)

## 9. Data Flow Preview

- Consensus Engine publishes ConsensusRecord
  └── Quality Gate receives → evaluates against thresholds
      └── No active veto + confidence 0.94 ≥ 0.85 threshold + no FAIL conditions
          └── Gate Result = PASS; exit code = 0
              └── Report Generator activated (async)
                  └── Collects: investigation, evidence list, findings, timeline
                      └── Renders MD template → `docs/verification/FEAT-055_vir_report.md`
                      └── Serializes JSON → `.agents/visual-runtime/reports/FEAT-055_20260712.json`
                          └── Reports complete; Orchestrator ends session

## 10. Existing Asset Analysis

| Asset | Location | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| frontend-visual-debug output template | SKILL.md line 158-206 | Extend | Existing report template extended with VIR structure |
| docs/verification/ | project root | Reuse | Existing verification directory for reports |

## 11. Dependency & Blast Radius Analysis

- **Impact Level**: High — Quality Gate is the final enforcement layer

## 12. Migration Strategy

- **Backward Compatibility**: Report format extends existing `docs/verification/FEAT-XXX_*.md` convention
- **Migration Phases**: Phase 6 implements Quality Gate + basic report; Phase 8 adds full evidence-linked report

## 13. Architecture Principles

- **API First**: Report JSON Schema published before report generator implemented
- **Script First**: Quality Gate and reporter exposed as CLI commands
- **Backward Compatibility**: Report path convention matches existing AIWF verification pattern

## 14. Non Goals

- Quality Gate does not perform investigation (Cognitive Engines do)
- Does not send notifications (CI/CD layer does)
- Does not execute fixes (Coder Agent does)

## 15. ROI Analysis

- **Value**: Automated gate enforcement replaces manual review per PR
- **CI/CD Integration**: VIR blocks merges with bad UI automatically
- **Reporting Value**: Evidence-backed reports reduce debugging time from hours to minutes

## 16. Success Metrics

- **Gate Evaluation Speed**: < 500ms
- **Report Generation Speed**: < 3 seconds
- **Report Completeness**: 100% of required fields in JSON schema
- **Exit Code Accuracy**: 100% — exit code matches gate result on all test scenarios

## 17. Risk Matrix

| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Gate thresholds misconfigured cause all FAIL or all PASS | High | Medium | Default thresholds validated on test suite; threshold linting | QA Engineer |
| Report template rendering fails on edge-case evidence | Medium | Low | Template tests on edge cases; fallback to minimal report | Backend Engineer |
| JSON Schema too strict breaks backward compatibility | Medium | Low | Schema versioning; additive-only changes | Architect |

## 18. Technical Questions

- Should PARTIAL verdict in CI/CD produce exit code 0 or a separate code?
- What is the maximum report size before truncation is needed?
- Should the JSON report include full evidence payloads or only IDs?

## 19. Open Decision Register

| Topic | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| PARTIAL exit code | Pending | Exit code 3 for PARTIAL; configurable override; decide in BP-VIR-015 |
| Report evidence inclusion | Pending | IDs + summary in report; full payload queryable from SQLite |
| Max report size | Pending | 5MB default; configurable; decide in BP-VIR-015 |

## 20. ADR Detection

- **ADR Required**: No — report format follows existing AIWF conventions

## 21. Knowledge Update Impact

- **patterns**: Yes — Quality Gate pattern; Evidence-backed Report pattern
- **architecture**: Yes — Quality Gate + Reporting architecture

## 22. Test Strategy Preview

- **Unit Tests**: Gate evaluation for each verdict type; threshold boundary testing; report schema validation
- **Integration Tests**: Full pipeline → Consensus → Gate → Report on known test scenarios
- **CI Tests**: Exit code validation on PASS/FAIL/BLOCKED scenarios
- **Report Tests**: All required fields present; evidence IDs resolve to valid artifacts

## 23. Extension Impact

- **Extension UI Changes**: Quality gate status in Visualizer dashboard; report viewer panel (Phase 8)
- **Affected ViewModels**: Gate result badge; confidence breakdown chart; finding summary list

## 24. Complexity Estimation

- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 15% existing (extend verification report template) / 85% new

## 25. Roadmap Alignment

- **Roadmap Phase**: VIR Phase 6 (Multi-Agent + Consensus → Gate + Report)
- **Prerequisites**: FEAT-063 (Consensus Engine), FEAT-061 (Evidence Domain)

## 26. Clarification Questions & Answers

| Question | Answer |
|---|---|
| Machine-readable CI output? | Yes — exit codes + JSON report |
| Report format? | Markdown + JSON minimum |
| Evidence references in report? | Yes — evidence IDs linked to artifacts |
| Gate override? | Yes — with human confirmation and logged reason |

## 27. Requirement Readiness Score

- **Score**: 95/100
- **Status**: Ready ≥ 85

## 34. Acceptance Criteria

- [ ] AC-01 (FR-01): PASS/FAIL/BLOCKED ConsensusRecord → correct gate result for each
- [ ] AC-02 (FR-07): Known FAIL scenario → exit code 1 returned in CI run
- [ ] AC-03 (FR-09): Gate override with confirmation → override reason logged in SQLite
- [ ] AC-04 (FR-10): Markdown and JSON reports generated for sample investigation
- [ ] AC-05 (FR-11): JSON report validates against published JSON Schema without errors

## 35. Final Planning Prompt

### Problem Statement
VIR needs a Quality Gate evaluating Consensus verdicts against configurable thresholds, producing machine-readable exit codes, and a Reporting System generating Markdown + JSON evidence-backed reports.

### Architectural Details
- `vir_runtime/gates/quality_gate.py` — Gate evaluation + override
- `vir_runtime/gates/thresholds.py` — Threshold configuration
- `vir_runtime/reporters/markdown_reporter.py` — MD report generation
- `vir_runtime/reporters/json_reporter.py` — JSON report generation
- `vir_runtime/reporters/schema/report_schema.json` — JSON Schema
- `.agents/visual-runtime/templates/report.md.j2` — Jinja2 template

### Verification Checklist
- [ ] docs/plans/FEAT-066_vir_quality_gates_reporting_plan.md generated and approved
- [ ] docs/designs/FEAT-066_vir_quality_gates_reporting_blueprint.md generated and approved
