---
name: implementation-to-debug
command: debug
aliases:
  - compile
  - lint
category: workflow
tags:
  - debug
  - testing
  - verification
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-04
updated_at: 2026-07-04
description: Review the implementation. Identify and resolve problems before verification.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached
---

# Skill: implementation-to-debug

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 6 or 5"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "implementation-to-debug" --command "debug" --checkpoint 7 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 7 --step "Step Complete" --next-skill "frontend-visual-debug" --next-command "visual-debug"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Purpose

Review the implementation, verify builds, resolve compilation and linting issues, and fix unit tests before code verification.

---

## Responsibilities

1.  **Read Project Profile**: Load `.agents/project-profile.json` to identify the languages, package managers, and tools configured for this workspace.
2.  **Stack-Specific Build & Compile Check**: Execute the compiler/build commands corresponding to the project stack:
    - **Go**: `go build ./...`
    - **Node/Vite/Svelte**: `npm run build` (or yarn/pnpm/bun equivalents)
    - **Python**: compile check if applicable, or package build
    - **Rust**: `cargo build`
    - **Other**: gradle/maven/dotnet equivalent commands listed in the profile.
3.  **Stack-Specific Lint & Formatter Check**:
    - **Go**: `go fmt ./...` or `golangci-lint run`
    - **Node**: `npm run lint` or `eslint`
    - **Python**: `ruff check` or `flake8`
    - **Rust**: `cargo clippy`
4.  **Stack-Specific Typecheck**:
    - **Node (TypeScript)**: `npm run typecheck` or `tsc --noEmit`
    - **Python**: `mypy`
5.  **Unit Tests Execution**: Run unit tests corresponding to the stack:
    - **Go**: `go test ./...`
    - **Node**: `npm test` or `vitest run`
    - **Python**: `pytest`
    - **Rust**: `cargo test`
6.  **Fix Compilation & Runtime Errors**: If any checks fail, analyze stderr, locate the bugs, and apply minimal fixes.
7.  **Logging & Error Handling**: Improve logging visibility, format, and ensure proper try-catch/error propagation.
8.  **Code Cleanup**: Remove dead code, unused imports, or debug console logs.
9.  **Runtime Validation Pipeline**: Execute the complete runtime debug validation pipeline (build target binary, start application, wait for readiness detection, execute smoke tests, verify health status, analyze runtime log classifications, perform graceful shutdown, and handle self-healing loop errors).

---

## Workflow Sequence

```
Step 1: Inspect session state & Git branch
        ↓
Step 2: Run compiler, build, linter, tests, and runtime validation pipeline
        ↓
Step 3: Resolve any errors or test failures
        ↓
Step 4: Generate Debug Report at docs/debug/FEAT-XXX_debug.md
        ↓
Step 5: Update session checkpoint to 7 & output heartbeat
```

---

## Output Report Format: `docs/debug/FEAT-XXX_debug.md`

Generate the debug report using this Markdown template:

```markdown
---
artifact_type: debug
feature_id: FEAT-XXX
workflow: standard
status: [PASS | FAIL]
---

# Debug Report – [Feature Title]

## 1. Summary
[Brief description of the debug phase activities]

## 2. Diagnostics
- **Build Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Lint Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Unit Tests Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Runtime Validation Status**: [PASS | FAIL] (Command used: `python skills/workflow-runtime/scripts/workflow_runtime.py debug`)

## 3. Issues Found & Resolved
| Issue Description | Root Cause | Fix Summary | Files Affected |
| :--- | :--- | :--- | :--- |
| [Issue 1] | [Why it happened] | [How it was fixed] | [File path] |

## 4. Remaining Risks
- **Risk**: [Risk] → **Mitigation**: [Mitigation]

## 5. Debug Status
**Status**: [PASS | FAIL (Unresolved issues remain)]
```

If debug status is **FAIL**, you MUST NOT proceed to Verification. Return to implementation phase to resolve the outstanding issues.

---

## Completion Contract

```text
Current Phase:
Phase 5 — Implementation to Debug

Status:
Completed

Report Generated:
docs/debug/FEAT-XXX_debug.md

Debug Status:
[PASS | FAIL]

Recommended Next Skill:
debug-to-verify (command: /verify)
```
