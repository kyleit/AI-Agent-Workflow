---
feature_id: FEAT-090
feature_name: Validation Runtime Engine
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-090_validation_runtime_engine_plan.md
---

# Master Brainstorming Document – Validation Runtime Engine (FEAT-090)

## 1. Executive Summary
This document designs the **Validation Runtime Engine**, which acts as the quality gatekeeper for the AIWF OS. It evaluates task outputs against predefined Acceptance Criteria (AC), compiles evidence, manages Debug and Verification Gates, and classifies execution failures to guide retry or recovery strategies.

## 2. Background
Currently, validation is handled in a fragmented manner across skills like `debug-to-verify` and `implementation-to-debug`, using standard terminal testing commands. This procedural verification fails to evaluate semantic success criteria or programmatically classify reasons for test failures (e.g. environment issues vs. logic bugs). Evolving this requires a centralized engine to compile evidence and enforce strict verification gates.

## 3. Current Architecture Analysis
The current codebase has `validation_runner.py` and `validator.py` under `skills/workflow-runtime/scripts`.
- It executes basic validation command lists.
- It scans the repository for lint and build errors.

## 4. Current Limitations
- **No AC Mapping**: Test scripts run globally without mapping results back to specific Acceptance Criteria.
- **Ambiguous Failures**: Cannot distinguish compile errors, lint failures, and runtime test failures programmatically.
- **No Evidence Bundle**: Verification records are scattered instead of unified into a single audit trail.

## 5. Objectives
- Implement an **Acceptance Criteria (AC) Mapper** that checks nodes against test requirements.
- Develop **Verification Gates** to prevent code promotion on failures.
- Provide a **Failure Classifier** that labels errors to guide recovery paths.

## 6. Functional Requirements
- **FR-01: AC Mapping and Checking**: Programmatically map tests to specific functional or non-functional AC.
- **FR-02: Evidence Bundler**: Compile code logs, test outputs, and system metrics into a signed verification record.
- **FR-03: Debug and Verification Gates**: Block workflow transitions if lint, build, or test suites fail.
- **FR-04: Failure Classification**: Analyze stderr outputs to label errors (e.g., `syntax_error`, `runtime_mismatch`, `environment_stale`).
- **FR-05: Objective Verification**: Confirm that the overall objective is solved before finalizing the loop.

## 7. Non-Functional Requirements
- **NFR-01: Evaluation Overhead**: Running validation checks (excluding test suite runtime) must take `< 50ms`.
- **NFR-02: Strict Quality Enforcement**: Promotion block must be absolute unless overridden by manual user authorization.

## 8. Scope
- Validation engine core (`validation_engine.py`).
- Failure Classifier algorithm.
- Evidence metadata schema.
- Verification gate CLI command logic.

## 9. Out of Scope
- Actually executing the test scripts (delegated to standard system shell tools).
- Virtual simulator runtime (delegated to VIR Platform).

## 10. Runtime Responsibilities
The Validation Runtime compiles test commands, runs the test processes, collects outputs, parses results, updates the AC compliance checklist, and issues green/red promoting decisions.

## 11. Components
- `ValidationEngine`: Executes verification steps and verifies preconditions.
- `EvidenceBundler`: Aggregates and formats the test run context.
- `FailureClassifier`: Matches error logs to known regex rules.
- `QualityGateController`: Enforces strict promote/halt boundaries.

## 12. Data Model
```json
{
  "verification_id": "VAL-889",
  "target_goal": "OBJ-001",
  "acceptance_criteria": [
    {"id": "AC-01", "description": "Lấy thông tin tag", "status": "passed"}
  ],
  "evidence": {
    "stdout": "test output logs...",
    "exit_code": 0
  },
  "verdict": "passed"
}
```

## 13. Runtime State
```
[Unverified] ──(run verification)──> [Evaluating] ──(pass)──> [Verified]
                                            │
                                         (fail)
                                            ▼
                                     [ValidationFailed] ──> [Classifying]
```

## 14. Event Flow
1. Task execution completes.
2. Executive loop invokes the Validation Runtime.
3. ValidationEngine compiles and runs verification scripts.
4. Output is piped to EvidenceBundler.
5. If tests fail, FailureClassifier identifies the root cause category.
6. Validation verdict is returned as `failed` with classification labels.

## 15. Sequence Flow
- Run validation suite -> Parse output -> Evaluate AC match -> Compile evidence metadata -> Determine promote/block verdict.

## 16. Dependencies
- State manager (from FEAT-051) and Task Graph Engine (FEAT-087).

## 17. Integration Points
- CLI: `python workflow_runtime.py test validate`
- State: `.agents/state/approvals.json`

## 18. Interaction with Executive Runtime
- The Executive loop uses the Validation Engine to evaluate the current goal status before completing iteration cycles.

## 19. Interaction with other features
- Provides feedback to **Task Graph Engine (FEAT-087)** to determine if re-planning or retrying is required.

## 20. Security Considerations
- Execute validation test scripts under limited sandbox privileges.
- Sandbox environment isolation during verification tests.

## 21. Performance Considerations
- Run test suites incrementally, checking only modules modified in the current session.

## 22. Scalability Considerations
- Design supports registering custom validator plugins for different programming languages.

## 23. Failure Scenarios
- **Test Script Times Out**: Terminate execution, classify as `timeout_failure`, and return block verdict.
- **Evidence Serialization Fails**: Log warning, export raw text, and preserve block state.

## 24. Recovery Strategy
On validation failure, restore the target environment to the last clean checkpoint state and notify the developer agent to fix the identified bugs.

## 25. Migration Strategy
Map existing verification steps (e.g. from `pytest.ini` or Makefile) into validation node definitions in the new runtime.

## 26. Backward Compatibility
Support raw exit-code based verification checks for legacy scripts.

## 27. Risks
- Flaky tests causing false validation failures. Mitigated by allowing optional re-runs for flaky classifications.

## 28. Alternative Designs
- **Option A**: Manual-only verification. (Rejected: prone to error, slows down execution loops).
- **Option B**: Remote CI-driven validation. (Rejected: offline-first policy compliance).

## 29. Trade-offs
- Incremental verification is fast but might miss global system regressions. This is mitigated by enforcing full validation runs before release.

## 30. Acceptance Criteria
- [ ] AC-01: Successfully block task promotion when a test suite fails.
- [ ] AC-02: Correctly classify compile errors and test failures.

## 31. Estimated Complexity
- Medium.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-090_validation_runtime_engine.md`).

## 33. Recommended Implementation Order
Implement fifth, following the Observability system.
