---
name: loop-controller
command: loop
aliases:
  - loop-engine
  - self-correcting-loop
category: runtime
tags:
  - loop
  - controller
  - runtime
  - self-correcting
  - deterministic
version: 1.0.0
license: MIT
created_at: 2026-09-18
updated_at: 2026-09-18
role: loop_control_governance
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
state_authority: .agents/state
loop_state_path_pattern: .agents/state/loop/<workflow-id>.json
loop_ledger_path_pattern: .agents/state/loop/<workflow-id>.ledger.jsonl
engine_entrypoint: scripts/loop_engine
protocol_fallback: PROTOCOL.md
hash_algorithm: SHA-256
additive_only: true
direct_source_write: false
approval_authority: none
default_max_iterations: 8
default_no_progress_threshold: 3
description: Turn-driven, no-daemon self-correcting loop controller for the AIWF pipeline. Wraps the existing linear handoff with a bounded LOAD -> EXECUTE -> EVALUATE -> DECIDE -> PERSIST cycle, deciding one transition of {ADVANCE, REPEAT, BACKTRACK, HALT} per invocation from gate verdicts, with hard stop-conditions (max iterations, no-progress, gate-pass-final, user-halt, unrecoverable error). Deterministic Python engine (Script-First) plus a PROTOCOL.md hand-execution fallback; agent-agnostic via thin adapters.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: none
  workspace_scan: none
---

> [!CRITICAL]
> ## ⛔ MANDATORY ENFORCEMENT GUARDS — READ BEFORE ANY ACTION
>
> 1. **BOOTSTRAP FIRST**: Requires a valid Bootstrap Receipt (SHA-256) from `initialize-workflow`.
> 2. **COORDINATOR ROUTING**: Invoked only via the `workflow-coordinator` delegation chain. Direct invocation from a raw user prompt is FORBIDDEN.
> 3. **ADDITIVE-ONLY**: This skill only ADDS a control layer. It MUST NOT rename or remove any schema key, enum value, gate name, handoff order, the Bootstrap Receipt, the 95/100 readiness threshold, the SHA-256 approval mechanism, or the authority matrix.
> 4. **NO DAEMON**: No server, no port, no background process. Every step is a single turn-driven invocation; all state is files under `.agents/state/loop/`.
> 5. **NO SELF-APPROVAL / NO SOURCE WRITE**: `approval_authority: none`. The controller decides transitions only; it never approves gates and never edits feature source code.

# Skill: loop-controller (AIWF Self-Correcting Loop Controller)

## 0. Contract & Governance Boundaries
- **Role**: `loop_control_governance`
- **Canonical Entrypoint**: `workflow-coordinator`
- **State Authority**: `.agents/state/loop/` (never `.agents/.session.json`, which is DEPRECATED)
- **Engine**: `scripts/loop_engine` (deterministic Python, Clean Architecture + DI, basedpyright strict)
- **Fallback**: `PROTOCOL.md` (hand-execution parity — identical results to the engine)
- **Direct Source Write / Test / Git / Release**: `false` (STRICTLY FORBIDDEN)
- **Approval Authority**: `none`

## 1. Purpose
The loop-controller turns the linear AIWF pipeline into a **bounded, self-correcting loop**. It does not replace any phase skill or reorder any handoff; it wraps them. Each invocation reads gate verdicts and decides exactly one transition, recording an auditable trail. It exists to (a) let failing phases retry with refined inputs, (b) route named failures back to the correct upstream phase (e.g. a failed Spike → `brainstorming`), and (c) guarantee the loop always terminates.

## 2. The 5-Step Controller Contract
Each invocation performs exactly five steps (see `PROTOCOL.md` for the exact algorithm):
1. **LOAD** — read `loop_state` + Bootstrap Receipt. Missing `loop_state` → initialize `iteration = 0` (backward compatible). Missing receipt → require `initialize-workflow`.
2. **EXECUTE** — the host agent runs the skill of `current_phase` (the engine never runs a skill).
3. **EVALUATE** — obtain a verdict from `readiness-and-approval-gates` / test-gate / spike-gate and the blocking findings.
4. **DECIDE** — compute one transition ∈ `{ADVANCE, REPEAT, BACKTRACK, HALT}`.
5. **PERSIST** — atomically write the new `loop_state`, append one ledger line, and record the receipt via `workflow-command-audit`.

## 3. Transitions
| Transition | Meaning |
|---|---|
| `ADVANCE` | Gate PASS (+ approval if the phase requires it) → next phase per the existing handoff order. |
| `REPEAT` | Same phase, refine inputs from findings (or PASS-but-approval-pending). |
| `BACKTRACK` | Return to the phase a named failure points to (e.g. spike `fail → brainstorming`). |
| `HALT` | A stop-condition fired (see §4). |

## 4. Stop-Conditions (anti-infinite-loop)
1. `MAX_ITERATIONS` — `iteration + 1 ≥ max_iterations` (default `8`, configurable).
2. `GATE_PASS_FINAL` — final-phase gate PASS + valid approval.
3. `NO_PROGRESS` — identical `failure_signature` for `no_progress_threshold` consecutive cycles (default `3`) → HALT and **escalate to the user with 2–3 options**.
4. `USER_HALT` — explicit user halt.
5. `UNRECOVERABLE_ERROR` — non-recoverable runtime error.

`failure_signature` is a SHA-256 over the normalized (trim → lowercase → dedupe → sort) blocking findings, so an unchanged failure is detected deterministically.

## 5. State & Ledger Schemas
- `loop_state`: `schemas/loop-state.schema.json` (`aiwf.loop/1`) at `.agents/state/loop/<workflow-id>.json`.
- `ledger`: `schemas/loop-ledger.schema.json` (`aiwf.loop.ledger/1`), append-only JSONL at `.agents/state/loop/<workflow-id>.ledger.jsonl`, one line `{iter, phase, action, gate, verdict, evidence_refs[], next, ts}` per cycle.

## 6. Engine & Fallback (Script-First, interpreter-agnostic)
The controller never hard-codes an interpreter name. Use, in order:

1. **Canonical (agent-facing)** — `aiwf loop <load|decide|persist> ...`. Like every other AIWF skill, the installed `aiwf` wrapper resolves the interpreter (see `bootstrap.sh`).
2. **Portable launcher** (no `aiwf` CLI): `scripts/loop_engine.sh` (POSIX) or `scripts/loop_engine.ps1` (Windows). Both auto-detect `python3` → `python` → `py -3` (Python ≥ 3.9); if none is found they emit a `NoPythonInterpreter` envelope and exit `3`, directing you to step 3. Maintainer/debug direct form: `PYTHONPATH=scripts <python> -m loop_engine ...`.
3. **No interpreter at all** — follow `PROTOCOL.md` by hand. The transition table there mirrors `domain/transitions.py` exactly, so hand-execution is identical.

```bash
aiwf loop load    --workflow <id> --phase <phase>
aiwf loop decide  --workflow <id> --phase <phase> --verdict <PASS|BLOCK|FAIL|ERROR> [flags]
aiwf loop persist --input <decide-output.json | ->
```
`load` and `decide` never write; only `persist` performs side effects (atomic state write + append-only ledger).

## 7. Agent-Agnostic Adapter Matrix
All business logic lives in the engine/skill. Adapters only map "call skill / run one engine step / read-write state". They carry no business rules.

| Capability | Claude Code | Codex CLI | Antigravity |
|---|---|---|---|
| Invoke skill | Skill tool / `/loop` | prompt-routed skill call | workflow step invocation |
| Run one engine step | shell: `python -m loop_engine …` / `aiwf loop …` | shell | shell |
| Read/write state | files under `.agents/state/loop/` | files | files |
| Automation (optional) | settings hooks | wrapper script | workflow runner |

Adapter files: `adapters/claude/loop.md`, `adapters/codex/SKILL.md`, `adapters/antigravity/loop.workflow.md` (mirroring `skills/devteam/adapters/`).

### OS support matrix
| OS | Canonical | Launcher | No interpreter |
|---|---|---|---|
| Linux | `aiwf loop` (`bootstrap.sh`) | `loop_engine.sh` | PROTOCOL.md |
| macOS | `aiwf loop` (`bootstrap.sh`) | `loop_engine.sh` | PROTOCOL.md |
| Windows | `aiwf loop` (`bootstrap.ps1` / `aiwf.exe`) | `loop_engine.ps1` (PS 5.1 / pwsh) or `loop_engine.sh` under Git-Bash | PROTOCOL.md |

The engine uses only cross-platform primitives (`pathlib`, `os.replace` atomic
rename on both Windows and POSIX, UTF-8 without BOM); it is verified on Windows
and behaves identically on Linux/macOS.

## 8. Integration Points
- **Spike Gate** (`plan-to-blueprint`): a Spike Record with `verdict=fail` yields verdict `FAIL` + `backtrack_target=brainstorming` → the engine returns `BACKTRACK`.
- **`resume-workflow`**: reads `loop_state` to continue at the exact `current_phase`/`iteration`.
- **`readiness-and-approval-gates`**: supplies the PASS/BLOCK/FAIL verdict and blocking findings that drive DECIDE.
- **`workflow-command-audit`**: persists the per-cycle command receipt (the loop ledger is a separate append-only trail, not a replacement).

## 9. Backward Compatibility
- Workflows with no `loop_state` file are treated as `iteration = 0` and behave exactly like the legacy linear pipeline until a decision is persisted.
- `no_progress_threshold` is an additive config field defaulted to `3` when absent from legacy files.

## 10. Acceptance (BAT) — see `skill-self-verification`
| # | Input | Expected |
|---|---|---|
| 1 | `iteration+1 ≥ max_iterations` | `HALT` + `MAX_ITERATIONS` + escalate |
| 2 | same `failure_signature` × 3 | `HALT` + `NO_PROGRESS` + escalate |
| 3 | spike `fail` with `backtrack_target=brainstorming` | `BACKTRACK` → `brainstorming` |
| 4 | PASS + terminal + approval | `HALT` + `GATE_PASS_FINAL` |
| 5 | missing `loop_state` | initialize `iteration = 0` |
