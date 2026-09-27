---
name: multi-agent-loop
command: malo
aliases:
  - orchestrate
  - agent-loop
category: runtime
tags:
  - orchestration
  - multi-agent
  - loop
  - headless
  - runtime
version: 1.0.0
license: MIT
created_at: 2026-09-18
updated_at: 2026-09-18
role: multi_agent_loop_orchestration
activation_mode: delegated
canonical_entrypoint: workflow-coordinator
bootstrap_receipt_required: true
accepted_bootstrap_skill: initialize-workflow
state_authority: .agents/state
registry_path: .agents/config/agent-registry.json
engine_entrypoint: scripts/malo
protocol_fallback: PROTOCOL.md
additive_only: true
direct_source_write: false
approval_authority: none
reuses:
  - loop-controller
  - devteam
description: >-
  Turn-driven, foreground (no-daemon) orchestrator that drives the loop-controller
  across heterogeneous agents (Claude, Codex, Antigravity) on one shared workspace
  until the loop HALTs. Two drive modes are supported: `tick` (the IDE agent is
  worker and driver, one CLI call per turn) and `run` (agents spawn headless per
  phase for CI). Assigns agents dynamically by capability and never auto-approves
  git, release, or deploy gates.
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
> ## ⛔ MANDATORY ENFORCEMENT GUARDS
> 1. **BOOTSTRAP FIRST**: valid Bootstrap Receipt (SHA-256) from `initialize-workflow`.
> 2. **COORDINATOR ROUTING**: invoked only via the `workflow-coordinator` chain.
> 3. **ADDITIVE-ONLY**: only ADDS an orchestration layer over `loop-controller`; renames/removes nothing (schema keys, enums, transitions, stop-conditions, Bootstrap Receipt, 95/100, SHA-256 approval, `MODE_B_MULTI_AGENT_SINGLE_WRITER`).
> 4. **NO DAEMON**: the orchestrator is a **foreground** process the user launches; it spawns short-lived agent subprocesses and exits at HALT. No persistent background service.
> 5. **HUMAN APPROVAL INVARIANT**: agents are NEVER spawned to satisfy an approval gate. At Blueprint/Implementation approval the loop HALTs and escalates to the user.
> 6. **NO SELF-APPROVAL / NO SOURCE WRITE**: `approval_authority: none`; MALO decides orchestration only.

# Skill: multi-agent-loop (MALO — Multi-Agent Loop Orchestration)

## 0. Contract & Boundaries
- **Role**: `multi_agent_loop_orchestration`; **Canonical Entrypoint**: `workflow-coordinator`.
- **Transition authority**: `loop-controller` (`aiwf.loop/1`) — MALO shells it, never re-implements transitions.
- **Coordination substrate**: `devteam` — shared workspace + `.agents/session-mail/` handoff notes.
- **Engine**: `scripts/malo` (Clean Architecture + DI, basedpyright strict, ≤500 lines/file).

## 1. Purpose
Deliver one feature with **multiple heterogeneous agents** that (1) are assigned per phase,
(2) collaborate across agent types, and (3) run continuously on **one shared workspace** until
the loop HALTs (feature complete) — pausing only at mandatory human approval gates.

## 2. The Cycle (per phase)
`LOAD → SELECT agent → EXECUTE (headless spawn) → EVALUATE (verdict) → DECIDE (loop-controller) → PERSIST`, repeat until HALT.
1. **SELECT** — dynamic by capability: `select_agent(phase, registry, history)` picks the enabled,
   capable agent (priority → least-recently-used → id). None capable → fall back to the session agent.
2. **EXECUTE** — spawn the agent CLI headless in the shared workspace with the phase task; capture
   exit + verdict (`PASS|BLOCK|FAIL|ERROR`).
3. **EVALUATE/DECIDE/PERSIST** — the loop-controller decides `{ADVANCE, REPEAT, BACKTRACK, HALT}`
   and persists loop-state; MALO appends a run-ledger row.

## 3. Assignment Registry (`aiwf.agent-registry/1`)
`.agents/config/agent-registry.json` declares each agent: `type` (claude|codex|antigravity),
`enabled`, `priority`, `capabilities` (phases), `invocation` (headless argv template with
`${task}`/`${workflow}`/`${phase}`), `verdict_source`, `cost_hint`. Missing file → single session
agent (backward compatible). Note: codex requires `--skip-git-repo-check` outside a git repo
(spike-001); default registry includes it.

## 4. Approval Gates — Policy (auto | manual)
Phases in `approval_gate_phases` (default `blueprint`, `implementation`) are governed by an
**Approval Policy** (`.agents/config/loop-approval.json`, `aiwf.loop-approval/1`; override with
`aiwf malo run --approval auto|manual`):
- **`manual`**: the orchestrator HALTs with `AWAITING_APPROVAL`; the user approves via the normal
  AIWF flow and a re-run resumes from the persisted loop-state.
- **`auto`** (default): at an allowed gate the orchestrator runs the gate's **canonical approval
  command** (e.g. `aiwf blueprint --approve --work-item <id>`) — recording a **real, audited
  approval**, never a silent bypass — then advances. If the command is missing or fails, it falls
  back to `AWAITING_APPROVAL`.
- **Hard safety rule**: `git`, `release`, `deploy` gates are **NEVER** auto-approved, even in auto
  mode. `auto_gates` (default `clarification`, `blueprint`, `implementation`) selects the rest.
- Owner clarification (`clarification_strategy`, default `first-option`) is auto-answered only for
  MALO-driven gates; the workflow-runtime `aiwf workflow submit` clarification is handled separately.

## 5. Schemas (NEW, additive)
- `aiwf.agent-registry/1` — `schemas/agent-registry.schema.json`
- `aiwf.agent-assignment/1` — `schemas/agent-assignment.schema.json`
- `aiwf.phase-run/1` — `schemas/phase-run-result.schema.json` (append-only `.agents/state/loop/<wf>.runs.jsonl`)

## 6. Engine & Fallback (Script-First, interpreter-agnostic)
1. **Canonical**: `aiwf malo select|run …` (wrapper resolves the interpreter).
2. **Launcher**: `scripts/malo.sh` (POSIX) / `scripts/malo.ps1` (Windows) — auto-detect `python3→python→py -3` (≥3.9).
3. **No interpreter**: follow `PROTOCOL.md` by hand.
```bash
aiwf malo select --workflow <id> --phase <phase>
aiwf malo run    --workflow <id> --phases plan,blueprint,implement,verify \
        [--approval auto|manual] [--approval-gates blueprint,implementation] \
        [--backtrack spike=brainstorming] [--timeout 900] [--max-cycles 24] [--dry-run]
```

## 6b. Two Drive Modes — `tick` (agent-driven, default for IDE) vs `run` (autonomous)
MALO offers **two** ways to advance the loop. Pick by *who* drives:

- **`aiwf malo tick` — agent-driven (IDE / in-session, DEFAULT).** The IDE agent
  (Claude/Codex/Antigravity) is **worker AND driver**. It does the phase work *as itself*
  (no subprocess spawn), then calls `tick` once with the phase it just finished and that phase's
  verdict. `tick` runs the loop-controller's **DECIDE + PERSIST** and returns a single
  `next_action` telling the agent what to do next. The agent acts, then ticks again — one step
  per turn — until `COMPLETED`/`HALTED`. This is what "run on the IDE/Agent, not a standalone
  script" means: no daemon, no headless spawn; the loop is one CLI call the agent makes each turn.
- **`aiwf malo run` — autonomous (CI / unattended).** MALO itself spawns the selected agent
  headless per phase and drives to HALT. Use when no human is in the loop.

### `tick` contract
```bash
aiwf malo tick --workflow <id> --phase <phase-just-done> --verdict PASS|BLOCK|FAIL|ERROR \
      --phases plan,blueprint,implement,verify \
      [--approval-gates blueprint,implementation] [--approval auto|manual] \
      [--code-gate-phases blueprint,implementation,implementation-entry] \
      [--gate-evidence docs/aiwf-runs/<id>/05-blueprint/code-block-gate.json] \
      [--finding "<failure reason>" ...] [--backtrack spike=brainstorming]
```
On `BLOCK`/`FAIL`, pass the phase's failure reason via `--finding` (repeatable). Identical
findings across cycles drive **NO_PROGRESS** detection → `HALT_ESCALATE` (the repair-loop cap):
without `--finding`, a stuck phase cannot be detected and would loop, burning tokens.
Returns JSON (`aiwf.loop-tick/1`) with `next_action`:
- **`EXECUTE_PHASE`** — do `resulting_phase` yourself (`assigned_agent` = whom the registry
  would pick; `null` = run it in this session), then `tick` again with that phase + its verdict.
- **`RUN_CODE_BLOCK_GATE`** — the resulting phase is a **code-gate phase** (blueprint/
  implementation) but no passing `CODE_BLOCK_GATE` artifact is bound. **You may NOT present
  approval.** Run the strict code-block gate so the blueprint carries real full-file code blocks,
  then `tick` again with `--gate-evidence` pointing at the produced `code-block-gate.json`. This
  is **fail-closed**: a code-less / contract-only blueprint can never reach approval.
- **`AUTO_APPROVE`** — the gate is auto-approvable AND (for code-gate phases) a passing,
  non-empty gate is bound: **run `approval_command` yourself** (a real, audited approval, e.g.
  `aiwf blueprint --approve …`), then `tick` again with the gate phase and `--verdict PASS`.
- **`AWAIT_APPROVAL`** — a human gate (manual mode, `git`/`release`/`deploy`, or no approval
  command configured): **STOP and ask the user**; resume by ticking after they approve.
- **`COMPLETED`** / **`HALTED`** / **`HALT_ESCALATE`** — the loop ended; `escalation_options`
  lists next moves on escalation.

> **Code-gate precondition (unbypassable).** For any phase in `--code-gate-phases` (default
> `blueprint,implementation,implementation-entry`), `tick` refuses to emit `AUTO_APPROVE`/
> `AWAIT_APPROVAL` unless `--gate-evidence` names a `code-block-gate.json` with `decision == PASS`
> and `code_block_count > 0`. Never present a Blueprint for approval without real code blocks.

The **drive skill loop** the IDE agent follows each turn:
`work the phase → tick → obey next_action (execute / self-approve / stop) → repeat`.
Approval safety is identical to `run`: `tick` never returns `AUTO_APPROVE` for
`git`/`release`/`deploy`, and only when the policy is `auto` for an allowed gate that has a
configured command.

## 7. Outcomes
`run`: `COMPLETED` (loop HALT `GATE_PASS_FINAL`) · `AWAITING_APPROVAL` (human gate) ·
`HALTED_ESCALATE` (`NO_PROGRESS`/`MAX_ITERATIONS` + options) · `HALTED` · `NEEDS_SESSION_AGENT`
(no capable agent) · `MAX_CYCLES`.
`tick` (per step): `EXECUTE_PHASE` · `RUN_CODE_BLOCK_GATE` · `AUTO_APPROVE` · `AWAIT_APPROVAL` ·
`COMPLETED` · `HALTED` · `HALT_ESCALATE`.

## 8. Concurrency & Safety
One active phase per cycle ⇒ one spawned writer ⇒ `single_writer` under MODE_B (MODE_C stays
`MODE_C_NOT_ELIGIBLE`). Invocation is an argv array (no shell) → injection-safe. Run ledger redacts
the task payload; absolute paths forbidden. `max_cycles` + per-run `timeout` bound spend.

## 9. Agent-Agnostic Adapters
Thin adapters map "call skill / run one step / read-write state": `adapters/{claude,codex,antigravity}`.

## 10. Backward Compatibility
No registry (or all-disabled) → `select_agent` returns None → the current session agent runs every
phase = today's single-session loop. No loop-controller contract changes.

## 11. Acceptance (BAT) — see `tests/test_malo.py`
Selection distribution/LRU/none; injection-safe invocation; verdict normalization; drive
COMPLETED across ≥2 agent types; HALT `AWAITING_APPROVAL` at a gate without spawning;
`NEEDS_SESSION_AGENT`; `HALTED_ESCALATE` on NO_PROGRESS. Plus a real subprocess+loop-engine smoke.
