<!-- File path: docs/designs/FEAT-062_vir_thinking_pipeline_and_cognitive_engines_blueprint.md -->

---
feature_id: FEAT-062
feature_name: Visual Intelligence Runtime — Thinking Pipeline & Cognitive Engines
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-062_vir_thinking_pipeline_and_cognitive_engines_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Thinking Pipeline & Cognitive Engines

## 0. Baseline Context & References
- **Memory Baseline**: Memory of state transition trees and confidence score calculations models.
- **RAG Query Summaries**: Cognitive pipeline relies on `AsyncEventBus` and `EvidenceEngine` modules from Phase 1 and 3 to post contradiction findings and manage symptom arrays.
- **Inspected Source Files**:
  - [FEAT-062 Plan](file:///e:/AgentsProject/docs/plans/FEAT-062_vir_thinking_pipeline_and_cognitive_engines_plan.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/cognitive/pipeline.py` | Create | Manage the 11-stage pipeline, stage transitions, and iteration bounds | None | High. Orchestrates VIR reasoning loops. |
| `vir_runtime/cognitive/contradiction.py` | Create | Listen for and evaluate contradictions across sensory domains | None | High. Finds inconsistencies. |
| `vir_runtime/cognitive/doubt.py` | Create | Assess confidence metrics and prompt re-observations | `pipeline.py` | Medium. Challenges single-source findings. |
| `vir_runtime/cognitive/rca.py` | Create | Map symptoms to root causes and categorize layout faults | None | High. Resolves root cause errors. |
| `vir_runtime/cognitive/safety_checker.py` | Create | Audit target file edit requests against approved blueprints | None | Medium. Enforces file edit scopes. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── cognitive/
    ├── contradiction.py
    ├── doubt.py
    ├── pipeline.py
    ├── rca.py
    └── safety_checker.py
```

---

## 3. Complete Class & Module Design

### 3.1 ThinkingPipeline
- **Class / Module Name**: `vir_runtime.cognitive.pipeline.ThinkingPipeline`
  - **Responsibilities**: Execute the 11 stages sequentially. Apply timeouts per stage, limit maximum rethink loops (max=3).
  - **Constructor Parameters**:
    - `session_id: str`
    - `bus: AsyncEventBus`
  - **Public Methods**:
    - `async def start_pipeline() -> str` - Runs loops, returning target status.
    - `async def transition_to_blocked(reason: str) -> None`
  - **Internal Methods**:
    - `async def _execute_stage(stage: str) -> None`
  - **Dependencies**: `vir_runtime.cognitive.doubt`, `vir_runtime.cognitive.rca`

### 3.2 ContradictionEngine
- **Class / Module Name**: `vir_runtime.cognitive.contradiction.ContradictionEngine`
  - **Responsibilities**: Track active sensory properties, analyze conflicts, and classify severity levels (`possible` or `confirmed`).
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `def check_contradictions(twin_state: Dict[str, Any]) -> List[ContradictionRecord]`

---

## 4. Detailed Interface Contracts

- **API Signature**: `async def start_pipeline() -> str`
  - **Parameters**: None.
  - **Return Types**: Returns a string status code (`PASS`, `FAIL`, or `BLOCKED`).
  - **Exceptions**:
    - `PipelineTimeoutError` - If total run duration exceeds limit thresholds.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
cognitive:
  pipeline:
    max_rethink_loops: 3
    stage_timeout_seconds: 30
    total_timeout_seconds: 300
  rca:
    required_evidence_count: 2
```

---

## 6. Database & Storage Design
- Contradiction records and RCA classification codes are recorded in the `vir_evidence` table (Phase 3).

---

## 7. Cache Architecture
- **Stage Timestamps Cache**:
  - Memory dictionary storing transition timestamps to calculate elapsed time per stage.

---

## 8. Error Model

- **Exception Class**: `PipelineTimeoutError`
  - **Trigger Condition**: Stage execution time exceeds 30 seconds.
  - **Recovery Strategy**: Transition session to `BLOCKED`, export intermediate report, shut down page instances.
  - **Logging Requirements**: ERROR log outlining target active stage name.

---

## 9. Skill Integration Contracts
- None.

---

## 10. CLI & Runtime Contracts
- None.

---

## 11. Sequence Flows

- **Self-Doubt & Rethink Flow**:
  1. `ThinkingPipeline` executes `Test` stage.
  2. Single evidence source returns verdict.
  3. `SelfDoubtEngine` inspects evidence count.
  4. Count is < 2.
  5. Doubt engine decreases confidence, triggering re-observation loop.
  6. Pipeline returns to `Observe` stage (rethink loops counter incremented).

---

## 12. Security & Safety
- **Blueprint edit boundary gate**: `SafetyScopeChecker` compares absolute target path strings to blueprint write authorizations, blocking unauthorized file edits during RCA repairs.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-03` | Unit Test | `tests/unit/test_rethink_limits.py` | `pipeline.py` | `self.assertEqual(loop_count, 3)` |
| `FR-18` | Unit Test | `tests/unit/test_rca_evidence_rules.py` | `rca.py` | `self.assertFalse(is_confirmed)` |

---

## 14. Requirement Traceability Matrix
- `FR-03` -> Task 1.3 -> Class `ThinkingPipeline` -> `pipeline.py` -> `test_rethink_limits.py` -> Verified.
- `FR-18` -> Task 1.16 -> Class `RCAEngine` -> `rca.py` -> `test_rca_evidence_rules.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/cognitive/safety_checker.py`
  - **Purpose**: Workspace write bounds auditor.
  - **Owner**: Verifier
  - **Inputs / Outputs / Dependencies**: Depends on blueprint file maps.
