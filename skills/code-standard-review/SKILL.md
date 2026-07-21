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
description: Use when reviewing implemented code against an approved Blueprint, project rules, coding standards, architecture boundaries, security, maintainability, and testability before validation or release.
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

# Skill: code-standard-review

## Purpose

Provide the mandatory code review standard for post-implementation quality gates. This Skill verifies that changed code is correct, scoped, maintainable, secure, testable, and faithful to the approved Blueprint before validation/debug can be marked PASS.

## Required Inputs

- Approved Technical Blueprint under `docs/blueprints/`.
- List of changed files for the current work item.
- Relevant source files and tests.
- Active project rules from `AGENTS.md`, `AI_RULES.md`, and the active workflow Skill.
- Language/framework helper Skill when available, such as `python-development`, `go-development`, `golang-pro`, or `csharp-dotnet-pro`.

## Review Sequence

1. Read the approved Blueprint and its companion files.
2. Read only changed files and directly related tests/configuration.
3. Compare implementation against the Blueprint file-by-file.
4. Review against the Code Standard Checklist below.
5. Produce PASS/FAIL evidence.
6. If FAIL, report exact failed points and required corrections. The implementer must fix only those points and rerun this review.

## Code Standard Checklist

| # | Standard | PASS Requirement |
|---|---|---|
| 1 | Blueprint Compliance | Every changed file, function, public API, schema, and behavior matches the approved Blueprint or documents a justified minimal gap. |
| 2 | Scope Control | No unrelated refactors, formatting churn, feature creep, or out-of-scope file changes. |
| 3 | Architecture Boundaries | Dependency direction, layer placement, module ownership, and public/private boundaries follow project architecture. |
| 4 | Correctness | Main path, edge cases, error paths, idempotency, concurrency, and state transitions are handled correctly. |
| 5 | Error Handling & Logging | Errors are explicit, actionable, and recoverable where appropriate; logs are useful and do not leak secrets. |
| 6 | Security & Privacy | Inputs are validated, sensitive values are protected, permissions are respected, and no secrets or local absolute paths are introduced. |
| 7 | Maintainability | Names are clear, duplication is controlled, abstractions are justified, comments are useful, and code follows local style. |
| 8 | Performance & Resource Use | Work is bounded, no obvious leaks or runaway loops, I/O is efficient, and long-running processes clean up. |
| 9 | Testability | Tests or validation points map to changed behavior; mocks are not the only evidence when real runtime behavior exists. |
| 10 | Documentation & Traceability | Reports, docs, and changed behavior map back to requirements, Blueprint sections, and verification evidence. |

## Automatic FAIL Conditions

- Implementation changes code without an approved Blueprint.
- Changed behavior contradicts the Blueprint without an explicit reviewed correction path.
- Missing changed-file review evidence.
- Any local absolute path or `file:///` link is written into project artifacts.
- Secret, token, credential, private key, cookie, or sensitive data appears in code, docs, or logs.
- Domain/application/infrastructure/interface boundaries are violated.
- Mock-only tests are used as completion evidence for behavior with a real runtime surface.
- UI/browser changes have no real browser or CDP screenshot evidence.
- The review says PASS while any checklist item lacks concrete evidence.

## Required Review Evidence

Add this table to the debug report and post-implementation report:

```markdown
## Code Standard Review Evidence

| Field | Evidence |
|---|---|
| Reviewer Roles | Code Reviewer / Architecture Reviewer / Security Reviewer / QA Reviewer / relevant Specialist |
| Blueprint Reviewed | `docs/blueprints/...` |
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
