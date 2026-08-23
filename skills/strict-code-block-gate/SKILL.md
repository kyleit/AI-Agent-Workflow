---
name: strict-code-block-gate
description: Use when a Blueprint, approval gate, or implementation entry must validate implementation-ready code blocks across multiple programming languages before source writes.
version: 1.0.0
---

# Strict Code Block Gate

## Purpose

`strict-code-block-gate` is the canonical `CODE_BLOCK_GATE` authority. All workflow skills that create, approve, invalidate, or consume Blueprint code blocks MUST use this skill instead of local language-specific checks.

## Non-Negotiable Contract

- Default decision is `BLOCKED`.
- Accepted aggregate decisions are only `PASS`, `FAIL`, `BLOCKED`, and `NOT_APPLICABLE`.
- A missing, ambiguous, or non-strict language profile is `BLOCKED`.
- Any failed code-block check makes the aggregate decision `FAIL`.
- Any blocked code-block check makes the aggregate decision `BLOCKED`.
- `PASS` is valid only when every implementation-ready code block has complete metadata, a strict language profile, a materialized validation scope, and architecture-boundary evidence.
- For source-changing Blueprints, `PASS` also requires each block's target file to be covered by the Blueprint's engineering evidence: projected file line count under 500, family-folder split shape when needed, facade/barrel/aggregate entry when split, and language-specific lint/typecheck/build commands from the active strict profile.
- The gate NEVER writes product source files. It may only materialize temporary validation files under `.agents/tmp/code-block-gate/<workflow-id>/`.
- Project test suites are not part of this gate. Test commands remain `NOT_RUN` unless a separate approved test-execution gate authorizes them.

## Required Blueprint Metadata

Every implementation-ready fenced code block MUST include adjacent metadata before the fence:

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Stable block identifier unique within the Blueprint. |
| `language` | yes | Declared language or profile key. |
| `file` | yes | Repository-relative target path. |
| `operation` | yes | `create`, `update`, `delete`, or `replace`. |
| `symbol` | no | Function, class, module, command, schema, or rule being changed. |
| `implementation_ready` | yes | Must be `true` for executable implementation blocks. |

Placeholder text, ellipses used as omitted implementation, TODO-only blocks, or incomplete snippets are automatic `FAIL`.

## Canonical Runner

Use the local runner for deterministic evidence:

```text
python skills/strict-code-block-gate/scripts/run_strict_code_block_gate.py --blueprint <blueprint.md> --workflow-id <id> --output docs/aiwf-runs/<id>/05-blueprint/code-block-gate.json --no-execute
```

The same files are mirrored under `.agents/skills/strict-code-block-gate/` for runtime use.

## Integration Points

- `plan-to-blueprint` MUST create structured metadata and persist `code-block-gate.json`.
- `quick-feature` and `quick-fix` MUST route local Blueprint code-block review through this skill.
- `readiness-and-approval-gates` MUST reject Blueprint approval when this gate is not `PASS`.
- `blueprint-to-implementation` MUST verify the gate result hash still matches the approved Blueprint before source writes.
- `documentation-synchronization-governance` MUST invalidate this gate when Blueprint code blocks, metadata, target paths, or language profiles drift.

## Evidence Files

The runner emits:

- `blueprint_full_sha256`
- `decision`
- `per_code_block`
- `profile_results`
- `materialized_scope`
- `blocking_findings`
- `test_status: NOT_RUN`
- `engineering_constraints`: line-budget, family-folder split, aggregate entry, and language validator coverage when supplied by the Blueprint
