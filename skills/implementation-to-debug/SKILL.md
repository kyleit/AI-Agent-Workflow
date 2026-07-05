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
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-04
updated_at: 2026-07-04
description: Review the implementation. Identify and resolve problems before verification.
---

# Skill: implementation-to-debug

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

Before executing, inspect `.agents/.session.json` and perform the **Runtime Health Check**, **Drift Detection**, and **Checkpoint Verification**.
Verify that the current checkpoint in `.session.json` is exactly `6` (Implementation Complete).
1. If the session file is missing, if context health is `broken`, or if the current checkpoint is not `6`:
   - Recommend running: `blueprint-to-implementation` or `workflow-runtime` to reach the correct checkpoint state.
   - Stop execution.
2. At the start of execution, update `.session.json` checkpoint to `7` (Debug Complete) and set `"status"` to `"in_progress"`.
3. Upon successful debug validation and generation of the report, update `.session.json` checkpoint to `7` (Debug Complete), set `"status"` to `"completed"`, and output the runtime heartbeat.
4. If the execution fails or is aborted due to unresolved issues, set `"status"` to `"failed"`.

---

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

---

## Workflow Sequence

```
Step 1: Inspect session state & Git branch
        ↓
Step 2: Run compiler, build, linter, and tests
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
