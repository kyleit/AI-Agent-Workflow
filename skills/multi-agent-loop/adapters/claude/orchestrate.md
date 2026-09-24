---
description: Drive the AIWF multi-agent loop yourself, one step per turn (tick), until HALT
argument-hint: <workflow-id> <phases-csv>
---

<!-- SOURCE of the Claude /orchestrate adapter. Install to
     `.claude/commands/orchestrate.md`. Thin adapter: maps "run one engine
     command" only; all rules live in the engine + PROTOCOL.md. -->

Drive the AIWF multi-agent loop for workflow **$1** over phases **$2**. You are the
**worker AND the driver**: do each phase yourself in this session, then let the engine tell
you the next step. No subprocess spawn.

## Drive loop (one step per turn)
1. Do the current phase's work yourself.
2. Tick — DECIDE + PERSIST via the loop-controller, get the next action:
   ```bash
   aiwf malo tick --workflow $1 --phase <phase-just-done> --verdict PASS|BLOCK|FAIL|ERROR --phases $2
   # fallback: skills/multi-agent-loop/scripts/malo.sh tick ...
   # no interpreter: follow skills/multi-agent-loop/PROTOCOL.md by hand
   ```
3. Obey `next_action`:
   - `EXECUTE_PHASE` → do `resulting_phase` yourself (if `assigned_agent` names another agent
     you cannot run in-session, still do it here), then tick again.
   - `RUN_CODE_BLOCK_GATE` → the blueprint/implementation gate needs real full-file code blocks
     first. Materialize them and run the strict code-block gate, then tick again with
     `--gate-evidence <code-block-gate.json>`. NEVER present a code-less blueprint for approval.
   - `AUTO_APPROVE` → run `approval_command` yourself (a real, audited approval), then tick
     again with that gate phase and `--verdict PASS`.
   - `AWAIT_APPROVAL` → STOP; present the pending gate to the user; resume by ticking after
     they approve.
   - `COMPLETED` → feature done. `HALTED` / `HALT_ESCALATE` → present `escalation_options`, stop.

Start the first tick with `--phase` = the first phase after you've done its work (or the
workflow's current phase). Never auto-approve `git`/`release`/`deploy` — `tick` won't return
`AUTO_APPROVE` for them; it returns `AWAIT_APPROVAL`, so you stop and ask.

## Autonomous alternative (CI / unattended, no human)
`aiwf malo run --workflow $1 --phases $2` spawns agents headless per phase and drives to HALT.
