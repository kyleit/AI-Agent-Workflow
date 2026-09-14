---
artifact_type: phase_blueprint
feature_id: {{WORK_ITEM_ID}}
family_id: {{FAMILY_ID}}
small_feature_id: {{SMALL_FEATURE_ID}}
phase_id: P{{PHASE_NUMBER}}
workflow: standard-development
status: awaiting_owner_approval
master_blueprint: {{MASTER_BLUEPRINT_PATH}}
---

`phase_id` is sequential within this `family_id/small_feature_id` only. It may
repeat in another small feature; implementation-ready block IDs must not.

# {{WORK_ITEM_ID}} {{FAMILY_ID}}/{{SMALL_FEATURE_ID}} P{{PHASE_NUMBER}} {{PHASE_TITLE}} Phase Blueprint

## Phase Scope
{{PHASE_OUTCOME_AND_EXPLICIT_BOUNDARIES}}

## Blueprint Document Shape
Document length is never a completeness gate. Keep this phase contract
coherent and split only at a meaningful ownership, dependency, review, or
context boundary. Never omit, summarize, or mechanically divide implementation
blocks to satisfy an arbitrary size target.

## Phase Entry And Exit Contract
| Contract | Entry Preconditions | Produced Artifacts | Exit Verification | Blocking Condition |
|---|---|---|---|---|
| {{CONTRACT}} | {{PRECONDITIONS}} | {{ARTIFACTS}} | {{COMMAND_AND_BINARY_RESULT}} | {{NO_GO}} |

## Owned Directory Tree
```text
{{COMPLETE_PHASE_OWNED_DIRECTORY_TREE}}
```

## Full-File Delivery Contract
Every file in this phase is a concrete physical deliverable. Its
implementation-ready block must describe the complete file, exact imports,
exports, error behavior, configuration, and integration points. A shortened
illustrative snippet is not sufficient for approval.

## Dependency Contract
| Depends On | Required Artifact/Output | Consumer |
|---|---|---|
| {{DEPENDENCY}} | {{OUTPUT}} | {{CONSUMER}} |

## Implementation Task Contract

Each task is independently testable and is handed to a fresh implementation
Agent. The sequence is always: real failing test/action, observed failure,
complete file implementation, real green verification, retained evidence.

| Task ID | Responsibility | Exact Files | Depends On | Consumes | Produces | Red Test/Action | Implementation Blocks | Green Command + Expected Result | Evidence | Rollback |
|---|---|---|---|---|---|---|---|---|---|---|
| {{TASK_ID}} | {{ONE_RESPONSIBILITY}} | {{CONCRETE_FILES}} | {{TASK_IDS}} | {{TYPED_INTERFACES}} | {{TYPED_INTERFACES}} | {{COMMAND_AND_EXPECTED_FAILURE}} | {{BLOCK_IDS}} | {{COMMAND_AND_BINARY_EXPECTATION}} | {{RETAINED_EVIDENCE_PATH}} | {{ROLLBACK}} |

Every task must contain enough exact information for a fresh Agent to execute
it without guessing. Representative snippets, prose-only test plans, and
unresolved dependencies are `NO-GO`.

## File-By-File Change Matrix
| File | Layer | Operation | Owner | Imports | Exports | Exact Signatures | Lines | Profile | Commands | Code Block IDs | Tests | Evidence |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| {{RELATIVE_FILE}} | {{LAYER}} | {{OPERATION}} | {{OWNER}} | {{IMPORTS}} | {{EXPORTS}} | {{SIGNATURES}} | {{LINES}} | {{PROFILE}} | {{COMMANDS}} | {{BLOCK_IDS}} | {{TEST_IDS}} | {{EVIDENCE_PATHS}} |

Every concrete row above must contain one or more real IDs from the
Implementation-Ready Code-Block Inventory. `{{BLOCK_IDS}}` may not be blank,
`TBD`, or `NOT_APPLICABLE` for a source/config/schema/UI/test/asset-manifest
file.

This phase may be any length required to describe its independently executable
delivery unit. If it becomes too broad to own, test, review, or hand off as one
unit, split it at a real boundary and update the Master coverage references.

## Owned Surface Inventory

If this phase owns UI, list every route/screen/state it materializes. If it
owns backend, list every capability boundary it materializes. A phase may not
claim a family is complete while hiding screens, endpoints, schema objects,
workers, or tests in prose.

| Surface/Capability | Concrete Files | Code Blocks | API/Data Contract | States/Errors | Test IDs | Evidence |
|---|---|---|---|---|---|---|
| {{SURFACE_OR_CAPABILITY}} | {{FILES}} | {{BLOCK_IDS}} | {{CONTRACT}} | {{STATES}} | {{TEST_IDS}} | {{EVIDENCE}} |

## Implementation-Ready Code-Block Inventory
{{CODE_BLOCKS_WITH_ADJACENT_METADATA}}

Use literal metadata immediately before each implementation-ready fence. For
example:

id: CB-FAMILY-001
language: go
file: internal/example/example.go
operation: create
symbol: Example
implementation_ready: true
block_scope: full-file
full_file: true
```go
package example

// Complete copy-ready file contents belong here.
```

Replace the structural example with the complete file and a globally unique
ID before review. Do not emit a block without this metadata.

## QA Verification Matrix
| Test ID | Requirement/AC | Real Action | Expected Result | Command | Status | Evidence |
|---|---|---|---|---|---|---|
| {{TEST_ID}} | {{AC}} | {{REAL_ACTION}} | {{BINARY_EXPECTATION}} | {{COMMAND}} | NOT_RUN | {{EVIDENCE_PATH}} |

## Rollback
{{PHASE_ROLLBACK_STEPS}}

## NO-GO Conditions

- A file, requirement, code block, test, or evidence path is missing from the
  phase mapping.
- A dependency output is assumed rather than named and verified.
- A real test is represented by mock, dry-run, inferred, or screenshot-only
  evidence.

## Internal Review Evidence
| Field | Evidence |
|---|---|
| Reviewer Roles | {{ROLES}} |
| Source Artifacts Reviewed | Master Blueprint, upstream artifacts, active skills |
| Checklist Result | PASS/FAIL with concrete evidence |
| Failed Points | {{FAILED_POINTS_OR_NONE}} |
| Revision Scope | {{REVISION_SCOPE}} |
| Re-review Count | {{REVIEW_COUNT}} |
| Document Compliance Score | {{SCORE}}/100 |
| Relative Path Scan | PASS/FAIL |

## Section 10: Blueprint Readiness Assessment And CODE_BLOCK_GATE
| Field | Evidence |
|---|---|
| CODE_BLOCK_GATE | Exact canonical gate decision, JSON path, Blueprint SHA-256, and findings |
| Runtime Approval Readiness | Exact validator status and score; `APPROVAL_READY` only when score is 100 and findings are empty |
| Real E2E Status | `NOT_RUN` before implementation; never claim PASS without retained runtime evidence |
