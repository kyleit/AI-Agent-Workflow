---
name: strict-code-block-gate
description: Use when a Blueprint, approval gate, or implementation entry must validate implementation-ready code blocks across multiple programming languages before source writes.
version: 1.0.0
---

# Strict Code Block Gate

## Purpose

`strict-code-block-gate` is the canonical `CODE_BLOCK_GATE` authority. All workflow skills that create, approve, invalidate, or consume Blueprint code blocks MUST use this skill instead of local language-specific checks.

During Blueprint authoring, the gate is read-only with respect to framework
contracts. The Agent MUST NOT use an Edit/Create/Write operation on any
`.agents/contracts/**`, `.agents/policies/**`, `.agents/profiles/**`, gate
script, or gate configuration path while trying to obtain PASS. A missing,
malformed, or unexpectedly changed contract is evidence for `BLOCKED`, not a
repair target. Only Blueprint files and retained evidence may be repaired in
this loop.

The gate's measured projected line count is a lower bound, not a suggestion.
When a block is below that bound, the Agent must replace the whole block with
the complete copy-ready file and preserve all behavior required by its owning
surface. For a greenfield file this includes imports, declarations, exported
interfaces, validation, error and cancellation paths, integration wiring, and
tests or test seams where applicable. A short compilable example, signature
list, placeholder, or prose contract is never a full file.

## Non-Negotiable Contract

- Default decision is `BLOCKED`.
- Accepted aggregate decisions are only `PASS`, `FAIL`, `BLOCKED`, and `NOT_APPLICABLE`.
- A missing, ambiguous, or non-strict language profile is `BLOCKED`.
- Any failed code-block check makes the aggregate decision `FAIL`.
- Any blocked code-block check makes the aggregate decision `BLOCKED`.
- `PASS` is valid only when every implementation-ready code block has complete metadata, a strict language profile, a materialized validation scope, and architecture-boundary evidence.
- For a master Blueprint with phases, the gate validates the complete artifact set. Every row in every `File-By-File Change Matrix` must include `Code Block IDs`, each referenced block must exist, and its `file` must exactly match the matrix row. Missing phase blocks, orphan blocks, duplicate IDs, and file mismatches are `BLOCKED`.
- When a `Screen And Route Coverage Matrix` declares three or more routes, each
  route row must name concrete implementation files and matching code-block IDs.
  Feature routes may not all point at the root application shell (for example,
  mapping `#/hosts`, `#/settings`, and `#/scanner` to only `App.svelte`). A route
  without a covered view is `BLOCKED`, even when the shell block itself is valid.
- For a large greenfield artifact set, phase paths must encode the hierarchy
  `Master/<family>/<small-feature>/<phase>`. Direct `Master/<family>/<phase>`
  is allowed only for a measured small family. Required architecture families
  are derived from the request; family and small-feature IDs must be present in
  phase frontmatter.
- For source-changing Blueprints, `PASS` also requires each block's target file to be covered by the Blueprint's engineering evidence: an honest projected physical size, `projected_lines <= 500` for every physical source/config/test file, source-level family split shape when the source architecture requires it, facade/barrel/aggregate entry when split, and language-specific lint/typecheck/build commands from the active strict profile. Blueprint document length is never a gate.
- The gate NEVER writes product source files. It may only materialize temporary validation files under `.agents/tmp/code-block-gate/<workflow-id>/`.
- During Blueprint generation or repair, the Agent MUST NOT create, rewrite,
  relax, or delete `.agents/contracts/engineering-quality-gates.yaml`, strict
  profiles, gate scripts, or gate configuration to make a result pass. If the
  architecture contract is missing or malformed, stop with a blocking finding
  and route the contract through the architecture-review workflow; do not use a
  local contract edit as a Blueprint repair.
- Project test suites are not part of this gate. Test commands remain `NOT_RUN` unless a separate approved test-execution gate authorizes them.
- `NOT_RUN` applies to project execution only. It does not excuse missing code
  blocks. A complete artifact set must provide an implementation-ready block
  for every concrete file row before the gate can return `PASS`.
- The gate MUST treat the Blueprint as immutable input: it must not rewrite,
  truncate, or regenerate the Blueprint while validating code blocks.
- Blueprint repair is an Agent reasoning operation. The Agent MUST edit the
  actual Blueprint or phase file with native file tools and MUST NOT create or
  execute a scratch script to patch, expand, normalize, or regenerate blocks.
  Any workspace-writing scratch script is a hard `BLOCKED` authoring-policy
  finding, even when the resulting blocks look complete. The authoring audit
  also inspects recent AGY transcript command receipts, so inline commands
  such as `python -c`, `PowerShell -Command`, `node -e`, shell redirection, and
  file deletion commands that target workflow documents are blocked as well.
  Read-only parser, validator, hash, gate, and evidence commands remain allowed.
- Before validation, record the Blueprint SHA-256 and the presence of the
  `Data Flow And Sequence Diagram` section. After validation, re-read the
  Blueprint and fail with `blueprint_content_changed` if the hash or required
  data-flow section changed. A code-block repair that removes that section is
  always `BLOCKED`.
- `PASS` from this gate means only that the declared blocks are structurally
  and profile-valid. It is never evidence that the product builds, starts, or
  passes API/browser/desktop E2E. Those results require the separate real
  verification pipeline and retained runtime evidence.

## Greenfield Executable Verification Handoff

For `GREENFIELD_CROSS_LAYER` Blueprint sets, the structural gate is only the
first half of pre-approval verification. Before the coordinator may report
the documentation handoff as complete or request owner approval, it MUST run
the real language toolchains against the gate-materialized file set using the
commands declared by the active profiles: compiler/build, typecheck, and
dependency/checksum validation where applicable. A backend runtime surface
must also be started with its real persistence/runtime prerequisites and
exercised through at least one real contract request when the Blueprint
declares an executable server.

The execution must be performed on the materialized files, not inferred from
signatures, screenshots, mocked responses, or a `--no-execute` structural
receipt. Retain the exact commands, exit codes, tool output summary, runtime
inputs, and artifact paths in a separate verification evidence file. If any
declared command fails, if the prerequisite toolchain is missing, or if the
evidence cannot be retained, the greenfield handoff is `BLOCKED` or
`NOT_VERIFIED` and the Blueprint must be repaired before approval. This
requirement does not change the structural gate's `test_status: NOT_RUN`
field; it prevents that field from being misreported as product runtime PASS.

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
| `block_scope` | yes for implementation blocks | Must be `full-file` for source/config/schema/UI files, or `asset-manifest` for binary assets. |
| `full_file` | yes for implementation blocks | Must be `true` for source/config/schema/UI files. |

Placeholder text, ellipses used as omitted implementation, TODO-only blocks, or incomplete snippets are automatic `FAIL`.
Binary assets cannot be represented as source bytes in Markdown. They MUST use
the strict `asset` profile with a non-placeholder manifest block that declares
source, destination, inclusion rule, and checksum verification.
The gate also verifies the declared destination in the real workspace. Font
files must have a valid `wOF2`, `wOFF`, TrueType, or OpenType signature and
must not be empty or contain placeholder text. A manifest that describes a
font while the workspace contains a text stub is `BLOCKED`.
The gate MUST reject a binary target represented with `text`, `full-file`, a
one-line file, or any stub-like manifest. Generated lockfiles such as `go.sum`,
`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, and `Cargo.lock` MUST use
`language: generated-manifest`, `block_scope: generated-manifest`,
`full_file: false`, `operation: generate`, and an exact generator command. A
hand-authored checksum list is not implementation-ready evidence and MUST be
`BLOCKED`.
A short illustrative snippet is not an implementation contract. The gate
requires `block_scope: full-file`, `full_file: true`, and a content-size check
against the matrix projected physical lines. For a strict greenfield artifact
set, the declared projected count MUST be honest and the block MUST contain the
complete copy-ready file; the validator may allow only a small accounting
difference caused by line-ending normalization. Every physical source/config/
test file MUST be at most 500 lines. An oversized block is `BLOCKED` and must
be split by responsibility under one family directory with a facade/barrel/
aggregate entry. The Agent remains responsible
for reviewing imports, interfaces, error paths, states, and tests. A block that
  is materially shorter than its declared file is `BLOCKED`.
- Before running the gate, the Blueprint author MUST reconcile the matrix
  `Lines` value with the actual line count of the complete file block. Lowering
  the declared count to hide omitted implementation is a process violation and
  does not make a block complete. Completeness still requires all imports, types,
  exports, error paths, states, and integration points required by the upstream
  contract.

For a sizeable or greenfield delivery, the master is never a sufficient
validation scope by itself. The gate automatically discovers sibling and nested
blueprint files, requires a meaningful family/phase decomposition when the
matrix is large, and blocks if the phase artifact set is missing. A claim such
as `CODE_BLOCK_GATE: PASS` inside an artifact is untrusted and never overrides
the machine result. Placeholder, sample-only, stub, or not-implemented source
blocks are failures even when their metadata says `implementation_ready`.

## Spike-Verified Blueprint Contract

When source exists, use Branch A: read the actual source, cross-check every
identifier and signature, and mark every block `verified from: <path:line>`.
When source does not exist, use Branch B. B1 creates a runnable project under
`.agents/scratch/<work-item-slug>/`; B2 runs the real toolchain; B3 proves bad
data is rejected; B4 extracts only after B2 and B3 pass; B5 records commands,
exit codes, counts, and rejected constraints; B6 extracts every public unit at
the declared depth. A spike is evidence, not a code sample, because a sample
can compile while its constraints remain untested.

Every Blueprint declares `blueprint_depth: CONTRACT` or `blueprint_depth: FULL`.
The owner must choose the depth before Blueprint generation. CONTRACT contains
interfaces, structs, enums, constants, use-case signatures, DTOs, schemas, and
pure rule bodies. FULL contains all runnable code in the phase, including use
cases, adapters, handlers, entrypoints, migrations, packaging, frontend, and
tests. FULL is deliberately longer and requires rerunning the spike after a
design change; it removes the gap between approval and execution.

Zero blocks is not a vacuous PASS when API, interface, schema, or implementation
obligations exist. Partial extraction is not PASS: the number of public units
in the spike must equal the number represented in the Blueprint. FULL also
requires a real end-to-end entrypoint run. No block may be written from memory.

`.agents/scratch/<slug>/` is retained audit evidence until the work item closes;
product code must not import it. FULL implementation copies code and tests from
scratch, then reruns the complete test set at the product path. One-shot
containers are real verification for database, migration, Helm, and offline
frontend checks, not environment probes, and must be removed after evidence is
retained. `.gitignore` must not discard this evidence.

## Canonical Runner

Use the local runner for deterministic evidence:

```text
python skills/strict-code-block-gate/scripts/run_strict_code_block_gate.py --blueprint <blueprint.md> --phase-blueprint <phase.md> --workflow-id <id> --output docs/aiwf-runs/<id>/05-blueprint/code-block-gate.json --no-execute
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
- `artifact_set`: all master and phase Blueprint paths validated together

Workspace-alignment findings are authoritative after implementation. If a
writer changes a full-file target to make a build pass, the Blueprint and its
approval hash are stale. The workflow must return to Blueprint repair and
approval, or restore the source to the approved block, before implementation
can continue.
