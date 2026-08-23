---
name: code-standard-review
command: code-review
aliases:
  - standard-review
  - implementation-review
category: review
tags:
  - code-review
  - standards
  - quality
  - compliance
version: 1.0.0
license: MIT
created_at: 2026-07-21
updated_at: 2026-07-21
description: Use when reviewing implemented code against an approved Blueprint when available, or against an explicit user request and reviewed diff for maintenance/release-only work, plus project rules, coding standards, architecture boundaries, security, maintainability, and testability before validation or release.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached
---

> [!CRITICAL]
> ## ⛔ MANDATORY ENFORCEMENT GUARDS — READ BEFORE ANY ACTION
>
> **YOU MUST COMPLY WITH ALL 5 GUARDS BELOW. VIOLATION = IMMEDIATE STOP.**
>
> 1. **BOOTSTRAP FIRST**: You MUST have executed `initialize-workflow` skill and possess a valid Bootstrap Receipt (SHA-256) BEFORE executing this skill. If you have NOT loaded AI_RULES.md, AGENTS.md, and memory context — STOP NOW and run `initialize-workflow` first.
>
> 2. **COORDINATOR ROUTING**: This skill MUST be invoked via `workflow-coordinator` delegation chain (`aiwf → initialize-workflow → workflow-coordinator → this skill`). Direct invocation from raw user prompt is FORBIDDEN.
>
> 3. **NO BLUEPRINT = NO CODE**: Source code MUST NOT be created, modified, or deleted until a Technical Design Blueprint exists under `docs/features/` AND is explicitly approved by the user. Spec and Blueprint documents MUST be created FIRST.
>
> 4. **PHYSICAL WRITES ONLY**: All file changes MUST be physical writes to the project filesystem using file creation/edit tools. The following are NOT valid implementation and are STRICTLY FORBIDDEN:
>    - IDE "proposed changes" or "Apply" button
>    - Code blocks in chat/conversation response presented as implementation
>    - IDE virtual patches or preview mode
>    - Any change that exists only in AI response but not on disk
>    - Ref: Physical Repository Write Policy (AI_RULES.md Section 33)
>
> 5. **DOCUMENTATION FIRST**: Required workflow documents (Spec, Blueprint, Report) MUST be created BEFORE or IN THE SAME TRANSACTION as source code changes. No source change is complete without its corresponding document update.

# Skill: code-standard-review

## Purpose

Provide the mandatory code review standard for post-implementation quality gates. This Skill verifies that changed code is correct, scoped, maintainable, secure, and testable before validation/debug can be marked PASS. When an approved Blueprint exists, the review must verify Blueprint fidelity. When no active Blueprint exists because the task is maintenance/release-only work, the review must verify fidelity to the explicit user request, reviewed Git diff, and project rules instead.

> [!CRITICAL]
> **Cross-Skill Strict Policy & Physical Write Invariant**:
> **STRICT ENGINEERING POLICY IS AUTHORITATIVE.**
> The skill MUST load the Core Engineering Policy (`.agents/policies/strict-engineering.md`), Physical Repository Write Policy (`.agents/policies/physical-repository-write.md`), all active Language Profiles (`.agents/profiles/*.yaml`), and the Project Architecture Contract (`.agents/contracts/engineering-quality-gates.yaml`) during review.
> A skill MUST NOT weaken, bypass, suppress, reinterpret, or locally override a blocking gate.
> Code review MUST enforce Physical Repository Write Integrity (`disk = truth`, working tree inspection), file-size limit (<= 500 lines per physical file), family-folder split shape, Fail-Fast dependencies, and zero validator bypasses (`no any`, `# type: ignore`, `@ts-ignore`, `_ = err`).

## Required Inputs

- Approved Technical Blueprint under `docs/features/<feature-family>/blueprints/` when the implementation came from a workflow Blueprint.
- Explicit user request and reviewed Git diff when this is maintenance/release-only work without an active Blueprint.
- List of changed files for the current work item.
- Relevant source files and tests.
- Active project rules from `AGENTS.md`, `AI_RULES.md`, and the active workflow Skill.
- Language/framework helper Skill when available, such as `python-development`, `go-development`, `golang-pro`, or `csharp-dotnet-pro`.

## Review Sequence

1. Read the approved Blueprint and its companion files when one exists. If no active Blueprint exists for maintenance/release-only work, read the explicit user request, release diff, and relevant rules instead.
2. Read only changed files and directly related tests/configuration.
3. Compare implementation against the Blueprint file-by-file when one exists; otherwise compare the changed files against the explicit request and release diff.
4. Review against the Code Standard Checklist below.
5. Produce PASS/FAIL evidence.
6. If FAIL, report exact failed points and required corrections. The implementer must fix only those points and rerun this review.

## Code Standard Checklist

| # | Standard | PASS Requirement |
|---|---|---|
| 1 | Requirement Compliance | Every changed file, function, public API, schema, and behavior matches the approved Blueprint when one exists, or the explicit user request and reviewed release diff when no active Blueprint exists. Any justified minimal gap is documented. |
| 2 | Scope Control | No unrelated refactors, formatting churn, feature creep, or out-of-scope file changes. |
| 3 | Architecture Boundaries | Dependency direction, layer placement, module ownership, and public/private boundaries follow project architecture. |
| 3a | Family-Folder Splits | Files split for the 500-line limit are grouped under one family-name directory and exposed through one facade/barrel/aggregate entry file; no flat scatter-splitting. |
| 4 | Correctness | Main path, edge cases, error paths, idempotency, concurrency, and state transitions are handled correctly. |
| 5 | Error Handling & Logging | Errors are explicit, actionable, and recoverable where appropriate; logs are useful and do not leak secrets. |
| 6 | Security & Privacy | Inputs are validated, sensitive values are protected, permissions are respected, and no secrets or local absolute paths are introduced. |
| 7 | Maintainability | Names are clear, duplication is controlled, abstractions are justified, comments are useful, and code follows local style. |
| 8 | Performance & Resource Use | Work is bounded, no obvious leaks or runaway loops, I/O is efficient, and long-running processes clean up. |
| 9 | Testability | Tests or validation points map to changed behavior; mocks are not the only evidence when real runtime behavior exists. |
| 10 | Documentation & Traceability | Reports, docs, and changed behavior map back to requirements, Blueprint sections, and verification evidence. |

## Automatic FAIL Conditions

- Starting feature/fix implementation changes code without an approved Blueprint.
- Changed behavior contradicts the Blueprint when one exists, or contradicts the explicit user request/release diff when no active Blueprint exists, without an explicit reviewed correction path.
- Missing changed-file review evidence.
- Any local absolute path or local file URL scheme is written into project artifacts.
- Secret, token, credential, private key, cookie, or sensitive data appears in code, docs, or logs.
- Domain/application/infrastructure/interface boundaries are violated.
- Mock-only tests are used as completion evidence for behavior with a real runtime surface.
- UI/browser changes have no real browser or CDP screenshot evidence.
- The review says PASS while any checklist item lacks concrete evidence.

## Required Review Evidence

The Audit Report MUST be generated into the canonical Feature Family reports directory:
`docs/features/<feature-family>/reports/<feature-family>_audit_report.md`

Add this table to the audit and post-implementation report:

```markdown
## Code Standard Review Evidence

| Field | Evidence |
|---|---|
| Reviewer Roles | Code Reviewer / Architecture Reviewer / Security Reviewer / QA Reviewer / relevant Specialist |
| Baseline Reviewed | `docs/features/<feature-family>/blueprints/...` when available, otherwise explicit user request + reviewed Git diff |
| Changed Files Reviewed | `relative/path`, `relative/path` |
| Checklist Result | PASS/FAIL rows with concrete evidence |
| Failed Points | `None` or exact failed-point list |
| Fix Scope | `None` or exact sections/files to revise |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Final Result | `PASS` or `FAIL` |
```

## Completion Contract

```text
Current Gate:
Code Standard Review

Status:
[PASS | FAIL]

Required Next Gate:
Code Validation Gate

If FAIL:
Return to implementer with exact failed points only.
```
