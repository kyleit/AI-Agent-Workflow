<!-- File path: docs/designs/vir_ecosystem_integration_plan.md -->

# Visual Intelligence Runtime (VIR) — AIWF Ecosystem Integration Plan

This document details the integration matrices, trigger guidelines, input/output contracts, and validation check points required to connect VIR across the entire AI Skill Framework (AIWF).

---

## 1. VIR Integration Matrix (Subsystems Routing)

| Caller | Trigger Condition | VIR Skill Called | Input Contract | Input Schema | Output Contract | Output Schema | Blocking Conditions | Next Skill |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `implementation-to-debug` | Frontend modifications | `frontend-visual-debug` | `RuntimeRequest` | `config_schema` | `RuntimeResult` | `observation_schema` | Visual regression errors | `vir-investigate` |
| `frontend-visual-debug` | Initiate loop | `vir-investigate` | `Observation` | `observation_schema` | `Investigation` | `evidence_schema` | Active veto blocks | `vir-runtime` |
| `vir-investigate` | Observations needed | `vir-runtime` | `RuntimeRequest` | `config_schema` | `RuntimeResult` | `observation_schema` | Port probe timeouts | `vir-verify` |
| `vir-verify` | Auditing complete | `vir-memory-update` | `DigitalTwin` | `evidence_schema` | `GoalPlan` | `evidence_schema` | Write errors | `implementation-to-release` |

---

## 2. Trigger & Skip Policies

### Mandatory Triggers
VIR invocation is mandatory when:
- Active branch modifies elements styling or spacing design tokens.
- Navigation routes, interactive form elements, or dialog flows are modified.
- Axe-core accessibility/WCAG validation thresholds are required.
- Visual regressions testing is explicitly required by active blueprints.

### Skip Guidelines
VIR may be skipped only if:
- Target stack is classified as backend-only during `project-discovery`.
- No user-visible components are impacted.
- Skip reason is recorded inside `workflow_runtime` state database.

---

## 3. Skill Invocation Chain

```text
implementation-to-debug
        ↓
frontend-visual-debug (Entrypoint Orchestrator)
        ↓
frontend-design (Design Authority guidelines)
        ↓
vir-investigate (Root cause analysis & Self-doubt)
        ↓
vir-runtime (Deterministic Playwright/pixel runs)
        ↓
vir-verify (Weighted consensus gates)
        ↓
vir-memory-update ( baseline/experience indexers)
        ↓
implementation-to-release (Release readiness)
```

---

## 4. Input & Output Contracts Specifications

- **frontend-visual-debug**:
  - *Inputs*: `work_item_id`, `approved_blueprint`, `timeout_budget`.
  - *Outputs*: `debug_session_id`, `status` (PASS/FAIL).
- **vir-investigate**:
  - *Inputs*: `evidence_list`, `digital_twin_snapshot`.
  - *Outputs*: `root_cause_verdict`, `confidence_score`.
- **vir-runtime**:
  - *Inputs*: `runtime_request`, `viewport_matrix`.
  - *Outputs*: `runtime_result` (evidence arrays, screenshot buffers).
- **vir-verify**:
  - *Inputs*: `verification_request`, `consensus_scores`.
  - *Outputs*: `decision` (PASS/FAIL), `quality_gate_result`.
- **vir-memory-update**:
  - *Inputs*: `verified_result`, `regression_baseline`.
  - *Outputs*: `memory_update_result`.
