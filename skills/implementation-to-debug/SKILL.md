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
  usage: cached---

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

Review the implementation, verify code standards, run targeted validation, debug tests, exercise real runtime cases without mocks/fake data, capture browser evidence when UI is affected, and generate the post-implementation evidence report before final verification.

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
10. **Code Review Gate**: Use `code-standard-review` to review every changed file against the approved Blueprint when one exists. For post-implementation maintenance/debug work without an active Blueprint, review against the explicit user request, reviewed Git diff, project rules, architecture boundaries, security expectations, and scope limits before validation is marked PASS.
11. **Real Runtime Case Gate**: Exercise at least one real user/runtime path through the affected CLI/API/IPC/database/service/browser surface. Mock-only, reflection-only, and fake-data-only checks are not sufficient.
12. **Frontend Browser Evidence Gate**: If UI/browser behavior is affected, verify in a real browser and capture screenshots. Prefer IDE browser tools. If those are unavailable, use a browser reachable through a Chrome DevTools Protocol (CDP) debug port or equivalent real browser automation path.
13. **Final Evidence Report Gate**: Write `docs/features/<feature-family>/reports/<WORK_ITEM_ID>_<slug>_post_implementation_report.md` (or the matching phase variant inside that semantic feature folder) with relative links to screenshots under `docs/features/<feature-family>/reports/assets/<WORK_ITEM_ID>_<slug>/`.

---

## Workflow Sequence

```
Step 1: Inspect session state & Git branch
        ↓
Step 2: Code Review Gate
        - Use `code-standard-review`
        - Review changed files against Blueprint, project rules, architecture boundaries, security, and scope
        - If FAIL, fix only failed points and repeat review
        ↓
Step 3: Code Validation Gate
        - Run targeted build/lint/typecheck/dependency/schema/config checks for changed components
        ↓
Step 4: Debug/Test Gate
        - Run targeted tests for changed components
        - For pytest, use `pytest -v -s <related_test_file_or_directory> 2>&1 | tee .agents/runtime/tests.log`
        - Resolve failures and rerun within task scope
        ↓
Step 5: Real Runtime Case Gate
        - Exercise real CLI/API/IPC/database/service/browser surface without mocks or fake test doubles
        - Clean up any seed data created through real application interfaces
        ↓
Step 6: Frontend Browser Evidence Gate (when UI/browser behavior is affected)
        - Capture screenshots with IDE browser tools, or use CDP debug port fallback if IDE browser tools are unavailable
        - Store screenshots under docs/features/<feature-family>/reports/assets/<WORK_ITEM_ID>_<slug>/
        ↓
Step 7: Generate Debug Report at docs/features/<feature-family>/debug/<WORK_ITEM_ID>_<slug>_debug.md
        (or docs/features/<feature-family>/debug/phase-NN-<phase-slug>/phase-debug.md when debugging one phase)
        ↓
Step 8: Generate Post-Implementation Evidence Report at docs/features/<feature-family>/reports/<WORK_ITEM_ID>_<slug>_post_implementation_report.md
        (or matching FIX/QUICK/phase variant)
        ↓
Step 9: Update session checkpoint to 7 & output heartbeat
```

---

## Output Report Format: `docs/features/<feature-family>/debug/FEAT-XXX_slug_debug.md` (or `phase-NN-<phase-slug>/phase-debug.md` — see Workflow Sequence Step 4)

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
- **Code Review Status**: [PASS | FAIL] (Blueprint compliance, scope, architecture, security, code quality)
- **Build Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Lint Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Typecheck Status**: [PASS | FAIL | Not Configured] (Command used: `[cmd]`)
- **Unit Tests Status**: [PASS | FAIL] (Command used: `[cmd]`)
- **Runtime Validation Status**: [PASS | FAIL] (Command used: `python skills/workflow-runtime/scripts/workflow_runtime.py debug`)
- **Real Runtime Case Status**: [PASS | FAIL | Not Applicable + why] (Surface: `[real CLI/API/IPC/database/service/browser]`)
- **Frontend Browser Evidence Status**: [PASS | FAIL | Not Applicable + why] (Tool: `[IDE browser | CDP | equivalent]`)

## 2A. Code Standard Review Evidence
| Field | Evidence |
| :--- | :--- |
| Skill Used | `code-standard-review` |
| Blueprint Reviewed | `docs/blueprints/...` |
| Changed Files Reviewed | `relative/path`, `relative/path` |
| Checklist Result | PASS/FAIL rows with concrete evidence |
| Failed Points | `None` or exact failed-point list |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Final Result | [PASS | FAIL] |

## 3. Issues Found & Resolved
| Issue Description | Root Cause | Fix Summary | Files Affected |
| :--- | :--- | :--- | :--- |
| [Issue 1] | [Why it happened] | [How it was fixed] | [File path] |

## 4. Remaining Risks
- **Risk**: [Risk] → **Mitigation**: [Mitigation]

## 5. Real Runtime Evidence
| Case | Real Surface | Data Source | Command/Action | Result | Cleanup |
| :--- | :--- | :--- | :--- | :---: | :--- |
| [Case name] | [CLI/API/IPC/database/service/browser] | [Real application data or seed created through real interface] | `[command/action]` | [PASS/FAIL] | [Done/Not needed] |

## 6. Browser Evidence
| Screenshot | Scenario | Tool | Result |
| :--- | :--- | :--- | :---: |
| `[relative/path/to/screenshot.png](../reports/assets/FEAT-XXX_slug/screenshot.png)` | [Scenario] | [IDE browser/CDP/equivalent] | [PASS/FAIL] |

## 7. Post-Implementation Evidence Report
- **Report Path**: `docs/features/<feature-family>/reports/FEAT-XXX_slug_post_implementation_report.md`
- **Screenshots Directory**: `docs/features/<feature-family>/reports/assets/FEAT-XXX_slug/`

## 8. Debug Status
**Status**: [PASS | FAIL (Unresolved issues remain)]
```

If debug status is **FAIL**, you MUST NOT proceed to Verification. Return to implementation phase to resolve the outstanding issues.

The debug status MUST be **FAIL** if:
- `code-standard-review` fails against the approved Blueprint when one exists, or against the explicit user request, reviewed Git diff, and project rules when no active Blueprint exists.
- Targeted validation/build/lint/typecheck fails.
- Targeted tests fail or pytest logs are not written to `.agents/runtime/tests.log` when pytest is used.
- The changed behavior has a real runtime surface but only mock/fake/reflection tests were run.
- UI/browser behavior changed but no real browser/CDP screenshot evidence exists.
- The post-implementation evidence report under `docs/features/<feature-family>/reports/` is missing.

---

## Post-Implementation Evidence Report Format: `docs/features/<feature-family>/reports/FEAT-XXX_slug_post_implementation_report.md`

Generate this Markdown report after debug gates finish. Use the matching `FIX-XXX`, `QUICK-XXX`, or phase filename when applicable.

```markdown
---
artifact_type: post-implementation-report
feature_id: FEAT-XXX
workflow: standard
status: [PASS | FAIL]
---

# Post-Implementation Evidence Report – [Feature Title]

## 1. Summary
[What was implemented and what was verified]

## 2. Changed Files Reviewed
| File | Blueprint Contract | Review Result | Notes |
|---|---|:---:|---|
| `relative/path` | `relative/blueprint.md#section` | [PASS/FAIL] | [Notes] |

## 2A. Code Standard Review Evidence
| Field | Evidence |
|---|---|
| Skill Used | `code-standard-review` |
| Checklist Result | PASS/FAIL rows from `code-standard-review` |
| Failed Points | `None` or exact failed-point list |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Final Result | [PASS | FAIL] |

## 3. Validation Evidence
| Gate | Command | Result | Log/Notes |
|---|---|:---:|---|
| Build | `[cmd]` | [PASS/FAIL] | [Notes] |
| Lint | `[cmd]` | [PASS/FAIL] | [Notes] |
| Typecheck | `[cmd]` | [PASS/FAIL] | [Notes] |
| Tests | `[cmd]` | [PASS/FAIL] | `.agents/runtime/tests.log` if pytest was used |

## 4. Real Runtime Case Evidence
| Case | Real Surface | Data Source | Steps | Result | Cleanup |
|---|---|---|---|:---:|---|
| [Case] | [CLI/API/IPC/database/service/browser] | [Real app data or seed created through real interface] | [Steps] | [PASS/FAIL] | [Done/Not needed] |

## 5. Browser / Screenshot Evidence
| Screenshot | Scenario | Tool | Result |
|---|---|---|:---:|
| ![Scenario](assets/FEAT-XXX/screenshot.png) | [Scenario] | [IDE browser/CDP/equivalent] | [PASS/FAIL] |

## 6. Issues Found And Fixed
| Issue | Root Cause | Fix | Re-test Result |
|---|---|---|:---:|
| [Issue] | [Cause] | [Fix] | [PASS/FAIL] |

## 7. Remaining Risks
- [Risk or `None`]

## 8. Final Result
**Status**: [PASS | FAIL]
```

---

## Completion Contract

```text
Current Phase:
Phase 5 — Implementation to Debug

Status:
Completed

Report Generated:
docs/features/<feature-family>/debug/FEAT-XXX_slug_debug.md (or phase-NN-<phase-slug>/phase-debug.md)

Debug Status:
[PASS | FAIL]

Recommended Next Skill:
debug-to-verify (command: /verify)
```
