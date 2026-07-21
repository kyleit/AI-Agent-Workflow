---
name: quick-feature
command: feature
aliases:
  - scaffold
category: utility
tags:
  - utility
  - feature
  - quick
  - minor
version: 3.3.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-09
description: Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick features, upgraded with v3.2 Mini Spec quality standards and rich planning sections.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: cached---

# Skill: quick-feature (Three-Phase Workflow with Blueprint-Driven Execution)

## Purpose

Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick features, upgraded with v3.2 Mini Spec quality standards and rich planning sections.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "quick-feature" --command "feature" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "project-memory-update" --next-command "memory-sync"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, you must immediately output this table to establish the behavioral anchor:**

| 🔒 QUICK-FEATURE MODE ACTIVE |
| :--- |
| This Skill runs in a **three-phase model** with strict Blueprint enforcement. |
| **Phase 1 (Specification)**: Analyze and write the QUICK feature specification. |
| **Phase 2 (Blueprint)**: Design the technical solution and write the Design Blueprint. |
| **Phase 3 (Implementation)**: Implement code only after explicit Blueprint approval. |
| NO SOURCE CODE will be modified during Phase 1 or Phase 2. |
| Specification path: `docs/quick/QUICK-XXX_feature_name.md` |
| Design Blueprint path: `docs/blueprints/QUICK-XXX_feature_name_blueprint.md` |

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Blueprint Mandatory Execution Policy** (Section 13) - Never implement without approved Blueprint.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

---

## Capability Boundary & Guardrails

- **No Premature Implementation**: No source code may be created, deleted, or modified before a Technical Design Blueprint is generated under `docs/blueprints/` and explicitly approved by the user.
- **Validation of Blueprint**: Before code generation, verify that the Blueprint exists, has status `approved` in the session or was explicitly approved by the user in the prompt logs.
- **No Refactoring**: Implement ONLY the minimal changes described in the approved Blueprint. Do NOT introduce unrelated cleanups, structural refactoring, or database redesigns.
- **No Downstream Auto-Execution**: Do NOT execute Git commands (commit, push) automatically. Release must only occur if explicitly requested by the user.
- **Frontend Design Binding**: If the feature touches UI/UX, frontend components, layout, spacing, typography, color, animation, icons, visual hierarchy, aesthetic styling, or design-system decisions, the Agent MUST use `frontend-design` before finalizing the Specification, Blueprint, or implementation decisions.

---

## Quick-Feature Eligibility Rules

Every feature request must first be evaluated against the following criteria:

| Category | Quick-Feature Eligible (All Must Pass) | Standard Workflow Required (Any Trigger) |
|---|---|---|
| **Scope** | Single module or UI component (e.g. adding one API endpoint, one button, one dialog, one filter, one validation, one search field, one export function). | Multiple independent modules, cross-cutting concerns, database redesign. |
| **Architecture Impact** | Low (additive or purely local change, fits current design). | Medium/High (changes shared interfaces, authentication, storage/caching strategy). |
| **ADR Requirement** | No ADR required. | ADR required (decisions with long-term architectural trade-offs). |
| **Estimated Work** | Less than one working day (Low complexity). | More than one working day (High complexity, uncertain paths). |

---

## Feature ID Allocation Rule

QUICK Feature IDs are determined **ONLY** by scanning `docs/quick/`:
1. Scan `docs/quick/` for files matching `QUICK-XXX_*.md` (where `XXX` is a 3-digit number).
2. Ignore plans, designs, and other files.
3. If directory is empty (or has only `.gitkeep`): start at `QUICK-001`.
4. If files exist: next ID = highest existing ID + 1.

---

## Workflow Sequence

Execute these steps strictly. Do not stop for user approval until the Blueprint has passed internal review.

```
Step 1:  Receive User Feature Request
         ↓
Step 2:  Feature Classification & Eligibility Check
         - Produce the Decision Matrix.
         - [STOP] If classified as Standard → Reject and recommend standard workflow.
         ↓
Step 3:  Consult Project Memory & RAG (No whole-workspace scanning)
         ↓
Step 4:  Targeted Source Inspection
         ↓
Step 5:  Generate Feature Specification (docs/quick/QUICK-XXX_feature_name.md)
         ↓
Step 6:  Internal Spec Review Gate (No User Stop)
          - Review the Specification against this skill, AI_RULES.md, the user request, and frontend-design when UI/design is affected.
          - If review FAILS, explain the failed points and revise the Specification only in those points.
          - Repeat review/revision until PASS.
          - Do NOT ask the user for approval at this gate.
         ↓
Step 7:  Generate Technical Design Blueprint (docs/blueprints/QUICK-XXX_feature_name_blueprint.md)
         ↓
Step 8:  Internal Blueprint Review + Final User Approval Gate
          - Run python CLI to register blueprint.
          - Review the Blueprint against this skill, AI_RULES.md, the Specification, document-compliance-assessment rules, and frontend-design when UI/design is affected.
          - If review FAILS, clearly state each failed point and revise only those points. Repeat until PASS.
          - After review PASS, present the Technical Design Blueprint to the user in chat.
          - **ABSOLUTE USER APPROVAL STOP**: The AGENT MUST STOP CALLING TOOLS IMMEDIATELY AND END TURN.
          - [STOP] Wait for explicit user approval. DO NOT run any more tools. DO NOT mark approved. DO NOT inspect further. DO NOT implement.
          - Once approved, run python CLI to mark blueprint approved.
         ↓
Step 9:  Pre-Implementation Git Check (Phase 3)
          - Read current branch and git status.
          - If branch policy requires a user decision, stop and ask only that branch question.
         ↓
Step 10: Code Implementation (Direct minimal code changes)
         ↓
Step 11: Automatic Validation Pipeline
         - Run compiler, check builds, run existing unit tests.
         - [STOP] If tests fail → Report failures and halt.
         ↓
Step 12: Generate Quick Feature Summary Report & Self-Validation Checklist
```

---

## Detailed Step Instructions

### Step 5: Generate Feature Specification

Calculate the Feature ID and write the document at:
`docs/quick/QUICK-XXX_feature_name.md`

Use this template:

```markdown
<!-- File path: docs/quick/QUICK-XXX_feature_name.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-XXX
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – [Feature Name]

## 1. Feature Goal
[Detailed description of the feature goal]

## 2. Quick Feature Justification
Giải thích lý do tác vụ đủ điều kiện phát triển nhanh thay vì chu trình SDLC đầy đủ:
- **Estimated Complexity**: [Low / Medium]
- **Implementation Scope**: [Single module or local change]
- **Architectural Impact**: [Low / Purely additive]
- **Risk Level**: [Low / Medium]
- **Justification**: [Explain why this qualifies]

## 3. Scope Boundary
Phân định ranh giới phạm vi rõ ràng để tránh mơ hồ:
- **In Scope**:
  - [...]
- **Out of Scope**:
  - [...]
- **Not Modified**:
  - [...]
- **Future Work**:
  - [...]

## 4. Trigger / Execution Flow
- **Entry Point**: [Where execution starts, e.g., runtime CLI command or hook]
- **Trigger Source**: [E.g., User explicit CLI call, Git hook, runtime lifecycle event]
- **Execution Order**: [Logical order of invocation]
- **Completion Condition**: [What marks execution completion]

## 5. Runtime Sequence
[Sequence diagram or runtime ordering steps of the logic flow]
Example:
Memory Update
↓
Indexes
↓
SQLite
↓
Vector Sync
↓
External Sync
↓
Complete

## 6. Dependency Contract
- **Required Dependencies**: [Libraries, modules, or services required]
- **Optional Dependencies**: [Optional configurations or third-party integrations]
- **External Runtime**: [External APIs, executables, or services]
- **Expected Contracts**: [API response schemas, command output formats, or DB schemas]
- **Detection Method**: [How availability is checked at runtime]
- **Failure Behavior**: [Action taken when dependencies are unavailable]

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Dependency Missing | Skip operation with warn log | Log outputted to terminal | Proceed without optional step |
| Timeout | Raise error / fallback | Show retry message | Auto-retry or abort after timeout |
| Configuration Disabled | Skip operation silently | No output / Info log | Proceed |
| Invalid State | Abort execution | Direct error warning | Exit with code 1 |
| Partial Failure | Continue other steps | Highlight failed step | Log error to sync map |
| Retry Exhausted | Halt execution | Exit code with traceback | Log critical failure |

## 8. Non-functional Requirements
- **Performance Expectations**: [Execution speed, memory threshold]
- **Blocking vs Asynchronous**: [Whether operation blocks CLI execution or runs in background]
- **Timeouts**: [Maximum execution duration before timeout]
- **Retry Policy**: [Number of retries and backoff delays]
- **Resource Usage**: [CPU/Memory bounds, temporary disk storage]
- **Thread Safety**: [Concurrency constraints, file locks]
- **Idempotency**: [Idempotent behavior: executing multiple times yields identical state]
- **User Interaction**: [Sandbox prompts, choice protocols, or no-interaction modes]

## 9. Logging Requirements
- **Start**: [Log output at start, e.g., INFO log]
- **Progress**: [Step status messages]
- **Warning**: [Log on non-critical errors or fallbacks]
- **Skipped**: [Log when configuration/feature is disabled]
- **Success**: [Success confirmation messages]
- **Failure**: [Error log with traceback/reason]
- **Completion**: [End of phase execution summary log]

## 10. Configuration Impact
- **Existing Configs Reused**: [Properties reused from memory.config.json or session]
- **New Configs Required**: [New properties introduced]
- **Migration Required**: [Whether configuration format needs to be upgraded]
- **Default Behavior**: [Default values when properties are missing]
- **Backward Compatibility**: [Compatibility with older config formats]

## 11. Design Constraints
- **CLI/API Constraints**: No new CLI commands, no API modifications unless approved.
- **Database Constraints**: No database schema changes, no data restructuring.
- **Architectural Constraints**: Reuse existing runtime package, no duplicate logic, no architectural redesign.

## 12. Blast Radius
Xác định các thành phần bị ảnh hưởng và đánh giá mức độ tác động:
- **Affected Skills**: [None / List affected skills]
- **Affected Runtime**: [None / List affected areas]
- **Affected Extension**: [None / List affected areas]
- **Affected Memory**: [None / List affected areas]
- **Affected Documentation**: [None / List affected areas]
- **Affected Scripts**: [None / List affected areas]
- **Impact Level**: [Low | Medium | High]

## 13. File Change Scope
Biên giới tác động mã nguồn thực tế:
- **Modify**:
  - `relative/path/to/file`
- **Create**:
  - `relative/path/to/file`
- **Optional**:
  - [...]
- **Do Not Modify**:
  - [...]

## 14. Success Metrics
Các chỉ số đo lường hiệu quả thành công:
- **Regression free**: [Yes / No]
- **Backward compatible**: [Yes / No]
- **Token reduction**: [... %] (if applicable)
- **Latency improvement**: [... ms] (if applicable)
- **Implementation completeness**: [... %]

## 15. Rollback Strategy
- **Files Affected**: [List files modified or created]
- **Safe Rollback Steps**: [Manual/Automated rollback steps, e.g., git checkout / git clean]
- **Migration Rollback**: [How to revert database/config migration if any]
- **Behavior After Rollback**: [System health checks to verify state after rollback]

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Success Path): [Criteria for correct behavior in normal conditions]
- [ ] AC-02 (Failure Path): [Criteria for correct behavior under error conditions]
- [ ] AC-03 (Skipped Path): [Criteria for correct behavior when feature is disabled]
- [ ] AC-04 (Backward Compatibility): [Criteria validating older workflows continue working]
- [ ] AC-05 (Regression): [No unexpected changes inside external dependencies/modules]
- [ ] AC-06 (No duplicate execution): [Idempotency checks: executing twice doesn't duplicate actions]
- [ ] AC-07 (No behavior change outside scope): [No regression in core runtime actions]

## 17. Self Verification
Xác minh tự động bắt buộc sau triển khai:
- [ ] So sánh Trước vs Sau (Before vs After comparison).
- [ ] Kiểm thử không hồi quy (Regression testing).
- [ ] Xác thực tương thích hạ nguồn (Downstream workflow validation).
- [ ] Xác minh tương thích ngược (Compatibility verification).

## 18. Open Questions
[List any open questions or design decisions to resolve with the user]

## 19. Blueprint Handoff
Bản thiết kế kỹ thuật (Technical Design Blueprint) ở Phase 2 bắt buộc phải quyết định và làm rõ:
- Điểm tích hợp mã nguồn (Integration point)
- Trách nhiệm của các lớp và module (Class/Module responsibilities)
- Giao diện và cơ chế tiêm phụ thuộc (Interfaces & dependency injection)
- Triển khai cụ thể cơ chế xử lý lỗi và ghi log (Error handling & logging implementation details)
- Chiến lược kiểm thử tự động chi tiết (Testing strategy)
```
```

---

### Step 6: Internal Spec Review Gate

Review the Specification internally before Blueprint generation.

Rules:
- Do not stop for user approval after the Specification.
- Do not end turn after the Specification.
- Include `frontend-design` in the review when the feature touches UI/UX, frontend components, layout, spacing, typography, color, animation, icons, visual hierarchy, aesthetic styling, or design-system decisions.
- If the Specification review fails, state the exact failed points and revise only those points.
- Continue to Blueprint generation only after the Specification review passes.
- No source code may be modified during this step.

---

### Step 7: Generate Technical Design Blueprint

Create the Design Blueprint under `docs/blueprints/QUICK-XXX_feature_name_blueprint.md`.

Use this template:

```markdown
<!-- File path: docs/blueprints/QUICK-XXX_feature_name_blueprint.md -->
---
artifact_type: blueprint
feature_id: QUICK-XXX
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – [Feature Name]

## 1. Proposed Code Changes
All files to create, modify, or delete must be listed here. No placeholders allowed.

### [File Path]
- **Operation**: [NEW | MODIFY | DELETE]
- **Responsibility**: [Explain the file change's specific role]
- **Changes**: [List classes, methods, or blocks affected]

## 2. Target Folder Structure
Complete directory layout after modifications:
```text
.
├── (folders and files structure)
```

## 3. Interface & Data Contracts
- **API/CLI Contracts**: [CLI flags, REST payloads, response schema, config properties]
- **Data Schema**: [JSON schemas, DB columns, or state models]

## 4. Algorithms & Key Logic
- [Pseudo-code or step-by-step logic description]

## 5. Validation Rules
- [Specify validation checks and input formatting constraints]

## 6. Implementation Checklist
- [ ] Task...

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Test method and target file.
```

---

### Step 8: Internal Blueprint Review + Final User Approval Gate

1. Register the blueprint via CLI:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/blueprints/QUICK-XXX_feature_name_blueprint.md`
2. Review the blueprint strictly against the Specification, this Skill, `AI_RULES.md`, document-compliance-assessment rules, and `frontend-design` when UI/design is affected.
3. If review fails, state the exact failed points and revise only those points. Repeat until review passes.
4. **ABSOLUTE USER APPROVAL STOP**: After the Blueprint review passes, present the Design Blueprint to the user in chat and immediately stop calling tools. End the turn. DO NOT proceed autonomously. DO NOT mark the Blueprint approved. DO NOT inspect additional files. DO NOT implement code.
5. If the user has not explicitly approved with `Y`, `Yes`, `Proceed`, `Continue`, or equivalent approval text, the Agent must remain stopped at this gate.
6. Once the user responds with approval in the chat, run:
   `python skills/workflow-runtime/scripts/workflow_runtime.py blueprint --path docs/blueprints/QUICK-XXX_feature_name_blueprint.md --approve`

---

### Step 10: Code Implementation

Only after receiving blueprint approval:
1. Verify the blueprint is approved in the session.
2. Implement code changes exactly as described in the blueprint.

---

### Step 12: Generate Quick Task Result

Upon completion, print the final summary:

```markdown
## Quick Task Result
Status: [PASS / FAILED]
Files Modified:
- [Relative path to file](link)

Validation:
Build: [PASS | FAILED]
Tests: [PASS | FAILED]

Recommended Next Step:
- Post-implementation verification complete. STOP. Recommend running Release if desired.
```
